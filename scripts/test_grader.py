"""
scripts/test_grader.py

Discrimination verification test for core/grader.py:
Tests three answer variants against the exact same question and source chunk:
1. Correct, complete answer -> High score (8-10), missed_point == ""
2. Wrong answer -> Low score (0-3.5), clear identification of the specific error
3. Partial/incomplete answer -> Partial credit score (4-7.5), missed_point citing specific omitted textbook detail
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import GeneratedQuestion, GradeRequest, GradeResult, Chunk
from core.grader import grade_answer

# Use a realistic Chapter 4 question about mitochondria from the textbook
# Chunk bio9_ch04_c032: Mitochondria
question = GeneratedQuestion(
    q_id="test_q_mitochondria_01",
    qtype="short",
    question="What is the structure and function of mitochondria in a eukaryotic cell?",
    options=[],
    correct_option_index=-1,
    model_answer="Mitochondria are double-membrane-bound organelles known as the powerhouse of the cell. The outer membrane is smooth while the inner membrane forms infoldings called cristae, which increase surface area. They carry out cellular respiration to produce ATP (adenosine triphosphate) energy.",
    marks=3,
    language="en",
    source_chunk_id="bio9_ch04_c032",
    verified=True,
    verification_note="Directly supported by textbook passage on mitochondria.",
    explanation_en="Mitochondria have double membranes and produce ATP via aerobic respiration.",
    explanation_ur="مائٹوکونڈریا خلیے کے پاور ہاؤس ہیں جو اے ٹی پی توانائی پیدا کرتے ہیں۔",
    explanation_ur_roman="Mitochondria cell ka powerhouse hain jo ATP energy banate hain.",
)

variants = [
    {
        "label": "Case 1: Correct & Complete Answer",
        "answer": "Mitochondria are double-membrane bounded organelles called the powerhouse of the cell. The outer membrane is smooth, while the inner membrane folds inward into cristae to increase surface area. Their primary function is cellular respiration, producing energy in the form of ATP for cell activities.",
        "expected_score_range": (8.0, 10.0),
    },
    {
        "label": "Case 2: Wrong / Erroneous Answer",
        "answer": "Mitochondria are single-membraned structures responsible for storing chlorophyll and capturing sunlight for photosynthesis to synthesize glucose in plant cells.",
        "expected_score_range": (0.0, 3.5),
    },
    {
        "label": "Case 3: Partial / Incomplete Answer",
        "answer": "Mitochondria are double-membrane organelles called the powerhouse of the cell and their main function is to produce ATP energy for the cell.",
        "expected_score_range": (4.0, 7.5),
    },
]

print("=" * 70)
print("PHASE 10: CORE/GRADER.PY DISCRIMINATION VERIFICATION")
print(f"Question: {question.question}")
print(f"Source Chunk: {question.source_chunk_id}")
print(f"Model Answer: {question.model_answer}")
print("=" * 70)

results = []
for v in variants:
    print(f"\n--- Testing: {v['label']} ---")
    print(f"Student Answer: \"{v['answer']}\"")
    req = GradeRequest(
        question=question,
        student_answer=v["answer"],
        tone="strict",
    )
    res = grade_answer(req)
    results.append((v, res))

    print(f"Score: {res.score} / 10.0")
    print(f"Feedback: {res.feedback}")
    print(f"Missed Point: \"{res.missed_point}\"")

    low, high = v["expected_score_range"]
    if low <= res.score <= high:
        print(f"-> [PASS] Score {res.score} is within expected range [{low}, {high}]")
    else:
        print(f"-> [WARNING] Score {res.score} outside expected range [{low}, {high}]")

    if "Case 1" in v["label"]:
        if not res.missed_point or len(res.missed_point) == 0:
            print("-> [PASS] Clean missed_point for complete answer.")
        else:
            print(f"-> [INFO] Case 1 missed_point: {res.missed_point}")
    elif "Case 3" in v["label"]:
        if res.missed_point and len(res.missed_point) > 10:
            print(f"-> [PASS] Specific textbook missed point cited: \"{res.missed_point}\"")
        else:
            print("-> [FAIL] Missed point is missing or too short for partial answer.")

print("\n" + "=" * 70)
print("RAW GRADE_RESULT DATA SUMMARY:")
for v, res in results:
    print(f"\n[{v['label']}]")
    print(json.dumps({
        "score": res.score,
        "feedback": res.feedback,
        "missed_point": res.missed_point,
        "source_chunk_id": res.source_chunk_id
    }, indent=2))
