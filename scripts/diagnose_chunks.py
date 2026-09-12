"""
scripts/diagnose_chunks.py

Run parse_pdf on a given chapter and report:
  - total chunk count
  - length distribution (min, max, median, bucket counts)
  - every chunk shorter than MIN_CHARS (noise-filter collateral check)
  - 3 full untruncated sample chunks (first, middle, last)

Usage (from project root):
    python scripts/diagnose_chunks.py
    python scripts/diagnose_chunks.py --chapter "Chapter 1 - Introduction to Biology"
    python scripts/diagnose_chunks.py --chapter "Chapter 6 - Enzymes"
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path regardless of CWD
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.parse_pdf import parse_pdf, BOOK_NAME, CHAPTER_PAGE_RANGES

MIN_CHARS = 100  # chunks below this are flagged as potential collateral damage

PDF_PATH = r"docs/Book/Biology IX (English).pdf"


def diagnose(chapter: str) -> None:
    print(f"Parsing: {chapter}")
    chunks = parse_pdf(PDF_PATH, BOOK_NAME, chapter)
    lengths = sorted(len(c.text) for c in chunks)

    print(f"\nTotal chunks  : {len(chunks)}")
    print(f"Min length    : {lengths[0]} chars")
    print(f"Max length    : {lengths[-1]} chars")
    print(f"Median        : {lengths[len(lengths) // 2]} chars")
    print(f"<{MIN_CHARS} chars : {sum(1 for l in lengths if l < MIN_CHARS)}")
    print(f"100–1000      : {sum(1 for l in lengths if 100 <= l < 1000)}")
    print(f"1000–2000     : {sum(1 for l in lengths if 1000 <= l < 2000)}")
    print(f">2000 chars   : {sum(1 for l in lengths if l >= 2000)}")

    short = [c for c in chunks if len(c.text) < MIN_CHARS]
    if short:
        print(f"\n--- Chunks shorter than {MIN_CHARS} chars (potential collateral) ---")
        for c in short:
            print(f"  [{c.chunk_id}] section={c.section_heading!r:35s} text={c.text!r}")
    else:
        print(f"\nNo chunks shorter than {MIN_CHARS} chars. ✓")

    print("\n--- 3 sample chunks (first / middle / last) ---")
    for idx in [0, len(chunks) // 2, len(chunks) - 1]:
        c = chunks[idx]
        print(f"\n{'=' * 70}")
        print(f"chunk_id    : {c.chunk_id}")
        print(f"section     : {c.section_heading}")
        print(f"page_hint   : {c.page_hint}")
        print(f"chars/tokens: {len(c.text)} / ~{len(c.text) // 4}")
        print(f"text:\n{c.text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose parse_pdf chunk quality.")
    parser.add_argument(
        "--chapter",
        default="Chapter 4 - Cells and Tissues",
        choices=list(CHAPTER_PAGE_RANGES.keys()),
        help="Chapter to parse (default: Chapter 4)",
    )
    args = parser.parse_args()
    diagnose(args.chapter)


if __name__ == "__main__":
    main()
