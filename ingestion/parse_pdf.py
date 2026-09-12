"""
ingestion/parse_pdf.py

Extracts text from the STBB Biology IX PDF's text layer (no OCR) and splits
it into semantically coherent chunks by section heading.

Target: ~300-400 tokens per chunk, ~60-token overlap.
Raises ValueError if the alphabetic-ratio sanity check fails (< 0.5).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pypdf

# Add project root to sys.path so `contracts` imports cleanly when this
# module is run directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import Chunk

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Approximate token size (characters ÷ 4 is a rough but standard estimate)
CHARS_PER_TOKEN = 4
TARGET_TOKENS = 350          # centre of the 300-400 window
OVERLAP_TOKENS = 60
TARGET_CHARS = TARGET_TOKENS * CHARS_PER_TOKEN   # 1400
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN  # 240

# Minimum alphabetic ratio — below this the page is treated as garbled/scanned
ALPHA_RATIO_THRESHOLD = 0.5

# Chapter → (pdf_even_start_idx, pdf_even_end_idx_exclusive)
# Only even PDF indices are real pages; odd indices are exact duplicates.
# These ranges were verified by direct inspection of the PDF.
CHAPTER_PAGE_RANGES = {
    "Chapter 1 - Introduction to Biology":  (6,   22),
    "Chapter 4 - Cells and Tissues":        (56,  98),
    "Chapter 6 - Enzymes":                  (114, 124),
}

BOOK_NAME = "Biology 9 (STBB, English Medium)"

# ---------------------------------------------------------------------------
# Noise lines to strip from each page before chunking.
# These are structural artifacts of the PDF layout, not content.
# ---------------------------------------------------------------------------
NOISE_LINE_PATTERNS = [
    # Page header lines like "52 53BIOLOGYCELLS AND TISSUES" or "62 63BIOLOGY"
    re.compile(r'^\d{1,3}\s+\d{0,3}\s*BIOLOGY(?:[A-Z\s]*)?$'),
    # Merged/concatenated page numbers like "115114" or "52 53"
    re.compile(r'^\d{2,6}$'),
    # "Major Concept" label
    re.compile(r'^Major Concept\s*$'),
    # "In this Unit you will learn:" header
    re.compile(r'^In this Unit you will learn:\s*$'),
    # Bullet points from chapter intro (Ø Ÿ •) and Summary bullets
    re.compile(r'^[ØŸ•]\s+.+$'),
    # Figure / table captions — full caption lines
    # Matches: "Figure 4.1 ...", "Fig 4.1 ...", "Fig: 1.1 ...", "Table 2 ..."
    re.compile(r'^(?:Figure|Fig|Table|FIGURE):?\s+\d[\d.:\s]*.{0,100}$'),
    # "444Chapter", "111Chapter" etc. title-page artifacts
    re.compile(r'^\d{3}Chapter\s*$'),
    # Diagram label lines: very short (≤20 chars), only letters+spaces, no punctuation,
    # no digits — e.g. "Stomach", "Blood", "Nervous tissue" from chapter cover art.
    # NOTE: real headings always have either ':' at the end, digits, or are longer.
    re.compile(r'^[A-Z][a-zA-Z ]{0,18}[a-zA-Z]$'),
    # Lines that are only lowercase short words (scattered diagram labels)
    re.compile(r'^[a-z][a-z\s]{0,15}$'),
    # "tissue Columnar", "muscle tissue" etc. — lowercase+space+Uppercase, short lines
    re.compile(r'^[a-z][a-z]+ [A-Z][a-zA-Z]+$'),

    # "ENZYMES 115BIOLOGY" style merged header lines
    re.compile(r'^[A-Z]+\s+\d+BIOLOGY\s*$'),
]

# ---------------------------------------------------------------------------
# Section heading detection — only match lines that look like real headings.
# A "real heading" in STBB Biology 9 is one of:
#   1. Dotted numeric: "4.1.1 Something:" or "4.2 SOMETHING"
#   2. ALLCAPS major heading on its own line (≥8+ caps chars)
#   3. Numbered topic: "1. Diffusion:" or "1. Jabir Bin Hayan (722-817 A.D):"
#   4. Lettered/roman topic: "(a) Light microscope:" or "(B) Compound (Complex) Tissues:"
#   5. Title-case noun phrase ending in colon, with optional parenthetical aside:
#      "Ribosomes:" "Golgi body:" "Mitochondria (Singular; Mitochorion):"
#      "Biomathematics/Biometry:" "Bio-economics:" etc.
# ---------------------------------------------------------------------------
HEADING_REGEX = re.compile(
    r'^('
    # Dotted numeric: 4, 4.1, 4.2.3, 6.1.2 — with any text after
    r'\d+\.\d+(?:\.\d+)?(?:\.\d+)?\s+\S.{2,}'
    r'|'
    # ALLCAPS line that is its own paragraph (at least 8 caps chars)
    r'[A-Z][A-Z ]{8,}'
    r'|'
    # Numbered topic heading ending in colon: "1. Diffusion:" or with parenthetical
    r'\d+\.\s+[A-Z][a-zA-Z0-9 /-]+(?:\s*\([^)]+\))?\s*:'
    r'|'
    # Lettered or Roman numeral sub-heading: "(a)  Light microscope:" or "(B) Compound (Complex) Tissues:"
    r'\([a-zA-Z0-9]+\)\s+[A-Z][a-zA-Z0-9 /-]+(?:\s*\([^)]+\))?\s*:'
    r'|'
    # Title-case noun phrase (1–5 words) ending in colon with optional parenthetical aside:
    # Catches: "Ribosomes:" "Golgi body:" "Mitochondria (Singular; Mitochorion):"
    # "Biomathematics/Biometry:" "Bio-economics:"
    r'[A-Z][a-zA-Z0-9/-]+(?: [a-zA-Z0-9/-]+){0,4}(?:\s*\([^)]+\))?\s*:'
    r')$',
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _alpha_ratio(text: str) -> float:
    """Fraction of characters that are ASCII alphabetic letters."""
    if not text:
        return 0.0
    alpha_count = sum(1 for c in text if c.isalpha() and ord(c) < 128)
    return alpha_count / len(text)


def _clean_page(raw: str) -> str:
    """Strip noise lines from a single page's extracted text."""
    lines = raw.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(pat.match(stripped) for pat in NOISE_LINE_PATTERNS):
            continue
        cleaned_lines.append(stripped)
    return '\n'.join(cleaned_lines)


