"""Quick check: just Ch1 stats and samples."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.parse_pdf import parse_pdf, BOOK_NAME

PDF_PATH = r"docs/Book/Biology IX (English).pdf"
chapter = "Chapter 1 - Introduction to Biology"
chunks = parse_pdf(PDF_PATH, BOOK_NAME, chapter)
lengths = sorted(len(c.text) for c in chunks)
print(f"Total chunks  : {len(chunks)}")
print(f"Min length    : {lengths[0]} chars")
print(f"Max length    : {lengths[-1]} chars")
print(f"Median        : {lengths[len(lengths) // 2]} chars")
print(f"<100 chars    : {sum(1 for l in lengths if l < 100)}")
short = [c for c in chunks if len(c.text) < 100]
if short:
    print("SHORT CHUNKS:")
    for c in short:
        print(f"  [{c.chunk_id}] section={c.section_heading!r} text={c.text!r}")
else:
    print("No chunks < 100 chars. OK")
