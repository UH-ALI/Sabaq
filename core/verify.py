"""
core/verify.py

Independent verification layer for Sabaq.
Adheres to API_CONTRACTS.md S3:
    verify(question: GeneratedQuestion, source_chunk: Chunk) -> tuple[bool, str]

Checks whether a question's model_answer is genuinely supported by source_chunk.text.
Returns (verified: bool, verification_note: str).

verify_batch() sends all questions in a single LLM prompt for efficiency:
    verify_batch(questions, chunk_by_id) -> list[tuple[bool, str]]
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
        if "429" in exc_str or "quota" in exc_str.lower() or "rate" in exc_str.lower():
            return _do_call(config.FALLBACK_LLM_MODEL)
        elif "no longer available" in exc_str or "404" in exc_str:
            return _do_call("gemini-2.5-flash")
        else:
            raise


def verify(question: GeneratedQuestion, source_chunk: Chunk) -> tuple[bool, str]:
    """Independent LLM check: is question.model_answer actually supported by
    source_chunk.text? Returns (verified: bool, verification_note: str).
    This function must be called on every generated question before display -
    never skip it, never default to True."""

    client = _get_genai_client()

    prompt = (
        "You are a strict, objective textbook verification evaluator.\n\n"
        "Your task: Verify whether the question's model answer is genuinely, factually "
        "supported by the provided textbook excerpt.\n\n"
        f"QUESTION:\n{question.question}\n\n"
        f"PROPOSED MODEL ANSWER:\n{question.model_answer}\n\n"
        f'SOURCE TEXTBOOK EXCERPT (Chunk ID: {source_chunk.chunk_id}):\n"""\n{source_chunk.text}\n"""\n\n'
        "EVALUATION CRITERIA:\n"
        "1. Is the proposed model answer directly substantiated by the textbook excerpt text?\n"
        "2. If the excerpt does NOT contain the factual basis for this answer, or if the answer "
        "contradicts the text or introduces outside knowledge not found in this passage, verified MUST be false.\n"
        "3. If the answer is directly and accurately supported by the excerpt, verified MUST be true.\n"
        "4. Provide a concise verification_note (1-2 sentences) explaining specifically why it passed or failed.\n\n"
        "OUTPUT FORMAT:\n"
        "Return JSON:\n"
        '{\n  "verified": true or false,\n  "verification_note": "clear reason explaining why the answer is supported or unsupported by this excerpt"\n}'
    )

    raw_text = _call_with_fallback(client, config.LLM_MODEL, prompt, "application/json", 0.0)
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse verify() JSON response: {exc}\nRaw response:\n{raw_text}"
        ) from exc

    verified = bool(data.get("verified", False))
    verification_note = str(data.get("verification_note", ""))

    return verified, verification_note


def verify_batch(
    questions: list[GeneratedQuestion],
    chunk_by_id: dict[str, Chunk],
) -> list[tuple[bool, str]]:
    """Batch verification: sends ALL questions in a single LLM prompt and returns
    a list of (verified, verification_note) tuples in the same order as `questions`.

    Questions whose source_chunk_id is not in chunk_by_id are marked
    (False, "Source chunk could not be resolved.") without an LLM call.

    Reduces verification from N API calls to 1, cutting total generate_questions()
    round-trips from (1 generate + N verify) down to (1 generate + 1 verify_batch).
    """
    if not questions:
        return []

    client = _get_genai_client()

    entries: list[str] = []
    unresolvable: set[int] = set()

    for i, q in enumerate(questions):
        chunk = chunk_by_id.get(q.source_chunk_id)
        if chunk is None:
            unresolvable.add(i)
            entries.append(
                f"ITEM {i}:\n"
                "  QUESTION: (source chunk not found - skip)\n"
                "  MODEL_ANSWER: N/A\n"
                "  CHUNK_TEXT: N/A"
            )
        else:
            entries.append(
                f"ITEM {i}:\n"
                f"  QUESTION: {q.question}\n"
                f"  MODEL_ANSWER: {q.model_answer}\n"
                f"  SOURCE_CHUNK_ID: {chunk.chunk_id}\n"
                f'  CHUNK_TEXT: """\n{chunk.text}\n"""'
            )

    items_block = "\n\n".join(entries)
    n = len(questions)

    prompt = (
        "You are a strict, objective textbook verification evaluator.\n\n"
        "Your task: For each numbered ITEM below, verify whether the MODEL_ANSWER is genuinely, "
        "factually supported by the CHUNK_TEXT.\n\n"
        "EVALUATION CRITERIA (apply identically to every item):\n"
        "1. verified = true ONLY if the model answer is directly and accurately substantiated by the chunk text.\n"
        "2. verified = false if the answer contradicts the text, introduces outside knowledge, "
        "or the chunk does not contain the factual basis for the answer.\n"
        '3. For items marked "(source chunk not found - skip)", return verified = false with note "Source chunk could not be resolved."\n'
        "4. verification_note: 1-2 sentences explaining specifically why it passed or failed.\n\n"
        f"ITEMS TO VERIFY:\n{items_block}\n\n"
        "OUTPUT FORMAT:\n"
        f"Return a JSON array with exactly {n} objects, one per ITEM, in the same order:\n"
        '[\n  {"item_index": 0, "verified": true or false, "verification_note": "..."},\n  ...\n]'
    )

    raw_text = _call_with_fallback(client, config.LLM_MODEL, prompt, "application/json", 0.0)
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse verify_batch() JSON response: {exc}\nRaw response:\n{raw_text}"
        ) from exc

    if not isinstance(data, list):
        raise ValueError(
            f"verify_batch() expected JSON array, got {type(data)}: {raw_text}"
        )

    result_map: dict[int, tuple[bool, str]] = {}
    for entry in data:
        idx = int(entry.get("item_index", -1))
        result_map[idx] = (
            bool(entry.get("verified", False)),
            str(entry.get("verification_note", "")),
        )

    results: list[tuple[bool, str]] = []
    for i, q in enumerate(questions):
        if i in unresolvable:
            results.append((False, f"Source chunk {q.source_chunk_id} could not be resolved."))
        elif i in result_map:
            results.append(result_map[i])
        else:
            results.append((False, "Verification result missing from batch response."))

    return results
