"""
scripts/compare_fix.py

Run parse_pdf for all 3 chapters with the updated HEADING_REGEX and report:
  1. Chunk count per chapter (vs. baseline: Ch1=29, Ch4=53, Ch6=17, total=99)
  2. Average chunk length per chapter
  3. Min/max chunk length per chapter
  4. Topic-bleed count (chunks with >1 heading-like line in body)
  5. All remaining bleed chunks with detail

Baseline (before fix):
  Chapter 1:  29 chunks, avg 681 chars, 6 bleed
  Chapter 4:  53 chunks, avg 901 chars, 6 bleed
  Chapter 6:  17 chunks, avg 740 chars, 0 bleed
  Total:      99 chunks, 12 bleed

Run: python scripts/compare_fix.py
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.parse_pdf import parse_pdf, BOOK_NAME, CHAPTER_PAGE_RANGES

PDF_PATH = r"docs/Book/Biology IX (English).pdf"

# Same detection patterns as scan_topic_bleed.py
INLINE_HEADING_PATTERNS = [
    re.compile(r'^[A-Z][a-zA-Z0-9/-]+(?: [a-zA-Z0-9/-]+){0,4}(?:\s*\([^)]+\))?\s*:$'),
    re.compile(r'^\d+\.\s+[A-Z][a-zA-Z0-9 /-]+(?:\s*\([^)]+\))?\s*:$'),
    re.compile(r'^\([a-zA-Z0-9]+\)\s+[A-Z][a-zA-Z0-9 /-]+(?:\s*\([^)]+\))?\s*:$'),
    re.compile(r'^\d+\.\d+(?:\.\d+)?\s+\S.{2,}$'),
    re.compile(r'^[A-Z][A-Z ]{8,}$'),
]


def heading_lines_in(text: str) -> list[str]:
    return [
        line.strip() for line in text.split('\n')
        if line.strip() and any(p.match(line.strip()) for p in INLINE_HEADING_PATTERNS)
    ]


BASELINE = {
    "Chapter 1 - Introduction to Biology": {"chunks": 29, "avg": 681, "bleed": 6},
    "Chapter 4 - Cells and Tissues":       {"chunks": 53, "avg": 901, "bleed": 6},
    "Chapter 6 - Enzymes":                 {"chunks": 17, "avg": 740, "bleed": 0},
}

print("Running parse_pdf with updated HEADING_REGEX across all 3 chapters...\n")
print(f"{'Chapter':<45} {'Chunks':>6}  {'Δ':>4}  {'Avg':>6}  {'Δavg':>6}  {'Min':>5}  {'Max':>5}  {'Bleed':>5}")
print(f"{'-'*45} {'-'*6}  {'-'*4}  {'-'*6}  {'-'*6}  {'-'*5}  {'-'*5}  {'-'*5}")

all_bleed = []
total_after = 0
total_bleed_after = 0

for chapter in CHAPTER_PAGE_RANGES:
    chunks = parse_pdf(PDF_PATH, BOOK_NAME, chapter)
    lengths = [len(c.text) for c in chunks]
    avg = sum(lengths) // len(lengths) if lengths else 0
    bleed = [(c, heading_lines_in(c.text)) for c in chunks if len(heading_lines_in(c.text)) > 1]

    b = BASELINE[chapter]
    delta_n = len(chunks) - b["chunks"]
    delta_avg = avg - b["avg"]
    short_name = chapter.split(" - ")[0]

    print(f"{short_name:<45} {len(chunks):>6}  {delta_n:>+4}  {avg:>6}  {delta_avg:>+6}  {min(lengths):>5}  {max(lengths):>5}  {len(bleed):>5}")
    all_bleed.extend(bleed)
    total_after += len(chunks)
    total_bleed_after += len(bleed)

print(f"\nTotal chunks: {total_after}  (baseline: 99, delta: {total_after - 99:+d})")
print(f"Total bleed:  {total_bleed_after}  (baseline: 12)")

if all_bleed:
    print(f"\n⚠ Remaining bleed chunks ({len(all_bleed)}):")
    for c, headings in all_bleed:
        print(f"  [{c.chunk_id}] section={c.section_heading!r}")
        for h in headings:
            print(f"    -> {h!r}")
else:
    print("\n✓ Zero topic-bleed chunks remaining.")
