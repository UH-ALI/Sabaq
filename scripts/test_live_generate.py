import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from contracts import GenerateRequest
from core.generator import generate_questions

req = GenerateRequest(
    book="Biology 9 (STBB, English Medium)",
    chapter="Chapter 4 - Cells and Tissues",
    qtype="mcq",
    count=3,
    language="en",
)

print("Calling real generate_questions()...")
try:
    qs = generate_questions(req)
    print(f"Generated {len(qs)} questions:")
    for i, q in enumerate(qs, 1):
        print(f"Q{i}: {q.question}")
        print(f"   Source chunk: {q.source_chunk_id}")
        print(f"   Verified: {q.verified} ({q.verification_note})")
        print(f"   Model answer: {q.model_answer}")
except Exception as e:
    import traceback
    traceback.print_exc()
