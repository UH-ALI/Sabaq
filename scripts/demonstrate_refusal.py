"""
scripts/demonstrate_refusal.py

Standalone proof-of-concept for Phase 6 graceful refusal logic.
Does NOT modify contracts.py or core/generator.py.

Given a user query and target chapter:
1. Searches the index using multilingual-e5-base.
2. Filters to chunks from the target chapter.
3. Compares the top cosine similarity score against a threshold (0.8500).
4. Decides whether to generate normally or refuse gracefully.
"""

import json
import sys
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import Chunk
import config

# Recommended threshold based on empirical testing:
# In-scope queries ("factors affecting enzyme activity") score ~0.9100.
# Out-of-scope queries ("Krebs cycle") peak at ~0.8040.
SIMILARITY_REFUSAL_THRESHOLD = 0.8500


def check_scope(query: str, chapter: str, threshold: float = SIMILARITY_REFUSAL_THRESHOLD) -> dict:
    index_path = Path(config.INDEX_DIR) / "index.faiss"
    chunks_path = Path(config.INDEX_DIR) / "chunks.jsonl"

    index = faiss.read_index(str(index_path))
    chunks = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(Chunk(**json.loads(line)))

    model = SentenceTransformer(config.EMBEDDING_MODEL, local_files_only=True)
    prefixed_query = "query: " + query.strip()
    q_vec = model.encode([prefixed_query], normalize_embeddings=True, convert_to_numpy=True)
    q_vec = np.array(q_vec, dtype=np.float32)

    scores, indices = index.search(q_vec, index.ntotal)

    chapter_matches = []
    for score, idx in zip(scores[0], indices[0]):
        c = chunks[idx]
        if c.chapter == chapter:
            chapter_matches.append((float(score), c))

    if not chapter_matches:
        return {
            "query": query,
            "chapter": chapter,
            "top_score": 0.0,
            "decision": "REFUSE",
            "message": f"Would refuse: Chapter '{chapter}' has no indexed chunks.",
        }

    top_score, top_chunk = chapter_matches[0]

    if top_score < threshold:
        decision = "REFUSE"
        message = (
            f"Would refuse: not covered in this chapter "
            f"(top similarity {top_score:.4f} < threshold {threshold:.4f})."
        )
    else:
        decision = "GENERATE"
        message = (
            f"Would generate normally "
            f"(top similarity {top_score:.4f} >= threshold {threshold:.4f}; matched [{top_chunk.chunk_id}] '{top_chunk.section_heading}')."
        )

    return {
        "query": query,
        "chapter": chapter,
        "top_score": top_score,
        "top_chunk_id": top_chunk.chunk_id,
        "top_section": top_chunk.section_heading,
        "decision": decision,
        "message": message,
    }


def main():
    chapter = "Chapter 6 - Enzymes"
    test_cases = [
        "Krebs cycle",
        "factors affecting enzyme activity",
        "photosynthesis light reaction",  # from Chapter 7, not Chapter 6
        "lock and key model of enzymes",   # in Chapter 6
    ]

    print("=" * 80)
    print("PHASE 6 GRACEFUL REFUSAL DEMONSTRATION")
    print(f"Target Chapter: {chapter}")
    print(f"Refusal Threshold: {SIMILARITY_REFUSAL_THRESHOLD:.4f}")
    print("=" * 80)

    for q in test_cases:
        res = check_scope(q, chapter)
        status_tag = "🔴 [REFUSAL] " if res["decision"] == "REFUSE" else "🟢 [NORMAL]  "
        print(f"\nQUERY: '{q}'")
        print(f"  Result : {status_tag} {res['message']}")
        print(f"  Score  : {res['top_score']:.4f}")
        if res["decision"] == "GENERATE":
            print(f"  Ground : [{res['top_chunk_id']}] {res['top_section']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
