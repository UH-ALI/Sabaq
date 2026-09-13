"""
core/grader.py

Live rubric-based grading engine for Sabaq.
Adheres to API_CONTRACTS.md §3:
    grade_answer(req: GradeRequest) -> GradeResult

Grades req.student_answer against req.question.model_answer and the
original textbook source chunk. Returns a score (0-10), comprehensive feedback text,
and the specific missed_point if the answer was incomplete or wrong.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import Chunk, GeneratedQuestion, GradeRequest, GradeResult
import config

load_dotenv()

_CHUNK_CACHE: dict[str, Chunk] = {}


def _load_chunks() -> dict[str, Chunk]:
    global _CHUNK_CACHE
    if not _CHUNK_CACHE:
        chunks_path = Path(config.INDEX_DIR) / "chunks.jsonl"
        if chunks_path.exists():
            with open(chunks_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        _CHUNK_CACHE[data["chunk_id"]] = Chunk(**data)
    return _CHUNK_CACHE


def _get_genai_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "No Gemini API key found. Please set GEMINI_API_KEY in your .env file."
        )
    return genai.Client(api_key=api_key)


def _call_with_fallback(
    client: genai.Client,
    model_name: str,
    prompt: str,
    mime_type: str,
    temperature: float,
) -> str:
    """Call the primary model; on 429 quota/rate error retry once with FALLBACK_LLM_MODEL.
    On model-unavailable (404) retry once with gemini-2.5-flash."""

    def _do_call(model: str) -> str:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type=mime_type,
                temperature=temperature,
            ),
        )
        return response.text

    try:
        return _do_call(model_name)
    except Exception as exc:
        exc_str = str(exc)
        if (
            "429" in exc_str
            or "quota" in exc_str.lower()
            or "rate" in exc_str.lower()
            or "503" in exc_str
            or "unavailable" in exc_str.lower()
            or "high demand" in exc_str.lower()
            or "500" in exc_str
        ):
            return _do_call(config.FALLBACK_LLM_MODEL)
        elif "no longer available" in exc_str or "404" in exc_str:
            return _do_call("gemini-2.5-flash")
        else:
            raise


def _build_grading_prompt(req: GradeRequest, chunk: Chunk | None) -> str:
    q = req.question
    tone_str = req.tone.lower()

    if tone_str == "strict":
        tone_instruction = (
            "TONE: Strict Sindh Board Examiner.\n"
            "- Evaluate strictly against the official textbook standard.\n"
            "- Mark down firmly for missing technical terminology or vague statements.\n"
            "- Be direct, rigorous, and professional in pointing out deficiencies."
        )
    else:
        tone_instruction = (
            "TONE: Encouraging Academic Mentor.\n"
            "- Use a warm, supportive, and motivating tone.\n"
            "- Acknowledge what the student got right before pointing out omissions.\n"
            "- Provide constructive guidance on how to reach full board standard."
        )

    options_formatted = ""
    if q.qtype == "mcq" and q.options:
        opts = []
        for i, opt in enumerate(q.options):
            letter = chr(65 + i)
            correct_marker = " [CORRECT OPTION]" if i == q.correct_option_index else ""
            opts.append(f"  {letter}: {opt}{correct_marker}")
        options_formatted = "\nMCQ OPTIONS:\n" + "\n".join(opts)

    chunk_info = (
        f"CHUNK ID: {chunk.chunk_id}\n"
        f"SECTION: {chunk.section_heading} (Page {chunk.page_hint})\n"
        f'TEXTBOOK TEXT:\n"""\n{chunk.text}\n"""'
        if chunk
        else "TEXTBOOK TEXT: (Source chunk not directly found; evaluate against model answer)"
    )

    prompt = f"""You are an expert exam grader for Sindh Textbook Board Matric examinations (Class 9 Biology).

Your task: Grade the student's submitted answer strictly against the provided textbook passage and official model answer.

{tone_instruction}

QUESTION DETAILS:
Question Type: {q.qtype.upper()}
Question: {q.question}
Allocated Marks: {q.marks}{options_formatted}
Official Model Answer: {q.model_answer}

