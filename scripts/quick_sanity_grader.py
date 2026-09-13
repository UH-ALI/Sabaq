import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import GeneratedQuestion, GradeRequest
from core.grader import grade_answer

# Question from Chapter 4
q = GeneratedQuestion(
    q_id="sanity_q_01",
    qtype="short",
    question="What is the structure and function of the cell membrane?",
    options=[],
    correct_option_index=-1,
    model_answer="The cell membrane is a selectively permeable, thin outermost layer of animal cells composed of a phospholipid bilayer with embedded proteins. It controls the movement of substances into and out of the cell.",
    marks=3,
    language="en",
    source_chunk_id="bio9_ch04_c014",
    verified=True,
    verification_note="Textbook verified",
    explanation_en="Cell membrane is selectively permeable.",
    explanation_ur="سیل میمبرین نیم نفوذ پذیر جھلی ہے۔",
    explanation_ur_roman="Cell membrane selectively permeable hoti hai.",
)

# 1. Clearly correct answer
req_correct = GradeRequest(
    question=q,
    student_answer="The cell membrane is a thin outermost layer of animal cells made of a phospholipid bilayer with embedded proteins. It is selectively permeable and controls the movement of substances into and out of the cell.",
    tone="strict",
)
res_correct = grade_answer(req_correct)
print(f"[CORRECT ANSWER TEST]")
print(f"Score: {res_correct.score}/10")
print(f"Feedback: {res_correct.feedback[:120]}...")
print(f"Missed Point: {res_correct.missed_point}")

# 2. Clearly wrong answer
req_wrong = GradeRequest(
    question=q,
    student_answer="The cell membrane is a hard rigid wall made of pure limestone that protects the cell from UV radiation by reflecting all sunlight.",
    tone="strict",
)
res_wrong = grade_answer(req_wrong)
print(f"\n[WRONG ANSWER TEST]")
print(f"Score: {res_wrong.score}/10")
print(f"Feedback: {res_wrong.feedback[:120]}...")
print(f"Missed Point: {res_wrong.missed_point[:120]}...")

assert res_correct.score >= 7.5, f"Expected high score for correct answer, got {res_correct.score}"
assert res_wrong.score <= 3.5, f"Expected low score for wrong answer, got {res_wrong.score}"
print("\n>>> SANITY CHECK PASSED: Live grader discriminates cleanly between correct and wrong answers! <<<")