def _extract_chapter_text(
    reader: pypdf.PdfReader,
    start_idx: int,
    end_idx: int,
) -> tuple[str, list[tuple[int, int]]]:
    """
    Extract, clean, and concatenate text from even PDF pages in [start_idx, end_idx).

    Returns:
        full_text: the concatenated cleaned text for the chapter
        page_breaks: list of (char_offset_in_full_text, human_page_number) sorted
                     by offset, used to assign page_hint to chunks.
    """
    parts: list[str] = []
    page_breaks: list[tuple[int, int]] = []
    offset = 0

    for pdf_idx in range(start_idx, end_idx, 2):  # step 2 — skip duplicate odd pages
        raw = reader.pages[pdf_idx].extract_text() or ""
        cleaned = _clean_page(raw)
        # Collapse multiple blank lines to at most two
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
        if not cleaned:
            continue
        page_breaks.append((offset, pdf_idx + 1))  # pdf_idx+1 ≈ human page ref
        parts.append(cleaned)
        offset += len(cleaned) + 1  # +1 for the joining '\n'

    full_text = '\n'.join(parts)
    return full_text, page_breaks


def _page_hint_for_offset(
    char_offset: int,
    page_breaks: list[tuple[int, int]],
) -> int:
    """Return the best human-readable page number for a character offset."""
    hint = page_breaks[0][1] if page_breaks else 1
    for pb_offset, pb_page in page_breaks:
        if pb_offset <= char_offset:
            hint = pb_page
        else:
            break
    return hint


def _find_sections(text: str) -> list[tuple[int, str]]:
    """
    Find all heading positions in text.
    Returns sorted list of (char_offset, heading_text).
    """
    found: dict[int, str] = {}
    for m in HEADING_REGEX.finditer(text):
        pos = m.start()
        heading = m.group(0).strip()
        if pos not in found:
            found[pos] = heading
    return sorted(found.items())


