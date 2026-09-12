"""
scripts/test_verify.py

Tests core.verify.verify() against:
1. A genuinely correct question & answer supported by source_chunk.text -> Expect True
2. A question with an incorrect/contradictory model_answer -> Expect False
3. A question asking about content completely absent from the chunk -> Expect False
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import Chunk, GeneratedQuestion
from core.verify import verify
import config


def load_chunk(chunk_id: str) -> Chunk:
    chunks_path = Path(config.INDEX_DIR) / "chunks.jsonl"
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = Chunk(**json.loads(line))
                if c.chunk_id == chunk_id:
                    return c
    raise ValueError(f"Chunk {chunk_id} not found in chunks.jsonl")


def main():
    print("=" * 80)
    print("PHASE 5 VERIFICATION TEST SUITE")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # TEST 1: Genuinely Correct Grounded Case -> Expected: True
    # -------------------------------------------------------------------------
    chunk_46 = load_chunk("bio9_ch04_c046")
    q_valid = GeneratedQuestion(
        q_id="test_001",
        qtype="mcq",
        question="How many basic types of tissue are found in humans and other large multicellular animals?",
        options=["Two", "Three", "Four", "Five"],
        correct_option_index=2,
        model_answer="Four",
        marks=1,
        language="en",
        source_chunk_id=chunk_46.chunk_id,
        verified=False,
        verification_note="",
        explanation_en="Humans and other large multicellular animals are made up of four basic types of tissue.",
        explanation_ur="",
        explanation_ur_roman="",
    )

    print("\n--- TEST 1: Genuinely Correct Case ---")
    print(f"Chunk ID    : {chunk_46.chunk_id}")
    print(f"Chunk Text  : {chunk_46.text.strip()}")
    print(f"Question    : {q_valid.question}")
    print(f"Model Answer: {q_valid.model_answer}")
    
    verified_1, note_1 = verify(q_valid, chunk_46)
    print(f"-> VERIFIED : {verified_1}")
    print(f"-> NOTE     : {note_1}")
    assert verified_1 is True, "Test 1 failed: Expected verified=True"
    print("✓ TEST 1 PASSED (Returned True)")

    # -------------------------------------------------------------------------
    # TEST 2: Wrong/Contradictory Answer Case -> Expected: False
    # -------------------------------------------------------------------------
    chunk_13 = load_chunk("bio9_ch04_c013")
    # Chunk 13 states: "Plant cells are generally a cubical shape while animal cells are usually spherical."
    # We deliberately give a FALSE answer claiming plant cells are spherical:
    q_contradictory = GeneratedQuestion(
        q_id="test_002",
        qtype="mcq",
        question="What is the general shape of plant cells?",
        options=["Spherical", "Cubical", "Irregular", "Spindle"],
        correct_option_index=0,
        model_answer="Spherical",  # Deliberately wrong! Text says cubical.
        marks=1,
        language="en",
        source_chunk_id=chunk_13.chunk_id,
        verified=False,
        verification_note="",
        explanation_en="Incorrect claim.",
        explanation_ur="",
        explanation_ur_roman="",
    )

    print("\n--- TEST 2: Deliberately Wrong Answer Case ---")
    print(f"Chunk ID    : {chunk_13.chunk_id}")
    print(f"Chunk Text  : {chunk_13.text.strip()[:200]}...")
    print(f"Question    : {q_contradictory.question}")
    print(f"Model Answer: {q_contradictory.model_answer} (DELIBERATELY WRONG: chunk says cubical)")
    
    verified_2, note_2 = verify(q_contradictory, chunk_13)
    print(f"-> VERIFIED : {verified_2}")
    print(f"-> NOTE     : {note_2}")
    assert verified_2 is False, "Test 2 failed: Expected verified=False"
    print("✓ TEST 2 PASSED (Returned False)")

    # -------------------------------------------------------------------------
    # TEST 3: Outside Topic / Hallucination Case -> Expected: False
    # -------------------------------------------------------------------------
    # Using chunk_46 (which only talks about tissue types) to verify a question about Krebs cycle
    q_hallucinated = GeneratedQuestion(
        q_id="test_003",
        qtype="short",
        question="What is the role of the Krebs cycle during cellular respiration?",
        options=[],
        correct_option_index=-1,
        model_answer="The Krebs cycle produces ATP and electron carriers inside the mitochondrial matrix.",
        marks=3,
        language="en",
        source_chunk_id=chunk_46.chunk_id,
        verified=False,
        verification_note="",
        explanation_en="",
        explanation_ur="",
        explanation_ur_roman="",
    )

    print("\n--- TEST 3: Outside Topic / Hallucinated Case ---")
    print(f"Chunk ID    : {chunk_46.chunk_id} (Only discusses basic animal tissue types)")
    print(f"Question    : {q_hallucinated.question}")
    print(f"Model Answer: {q_hallucinated.model_answer}")
    
    verified_3, note_3 = verify(q_hallucinated, chunk_46)
    print(f"-> VERIFIED : {verified_3}")
    print(f"-> NOTE     : {note_3}")
    assert verified_3 is False, "Test 3 failed: Expected verified=False"
    print("✓ TEST 3 PASSED (Returned False)")

    print("\n" + "=" * 80)
    print("ALL VERIFICATION SUITE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
