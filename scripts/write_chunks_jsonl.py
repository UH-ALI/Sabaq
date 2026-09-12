"""
scripts/write_chunks_jsonl.py

Runs parse_pdf on all 3 in-scope chapters and writes every Chunk to
data/bio9/chunks.jsonl in the exact format from API_CONTRACTS.md §2:

    {"chunk_id": "...", "book": "...", "chapter": "...",
     "section_heading": "...", "page_hint": N, "text": "..."}

One JSON object per line. Field names match the Chunk dataclass exactly.
Run from project root:
    python scripts/write_chunks_jsonl.py
"""

import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.parse_pdf import parse_pdf, BOOK_NAME, CHAPTER_PAGE_RANGES

PDF_PATH = r"docs/Book/Biology IX (English).pdf"
OUTPUT_PATH = Path("data/bio9/chunks.jsonl")


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    total = 0

    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        for chapter in CHAPTER_PAGE_RANGES:
            print(f"Parsing: {chapter} ...", end=" ", flush=True)
            chunks = parse_pdf(PDF_PATH, BOOK_NAME, chapter)
            print(f"{len(chunks)} chunks")
            for chunk in chunks:
                line = json.dumps(dataclasses.asdict(chunk), ensure_ascii=False)
                fh.write(line + "\n")
            total += len(chunks)

    print(f"\nWrote {total} chunks to {OUTPUT_PATH}")

    # Spot-check: read back and verify field names
    print("\nSpot-check first 3 lines:")
    with OUTPUT_PATH.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i >= 3:
                break
            obj = json.loads(line)
            required_fields = {"chunk_id", "book", "chapter", "section_heading", "page_hint", "text"}
            missing = required_fields - set(obj.keys())
            if missing:
                print(f"  ✗ Line {i+1} MISSING FIELDS: {missing}")
            else:
                print(f"  ✓ Line {i+1}: chunk_id={obj['chunk_id']!r} section={obj['section_heading']!r} page={obj['page_hint']}")


if __name__ == "__main__":
    main()