def _split_at_sentences(text: str, start: int, target_chars: int) -> int:
    """
    Starting from `start`, find a good split point around start + target_chars
    that falls at a sentence boundary. Returns the end index into text.
    """
    hard_end = min(start + target_chars, len(text))
    if hard_end == len(text):
        return hard_end

    # Look backward for a sentence boundary within the last 30% of the window
    lookback = target_chars // 3
    window = text[max(start, hard_end - lookback):hard_end]
    # Find last sentence-ending punctuation followed by whitespace/newline
    sentence_break = None
    for m in re.finditer(r'[.!?]\s', window):
        sentence_break = m.end()
    if sentence_break is not None:
        return max(start, hard_end - lookback) + sentence_break

    # Fall back to last whitespace
    for m in re.finditer(r'\s', window):
        sentence_break = m.start()
    if sentence_break is not None:
        return max(start, hard_end - lookback) + sentence_break

    return hard_end


def _is_heading_like_first_line(line: str) -> bool:
    """
    Check whether a chunk's first line looks like its own section heading
    (e.g. '(B) Plant tissues', '(B) Compound (Complex) Tissues:').
    Used to self-correct chunks whose body text begins with a real heading
    that was overridden or missed by the preceding text stream.
    """
    line = line.strip()
    if not line or line.endswith(('.', '?', '!', ';')):
        return False
    if any(p.match(line) for p in NOISE_LINE_PATTERNS) or "BIOLOGY" in line:
        return False
    words = line.split()
    if not (1 <= len(words) <= 6):
        return False
    # If ends in colon
    if line.endswith(':'):
        return True
    # Lettered or numbered marker: e.g. "(B) Plant tissues", "(A) Simple...", "1. ..."
    if line.startswith('(') and len(words) >= 2:
        return True
    if len(words) >= 2 and words[0][0].isdigit():
        return True
    # Title-cased phrase (1-5 words, every major word capitalized)
    minor = {'and', 'or', 'of', 'in', 'the', 'for', 'with', 'on', 'at', 'to', 'a', 'an', '&'}
    if 1 <= len(words) <= 5 and all(w[0].isupper() or w.lower() in minor for w in words):
        if all(any(c.isalpha() for c in w) for w in words):
            return True
    return False


def _make_chunks_from_section(
    heading: str,
    body: str,
    book: str,
    chapter: str,
    page_breaks: list[tuple[int, int]],
    body_global_offset: int,
    seq_counter: list[int],
    chapter_code: str,
) -> list[Chunk]:
    """
    Slice a section body into overlapping chunks of ~TARGET_CHARS.
    Each chunk is a Chunk dataclass instance.
    """
    chunks: list[Chunk] = []
    if not body.strip():
        return chunks

    pos = 0
    while pos < len(body):
        end = _split_at_sentences(body, pos, TARGET_CHARS)
        chunk_text = body[pos:end].strip()

        if len(chunk_text) > 40 and _alpha_ratio(chunk_text) > 0.35:
            seq = seq_counter[0]
            seq_counter[0] += 1
            absolute_offset = body_global_offset + pos
            page_hint = _page_hint_for_offset(absolute_offset, page_breaks)

            # Heading self-correction: if chunk body starts with a heading-like phrase
            # of its own (e.g. "(B) Plant tissues"), use that phrase as section_heading.
            first_line = chunk_text.split('\n')[0].strip()
            chunk_heading = first_line if _is_heading_like_first_line(first_line) else heading

            chunks.append(Chunk(
                chunk_id=f"{chapter_code}_c{seq:03d}",
                book=book,
                chapter=chapter,
                section_heading=chunk_heading,
                page_hint=page_hint,
                text=chunk_text,
            ))

        if end >= len(body):
            break
        # Next window: step forward by (target - overlap) to create overlap
        step = max(1, TARGET_CHARS - OVERLAP_CHARS)
        pos = _split_at_sentences(body, pos + step, 0)
        if pos >= end:
            pos = end  # guarantee forward progress

    return chunks


