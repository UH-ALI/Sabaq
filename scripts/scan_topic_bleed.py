"""
scripts/scan_topic_bleed.py

Detects topic-bleed chunks: chunks whose body text contains more than one
colon-terminated heading-like line. That's the signature of a chunk that
quietly covers two separate topics.

A "heading-like line" in the body is any line matching one of these patterns:
  - Title-case noun phrase ending in colon:  "Ribosomes:"  "Golgi body:"
  - Numbered topic heading ending in colon:  "1. Diffusion:"
  - Lettered sub-heading ending in colon:    "(a) Light microscope:"
  - Dotted numeric heading:                  "4.2.3 Cellular Structures..."
  - ALLCAPS heading line

Usage: python scripts/scan_topic_bleed.py [--jsonl path/to/chunks.jsonl]
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Heading-like patterns to look for WITHIN a chunk body
INLINE_HEADING_PATTERNS = [
    # Title-case noun phrase (1-5 words), ending in colon with optional parenthetical
    re.compile(r'^[A-Z][a-zA-Z0-9/-]+(?: [a-zA-Z0-9/-]+){0,4}(?:\s*\([^)]+\))?\s*:$'),
    # Numbered topic: "1. Diffusion:" or with parenthetical
    re.compile(r'^\d+\.\s+[A-Z][a-zA-Z0-9 /-]+(?:\s*\([^)]+\))?\s*:$'),
    # Lettered or Roman numeral sub-heading: "(a) Light microscope:" or "(B) Compound (Complex) Tissues:"
    re.compile(r'^\([a-zA-Z0-9]+\)\s+[A-Z][a-zA-Z0-9 /-]+(?:\s*\([^)]+\))?\s*:$'),
    # Dotted numeric: "4.2.3 Cellular Structures..."
    re.compile(r'^\d+\.\d+(?:\.\d+)?\s+\S.{2,}$'),
    # ALLCAPS line
    re.compile(r'^[A-Z][A-Z ]{8,}$'),
]


def count_heading_lines(text: str) -> list[str]:
    """Return all lines in text that match a heading-like pattern."""
    hits = []
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped and any(p.match(stripped) for p in INLINE_HEADING_PATTERNS):
            hits.append(stripped)
    return hits


def scan(jsonl_path: str) -> None:
    path = Path(jsonl_path)
    chunks = []
    with path.open(encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    bleed_chunks = []
    for c in chunks:
        headings_found = count_heading_lines(c['text'])
        if len(headings_found) > 1:
            bleed_chunks.append((c, headings_found))

    print(f"Scanned {len(chunks)} chunks in {path}")
    print(f"Topic-bleed chunks (>1 heading-like line in body): {len(bleed_chunks)}\n")

    if bleed_chunks:
        for c, headings in bleed_chunks:
            print(f"  [{c['chunk_id']}] section={c['section_heading']!r}")
            print(f"    Heading-like lines found in body ({len(headings)}):")
            for h in headings:
                print(f"      -> {h!r}")
            print()

    # Per-chapter stats
    from collections import defaultdict
    chapter_stats: dict[str, dict] = defaultdict(lambda: {'total': 0, 'bleed': 0, 'total_chars': 0})
    for c in chunks:
        ch = c['chapter']
        chapter_stats[ch]['total'] += 1
        chapter_stats[ch]['total_chars'] += len(c['text'])
    for c, _ in bleed_chunks:
        chapter_stats[c['chapter']]['bleed'] += 1

    print("Per-chapter summary:")
    print(f"  {'Chapter':<45} {'Chunks':>6}  {'Avg chars':>9}  {'Bleed':>5}")
    print(f"  {'-'*45} {'-'*6}  {'-'*9}  {'-'*5}")
    for ch, s in chapter_stats.items():
        avg = s['total_chars'] // s['total'] if s['total'] else 0
        short_name = ch.split(' - ')[0] if ' - ' in ch else ch
        print(f"  {short_name:<45} {s['total']:>6}  {avg:>9}  {s['bleed']:>5}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jsonl', default='data/bio9/chunks.jsonl')
    args = parser.parse_args()
    scan(args.jsonl)


if __name__ == '__main__':
    main()
