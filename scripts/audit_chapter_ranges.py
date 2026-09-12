"""
scripts/audit_chapter_ranges.py

Prints raw unfiltered pypdf text for the boundary pages of each of the 3
in-scope chapters — title page, last content page, and first page of the
next chapter. Used to verify CHAPTER_PAGE_RANGES is correct.

Usage (from project root):
    python scripts/audit_chapter_ranges.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pypdf

PDF_PATH = r"docs/Book/Biology IX (English).pdf"
CHARS_PER_PREVIEW = 600


def show(label: str, idx: int, reader: pypdf.PdfReader) -> None:
    text = reader.pages[idx].extract_text() or "(empty)"
    print(f"\n--- {label} (PDF idx {idx}) ---")
    print(text[:CHARS_PER_PREVIEW])


def main() -> None:
    reader = pypdf.PdfReader(PDF_PATH)
    print(f"Total PDF pages: {len(reader.pages)}")

    print("\n" + "=" * 60)
    print("CHAPTER 1 — Introduction to Biology (expected: idx 6–22)")
    show("Ch1 title/start",          6, reader)
    show("Ch1 last content page",   20, reader)
    show("Ch1→Ch2 boundary (Ch2)", 22, reader)

    print("\n" + "=" * 60)
    print("CHAPTER 4 — Cells and Tissues (expected: idx 56–98)")
    show("Ch4 title page",           56, reader)
    show("Ch4 first content",        58, reader)
    show("Ch4 last content page",    96, reader)
    show("Ch4→Ch5 boundary (Ch5)",   98, reader)

    print("\n" + "=" * 60)
    print("CHAPTER 6 — Enzymes (expected: idx 114–124)")
    show("Ch5→Ch6 transition",      112, reader)
    show("Ch6 first content",       114, reader)
    show("Ch6 last content page",   122, reader)
    show("Ch6→Ch7 boundary (Ch7)", 124, reader)


if __name__ == "__main__":
    main()