def _chapter_code(chapter: str) -> str:
    """Derive a short code from the chapter name, e.g. 'Chapter 4 …' → 'bio9_ch04'."""
    m = re.search(r'Chapter\s+(\d+)', chapter, re.I)
    if m:
        return f"bio9_ch{int(m.group(1)):02d}"
    slug = re.sub(r'[^a-z0-9]+', '_', chapter.lower()).strip('_')
    return f"bio9_{slug}"


# ---------------------------------------------------------------------------
# Public API — signature matches API_CONTRACTS.md §3 exactly
# ---------------------------------------------------------------------------

def parse_pdf(pdf_path: str, book_name: str, chapter_name: str) -> list[Chunk]:
    """Extracts text from the PDF's text layer (no OCR), splits by heading,
    ~300-400 tokens per chunk with ~60-token overlap. Raises ValueError if
    extracted text fails a basic sanity check (alphabetic ratio < 0.5)."""

    if chapter_name not in CHAPTER_PAGE_RANGES:
        raise ValueError(
            f"Chapter {chapter_name!r} is not in scope. "
            f"Valid chapters: {list(CHAPTER_PAGE_RANGES)}"
        )

    start_idx, end_idx = CHAPTER_PAGE_RANGES[chapter_name]
    reader = pypdf.PdfReader(pdf_path)
    full_text, page_breaks = _extract_chapter_text(reader, start_idx, end_idx)

    # --- Sanity check: alphabetic ratio ---
    ratio = _alpha_ratio(full_text)
    if ratio < ALPHA_RATIO_THRESHOLD:
        raise ValueError(
            f"Alphabetic ratio of extracted text is {ratio:.2f} "
            f"(threshold {ALPHA_RATIO_THRESHOLD}). "
            "Text extraction may have failed — confirm the PDF has a real text layer."
        )

    # --- Split into sections at heading boundaries ---
    heading_positions = _find_sections(full_text)
    code = _chapter_code(chapter_name)
    seq_counter = [0]
    all_chunks: list[Chunk] = []

    # Build (heading, body_text, global_offset_of_body_start) triples
    sections: list[tuple[str, str, int]] = []

    if not heading_positions:
        sections.append(("Introduction", full_text, 0))
    else:
        # Preamble before first heading
        first_pos = heading_positions[0][0]
        preamble = full_text[:first_pos].strip()
        if preamble:
            sections.append(("Introduction", preamble, 0))

        for i, (pos, heading) in enumerate(heading_positions):
            next_pos = heading_positions[i + 1][0] if i + 1 < len(heading_positions) else len(full_text)
            # Body starts after the heading line itself
            heading_end = pos + len(heading)
            body = full_text[heading_end:next_pos].strip()
            sections.append((heading, body, heading_end))

    for heading, body, offset in sections:
        chunks = _make_chunks_from_section(
            heading=heading,
            body=body,
            book=book_name,
            chapter=chapter_name,
            page_breaks=page_breaks,
            body_global_offset=offset,
            seq_counter=seq_counter,
            chapter_code=code,
        )
        all_chunks.extend(chunks)

    return all_chunks


# ---------------------------------------------------------------------------
# CLI entry point — used during Phase 2 manual verification
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    PDF_PATH = r"docs/Book/Biology IX (English).pdf"
    CHAPTER = "Chapter 4 - Cells and Tissues"

    print(f"Parsing: {CHAPTER}")
    chunks = parse_pdf(PDF_PATH, BOOK_NAME, CHAPTER)
    print(f"Total chunks produced: {len(chunks)}\n")

    # Print 3 full sample chunks (first, middle, last) — NOT truncated
    sample_indices = [0, len(chunks) // 2, len(chunks) - 1]
    for idx in sample_indices:
        c = chunks[idx]
        sep = '=' * 70
        print(sep)
        print(f"chunk_id     : {c.chunk_id}")
        print(f"section      : {c.section_heading}")
        print(f"page_hint    : {c.page_hint}")
        print(f"text length  : {len(c.text)} chars (~{len(c.text) // CHARS_PER_TOKEN} tokens)")
        print(f"text:\n{c.text}")
        print()
