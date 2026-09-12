"""
scripts/diagnose_all_chapters.py

Run diagnose_chunks diagnostic on all three in-scope chapters.
Usage: python scripts/diagnose_all_chapters.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.parse_pdf import parse_pdf, BOOK_NAME, CHAPTER_PAGE_RANGES

MIN_CHARS = 100
PDF_PATH = r"docs/Book/Biology IX (English).pdf"


def diagnose(chapter: str) -> None:
    print(f"\n{'#' * 70}")
    print(f"# {chapter}")
    print(f"{'#' * 70}")
    chunks = parse_pdf(PDF_PATH, BOOK_NAME, chapter)
    lengths = sorted(len(c.text) for c in chunks)

    print(f"Total chunks  : {len(chunks)}")
    print(f"Min length    : {lengths[0]} chars")
    print(f"Max length    : {lengths[-1]} chars")
    print(f"Median        : {lengths[len(lengths) // 2]} chars")
    print(f"<{MIN_CHARS} chars  : {sum(1 for l in lengths if l < MIN_CHARS)}")
    print(f"100–1000      : {sum(1 for l in lengths if 100 <= l < 1000)}")
    print(f"1000–2000     : {sum(1 for l in lengths if 1000 <= l < 2000)}")

    short = [c for c in chunks if len(c.text) < MIN_CHARS]
    if short:
        print(f"\n⚠ Chunks shorter than {MIN_CHARS} chars:")
        for c in short:
            print(f"  [{c.chunk_id}] section={c.section_heading!r:35s} text={c.text!r}")
    else:
        print(f"✓ No chunks shorter than {MIN_CHARS} chars.")

    # Print 3 full sample chunks
    print("\n--- Sample chunks (first / middle / last) ---")
    for idx in [0, len(chunks) // 2, len(chunks) - 1]:
        c = chunks[idx]
        print(f"\n{'=' * 70}")
        print(f"chunk_id    : {c.chunk_id}")
        print(f"section     : {c.section_heading}")
        print(f"page_hint   : {c.page_hint}")
        print(f"chars/tokens: {len(c.text)} / ~{len(c.text) // 4}")
        print(f"text:\n{c.text}")


if __name__ == "__main__":
    for chapter in CHAPTER_PAGE_RANGES:
        diagnose(chapter)
