"""
core/mock_core.py

Mock implementations of generate_questions() and grade_answer().
Identical signatures to core/generator.py and core/grader.py — the UI
imports from here on Day 1 and only ever changes one line (config.USE_MOCK_CORE)
to switch to the real engine.

Returns hardcoded data from fixtures/demo_fixtures.json.
"""

import json
import os
from contracts import GeneratedQuestion, GradeResult, GenerateRequest, GradeRequest

# Resolve fixtures path relative to this file so it works regardless of cwd.
_FIXTURES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "demo_fixtures.json"
)


def _load_fixtures() -> dict:
    with open(_FIXTURES_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def generate_questions(req: GenerateRequest) -> list[GeneratedQuestion]:
    """Returns 3 hardcoded GeneratedQuestion objects from fixtures/demo_fixtures.json.
    Same signature as the real generator — UI code never needs to change its import."""
    data = _load_fixtures()
    questions = []
    for q in data["questions"]:
        questions.append(
            GeneratedQuestion(
                q_id=q["q_id"],
                qtype=q["qtype"],
                question=q["question"],
                options=q["options"],
                correct_option_index=q["correct_option_index"],
                model_answer=q["model_answer"],
                marks=q["marks"],
                language=q["language"],
                source_chunk_id=q["source_chunk_id"],
                verified=q["verified"],
                verification_note=q["verification_note"],
                explanation_en=q["explanation_en"],
                explanation_ur=q["explanation_ur"],
                explanation_ur_roman=q["explanation_ur_roman"],
            )
        )
    return questions


def grade_answer(req: GradeRequest) -> GradeResult:
    """Returns one hardcoded GradeResult. Same signature as the real grader."""
    data = _load_fixtures()
    gr = data["grade_result"]
    return GradeResult(
        score=gr["score"],
        feedback=gr["feedback"],
        missed_point=gr["missed_point"],
        source_chunk_id=gr["source_chunk_id"],
    )
