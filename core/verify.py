"""
core/verify.py

Independent verification layer for Sabaq.
Adheres to API_CONTRACTS.md §3:
    verify(question: GeneratedQuestion, source_chunk: Chunk) -> tuple[bool, str]

Checks whether a question's model_answer is genuinely supported by source_chunk.text.
Returns (verified: bool, verification_note: str).
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

from contracts import Chunk, GeneratedQuestion
import config

load_dotenv()


def _get_genai_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "No Gemini API key found. Please set GEMINI_API_KEY in your .env file."
        )
    return genai.Client(api_key=api_key)


def verify(question: GeneratedQuestion, source_chunk: Chunk) -> tuple[bool, str]:
    """Independent LLM check: is question.model_answer actually supported by
    source_chunk.text? Returns (verified: bool, verification_note: str).
    This function must be called on every generated question before display —
    never skip it, never default to True."""

    client = _get_genai_client()

    prompt = f"""You are a strict, objective textbook verification evaluator.

Your task: Verify whether the question's model answer is genuinely, factually supported by the provided textbook excerpt.

QUESTION:
{question.question}

PROPOSED MODEL ANSWER:
{question.model_answer}

SOURCE TEXTBOOK EXCERPT (Chunk ID: {source_chunk.chunk_id}):
\"\"\"
{source_chunk.text}
\"\"\"

EVALUATION CRITERIA:
1. Is the proposed model answer directly substantiated by the textbook excerpt text?
2. If the excerpt does NOT contain the factual basis for this answer, or if the answer contradicts the text or introduces outside knowledge not found in this passage, verified MUST be false.
3. If the answer is directly and accurately supported by the excerpt, verified MUST be true.
4. Provide a concise verification_note (1-2 sentences) explaining specifically why it passed or failed.

OUTPUT FORMAT:
Return JSON:
{{
  "verified": true or false,
  "verification_note": "clear reason explaining why the answer is supported or unsupported by this excerpt"
}}
"""

    model_name = config.LLM_MODEL
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,  # Zero temperature for deterministic verification
            ),
        )
    except Exception as exc:
        if "no longer available" in str(exc) or "404" in str(exc):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
        else:
            raise

    raw_text = response.text
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse verify() JSON response: {exc}\nRaw response:\n{raw_text}"
        ) from exc

    verified = bool(data.get("verified", False))
    verification_note = str(data.get("verification_note", ""))

    return verified, verification_note