GROUNDING TEXTBOOK EXCERPT:
{chunk_info}

STUDENT'S SUBMITTED ANSWER:
\"\"\"{req.student_answer}\"\"\"

GRADING CRITERIA & SCORING SCALE (0.0 to 10.0):
You must assign an accurate score on a 0.0 - 10.0 scale reflecting the student's conceptual mastery and completeness:

1. High / Full Credit (Score 8.0 - 10.0):
   - The student's answer is accurate, correct, and substantially complete.
   - For MCQs: correctly identifies the correct option or key fact.
   - For Short Answers: accurately covers the core textbook concepts required by the question and model answer.
   - 'missed_point' MUST be an empty string "" if the answer is complete. Do not nitpick trivial details if the core model answer points are satisfied.
   - 'feedback' should affirm their mastery and mention the textbook concepts they stated well.

2. Partial Credit (Score 4.0 - 7.5):
   - The student demonstrates valid understanding of key concepts (e.g., gets the primary function or structure right), BUT missed key scientific details, specific mechanisms, or terminology explicitly stated in the textbook chunk.
   - 'score' MUST reflect partial credit (4.0 - 7.5).
   - 'missed_point' MUST cite the SPECIFIC, concrete detail or textbook terminology omitted from their answer (e.g. "Specifically, you omitted that... according to the textbook").
   - CRITICAL: Never write generic advice like "be more thorough", "give more detail", or "study more". Cite the EXACT fact from the excerpt that was missing.
   - 'feedback' should state what was correct, then clearly explain what needs to be added according to the textbook.

3. Low / No Credit (Score 0.0 - 3.5):
   - The student's answer is incorrect, chooses a wrong option, states biologically false claims, confuses terms, or contradicts the textbook.
   - 'score' MUST be low (0.0 - 3.5).
   - 'feedback' must clearly identify the specific error or misconception.
   - 'missed_point' must state the correct textbook fact that contradicts or corrects the student's erroneous claim.

OUTPUT FORMAT:
Return a valid JSON object with these exact keys:
{{
  "score": float between 0.0 and 10.0,
  "feedback": "detailed examiner feedback matching the selected tone",
  "missed_point": "specific omitted or correcting textbook fact, or empty string if answer is complete and score >= 8.0"
}}
"""
    return prompt


def grade_answer(req: GradeRequest) -> GradeResult:
    """Grades req.student_answer against req.question.model_answer and the
    original source chunk. Returns score 0-10, feedback text, and the specific
    missed_point if the answer was incomplete or wrong.

    Adheres strictly to API_CONTRACTS.md §3.
    """
    # Check for empty or whitespace-only answer
    if not req.student_answer or not req.student_answer.strip():
        return GradeResult(
            score=0.0,
            feedback="No answer was provided. Please write your response to receive evaluation.",
            missed_point="No response submitted to compare against textbook requirements.",
            source_chunk_id=req.question.source_chunk_id,
        )

    chunks = _load_chunks()
    chunk = chunks.get(req.question.source_chunk_id)

    client = _get_genai_client()
    prompt = _build_grading_prompt(req, chunk)

    raw_text = _call_with_fallback(
        client=client,
        model_name=config.LLM_MODEL,
        prompt=prompt,
        mime_type="application/json",
        temperature=0.1,  # Low temperature for objective, consistent grading
    )

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse grade_answer() JSON response: {exc}\nRaw response:\n{raw_text}"
        ) from exc

    raw_score = float(data.get("score", 0.0))
    # Clamp score to [0.0, 10.0]
    score = max(0.0, min(10.0, round(raw_score, 1)))

    feedback = str(data.get("feedback", "")).strip()
    missed_point = str(data.get("missed_point", "")).strip()

    # Integrity check: if score >= 8.0, missed_point should be clean
    if score >= 8.0 and not missed_point:
        missed_point = ""

    return GradeResult(
        score=score,
        feedback=feedback,
        missed_point=missed_point,
        source_chunk_id=req.question.source_chunk_id,
    )
