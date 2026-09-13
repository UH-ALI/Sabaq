"""
Inspect raw PDF pages around the tissue section (pages 85-91)
to understand the actual order of headings vs content — specifically
to diagnose the section_heading mis-attribution on bio9_ch04_c049.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pypdf
from ingestion.parse_pdf import _clean_page, HEADING_REGEX

reader = pypdf.PdfReader("docs/Book/Biology IX (English).pdf")

# Pages 85-91 correspond to PDF indices 84-90 (even only: 84, 86, 88, 90)
print("=== RAW HEADING DETECTIONS (pages 85-91) ===\n")
for pdf_idx in range(84, 92, 2):
    raw = reader.pages[pdf_idx].extract_text() or ""
    cleaned = _clean_page(raw)
    human_page = pdf_idx + 1
    print(f"=== PDF idx {pdf_idx} (human page ~{human_page}) ===")
    for i, line in enumerate(cleaned.splitlines()):
        stripped = line.strip()
        if stripped:
            m = HEADING_REGEX.match(stripped)
            tag = "<<HEADING>>" if m else "        "
            print(f"  {tag} | {stripped[:80]}")
    print()

# Now also show where in the chapter full_text the heading "2. Connective tissue:"
# appears relative to "3. Muscle tissues:"
print("\n=== CHECKING HEADING ORDER IN FULL CHAPTER TEXT ===\n")
from ingestion.parse_pdf import _extract_chapter_text, CHAPTER_PAGE_RANGES, _find_sections

reader2 = pypdf.PdfReader("docs/Book/Biology IX (English).pdf")
ch4_start, ch4_end = CHAPTER_PAGE_RANGES["Chapter 4 - Cells and Tissues"]
full_text, page_breaks = _extract_chapter_text(reader2, ch4_start, ch4_end)

sections = _find_sections(full_text)
print(f"{'Pos':>7}  {'Heading'}")
print(f"{'---':>7}  {'-------'}")
for pos, heading in sections:
    if any(kw in heading for kw in ['tissue', 'Tissue', 'Muscle', 'Connective', 'Epithelial', 'Nervous', 'Plant', 'Permanent', 'Simple', 'Compound', 'Meristematic', 'Animal']):
        print(f"  {pos:>7}: {heading!r}")
