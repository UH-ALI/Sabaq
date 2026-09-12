"""
scripts/test_graceful_failure.py

Phase 6 (Option B) Diagnostic:
Tests retrieval similarity scores for:
1. Out-of-scope query: "Krebs cycle" against Chapter 6 ("Chapter 6 - Enzymes")
2. In-scope query: "factors affecting enzyme activity" against Chapter 6

Retrieval uses multilingual-e5-base with 'query: ' prefix and L2-normalization
against the FAISS IndexFlatIP index (inner product = exact cosine similarity).
"""

import json
import os
import sys
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import Chunk
import config

CHAPTER_6 = "Chapter 6 - Enzymes"


def load_all_chunks() -> list[Chunk]:
    chunks_path = Path(config.INDEX_DIR) / "chunks.jsonl"
    chunks = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(Chunk(**json.loads(line)))
    return chunks


def search_with_scores(query: str, target_chapter: str, top_k: int = 6):
    index_path = Path(config.INDEX_DIR) / "index.faiss"
    index = faiss.read_index(str(index_path))
    chunks = load_all_chunks()

    model = SentenceTransformer(config.EMBEDDING_MODEL, local_files_only=True)
    prefixed_query = "query: " + query.strip()
    q_vec = model.encode([prefixed_query], normalize_embeddings=True, convert_to_numpy=True)
    q_vec = np.array(q_vec, dtype=np.float32)

    # Search all vectors in index to see raw scores
    total_vectors = index.ntotal
    scores, indices = index.search(q_vec, total_vectors)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        c = chunks[idx]
        if c.chapter == target_chapter:
            results.append((float(score), c))
            if len(results) >= top_k:
                break

    return results


def main():
    print("=" * 80)
    print(f"PHASE 6 RETRIEVAL SCORES & REFUSAL THRESHOLD TEST")
    print(f"Target Chapter: {CHAPTER_6}")
    print("=" * 80)

    # Test 1: Out-of-scope query
    query_out = "Krebs cycle"
    print(f"\n--- TEST 1 (Out-of-scope): '{query_out}' ---")
    results_out = search_with_scores(query_out, CHAPTER_6, top_k=6)
    for rank, (score, chunk) in enumerate(results_out, 1):
        preview = " ".join(chunk.text.split())[:120]
        print(f"  #{rank} Score: {score:.4f} | [{chunk.chunk_id}] {chunk.section_heading}")
        print(f"      Excerpt: {preview}...")

    # Test 2: In-scope query
    query_in = "factors affecting enzyme activity"
    print(f"\n--- TEST 2 (In-scope): '{query_in}' ---")
    results_in = search_with_scores(query_in, CHAPTER_6, top_k=6)
    for rank, (score, chunk) in enumerate(results_in, 1):
        preview = " ".join(chunk.text.split())[:120]
        print(f"  #{rank} Score: {score:.4f} | [{chunk.chunk_id}] {chunk.section_heading}")
        print(f"      Excerpt: {preview}...")

    # Comparison summary
    top_out_score = results_out[0][0] if results_out else 0.0
    top_in_score = results_in[0][0] if results_in else 0.0

    print("\n" + "=" * 80)
    print("SUMMARY COMPARISON:")
    print(f"  Out-of-scope Top Score ('{query_out}'): {top_out_score:.4f}")
    print(f"  In-scope Top Score ('{query_in}'):     {top_in_score:.4f}")
    print(f"  Delta (Gap):                            {top_in_score - top_out_score:+.4f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
