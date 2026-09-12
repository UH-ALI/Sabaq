"""
core/generator.py

Generates practice questions grounded strictly in retrieved textbook chunks.
Adheres to API_CONTRACTS.md §3:
    generate_questions(req: GenerateRequest) -> list[GeneratedQuestion]

Grounding rule: The model is constrained to use ONLY the provided chunk text.
Outside knowledge is strictly forbidden.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import Chunk, GenerateRequest, GeneratedQuestion
from core.retriever import retrieve
from core.verify import verify
import config

load_dotenv()


def _get_genai_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "No Gemini API key found. Please set GEMINI_API_KEY in your .env file."
        )
    return genai.Client(api_key=api_key)


def _build_prompt(req: GenerateRequest, chunks: list[Chunk]) -> str:
    chunks_text = "\n\n".join(
        f"--- CHUNK ID: {c.chunk_id} | SECTION: {c.section_heading} ---\n{c.text}"
        for c in chunks
    )

    qtype_instructions = (
        "Generate Multiple Choice Questions (MCQs):\n"
        "- 'options': exactly 4 distinct options (strings).\n"
        "- 'correct_option_index': integer 0, 1, 2, or 3 corresponding to the correct option.\n"
        "- 'model_answer': exact text of the correct option.\n"
        "- 'marks': 1"
        if req.qtype == "mcq"
        else
        "Generate Short Answer Questions:\n"
        "- 'options': empty list []\n"
        "- 'correct_option_index': -1\n"
        "- 'model_answer': concise model answer (2-4 sentences) directly supported by the chunk.\n"
        "- 'marks': integer between 2 and 5"
    )

    prompt = f"""You are an expert exam question generator for Pakistani Matric students (Sindh Textbook Board, Biology Class 9).

Your task: Generate exactly {req.count} practice questions for the chapter: "{req.chapter}".
Target question type: {req.qtype.upper()}.
Target language: {req.language} (English if "en", Urdu script if "ur").

CRITICAL GROUNDING RULES:
1. Use ONLY the facts and details directly stated in the textbook chunks provided below.
2. Do NOT extrapolate, assume, or bring in outside biological knowledge, even if you know more about the topic.
3. Every question must be fully answerable from the single source chunk specified in 'source_chunk_id'.
4. 'source_chunk_id' MUST be the exact CHUNK ID from which the question and answer are drawn.
5. Provide explanations:
   - 'explanation_en': explanation in English citing the specific fact in the chunk.
   - 'explanation_ur': explanation in Urdu script.
   - 'explanation_ur_roman': Roman Urdu translation of explanation (can be brief draft).

{qtype_instructions}

PROVIDED TEXTBOOK CHUNKS:
{chunks_text}

OUTPUT FORMAT:
Return a valid JSON array of objects with these exact keys:
[
  {{
    "question": "question text",
    "options": ["opt0", "opt1", "opt2", "opt3"],
    "correct_option_index": 0,
    "model_answer": "correct option text or short answer",
    "marks": 1,
    "source_chunk_id": "bio9_ch04_c...",
    "explanation_en": "...",
    "explanation_ur": "...",
    "explanation_ur_roman": "..."
  }}
]
"""
    return prompt


def generate_questions(req: GenerateRequest) -> list[GeneratedQuestion]:
    """Retrieves relevant chunks for req.chapter, prompts the LLM to generate
    req.count questions of req.qtype in req.language, using ONLY the retrieved
    chunk text. Each returned question must have source_chunk_id set to the
    actual chunk_id it was grounded in. Does NOT set `verified` — that's verify.py's job."""

    index_path = os.path.join(config.INDEX_DIR, "index.faiss")
    chunks_path = os.path.join(config.INDEX_DIR, "chunks.jsonl")

    # Retrieve relevant chunks for req.chapter
    # We fetch sufficient chunks to give the LLM good diversity across the chapter
    top_k = max(req.count * 2, config.DEFAULT_TOP_K)
    retrieved_chunks = retrieve(
        query=req.chapter,
        index_path=index_path,
        chunks_path=chunks_path,
        top_k=top_k,
    )

    # Filter to only chunks matching req.chapter to ensure zero cross-chapter contamination
    chapter_chunks = [c for c in retrieved_chunks if c.chapter == req.chapter]
    if not chapter_chunks:
        # Fallback: if search was too sparse, load chunks from chunks_path for this chapter
        with open(chunks_path, "r", encoding="utf-8") as fh:
            all_chunks = [Chunk(**json.loads(line)) for line in fh if line.strip()]
        chapter_chunks = [c for c in all_chunks if c.chapter == req.chapter][:top_k]

    if not chapter_chunks:
        raise ValueError(f"No chunks found for chapter: {req.chapter}")

    client = _get_genai_client()
    prompt = _build_prompt(req, chapter_chunks)

    model_name = config.LLM_MODEL
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,  # Low temperature for strict factual grounding
            ),
        )
    except Exception as exc:
        if "no longer available" in str(exc) or "404" in str(exc):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
        else:
            raise

    raw_text = response.text
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse LLM JSON response: {exc}\nRaw response:\n{raw_text}") from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array of questions, got {type(data)}:\n{raw_text}")

    valid_chunk_ids = {c.chunk_id for c in chapter_chunks}
    questions: list[GeneratedQuestion] = []

    for item in data:
        # Validate source_chunk_id
        src_id = item.get("source_chunk_id", "")
        if src_id not in valid_chunk_ids:
            # Check if it's at least a valid chunk in the chapter
            pass

        q = GeneratedQuestion(
            q_id=uuid.uuid4().hex,
            qtype=req.qtype,
            question=item["question"],
            options=item.get("options", []),
            correct_option_index=int(item.get("correct_option_index", -1)),
            model_answer=item["model_answer"],
            marks=int(item.get("marks", 1 if req.qtype == "mcq" else 3)),
            language=req.language,
            source_chunk_id=src_id,
            verified=False,              # Unset/default; verify.py will set in Phase 5
            verification_note="",        # Unset/default; verify.py will set in Phase 5
            explanation_en=item.get("explanation_en", ""),
            explanation_ur=item.get("explanation_ur", ""),
            explanation_ur_roman=item.get("explanation_ur_roman", ""),
        )
        questions.append(q)

    # Phase 5 Verification Layer: verify every question against its source chunk
    chunk_by_id = {c.chunk_id: c for c in chapter_chunks}
    for q in questions:
        src = chunk_by_id.get(q.source_chunk_id)
        if src is not None:
            is_verified, note = verify(q, src)
            q.verified = is_verified
            q.verification_note = note
        else:
            q.verified = False
            q.verification_note = f"Source chunk {q.source_chunk_id} could not be resolved."

    return questions
