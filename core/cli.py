"""
core/cli.py

CLI entry point for Phase 4 generation testing.
Usage:
    python -m core.cli --chapter bio9_ch04 --qtype mcq --n 5
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import GenerateRequest, Chunk
from core.generator import generate_questions
import config

CHAPTER_MAP = {
    "bio9_ch01": "Chapter 1 - Introduction to Biology",
    "bio9_ch04": "Chapter 4 - Cells and Tissues",
    "bio9_ch06": "Chapter 6 - Enzymes",
}


def main():
    parser = argparse.ArgumentParser(description="Sabaq Question Generator CLI")
    parser.add_argument("--chapter", default="bio9_ch04", help="Chapter code or full name")
    parser.add_argument("--qtype", default="mcq", choices=["mcq", "short"], help="Question type")
    parser.add_argument("--n", type=int, default=5, help="Number of questions to generate")
    parser.add_argument("--lang", default="en", choices=["en", "ur"], help="Language")
    args = parser.parse_args()

    chapter_name = CHAPTER_MAP.get(args.chapter, args.chapter)

    req = GenerateRequest(
        book="Biology 9 (STBB, English Medium)",
        chapter=chapter_name,
        qtype=args.qtype,
        count=args.n,
        language=args.lang,
    )

    print(f"Generating {req.count} {req.qtype.upper()} questions for: {req.chapter} ...\n")
    questions = generate_questions(req)

    # Load chunks for printing full source text verification
    chunks_path = Path(config.INDEX_DIR) / "chunks.jsonl"
    chunk_lookup: dict[str, Chunk] = {}
    with chunks_path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                c = Chunk(**json.loads(line))
                chunk_lookup[c.chunk_id] = c

    for i, q in enumerate(questions, 1):
        print("=" * 80)
        print(f"QUESTION {i} of {len(questions)}")
        print("=" * 80)
        print(f"Question Text : {q.question}")
        if q.qtype == "mcq":
            print("Options       :")
            for opt_idx, opt in enumerate(q.options):
                marker = "✓" if opt_idx == q.correct_option_index else " "
                print(f"  [{marker}] ({chr(65 + opt_idx)}) {opt}")
            print(f"Correct Answer: Option ({chr(65 + q.correct_option_index)}): {q.model_answer}")
        else:
            print(f"Model Answer  : {q.model_answer}")
        print(f"Marks         : {q.marks}")
        print(f"Source Chunk  : {q.source_chunk_id}")
        verified_badge = "✅ VERIFIED" if q.verified else "❌ UNVERIFIED"
        print(f"Verified      : {verified_badge}")
        print(f"Verify Note   : {q.verification_note}")
        print("-" * 80)
        print("SOURCE CHUNK FULL TEXT:")
        if q.source_chunk_id in chunk_lookup:
            src = chunk_lookup[q.source_chunk_id]
            print(f"Section : {src.section_heading} | Page: {src.page_hint}")
            print(src.text)
        else:
            print(f"[ERROR: Source chunk {q.source_chunk_id} not found in chunks.jsonl!]")
        print("=" * 80)
        print()


if __name__ == "__main__":
    main()
