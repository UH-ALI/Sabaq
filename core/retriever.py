"""
core/retriever.py

Retrieval component for Sabaq.
Embeds incoming queries using multilingual-e5-base with the mandatory "query: "
prefix, searches the IndexFlatIP FAISS index (cosine similarity), and returns
the top-k matching Chunks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Add project root to sys.path so contracts and config import cleanly
sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import Chunk
import config

# ⚠️ IMPORTANT: The "query: " prefix is REQUIRED by multilingual-e5-base.
# The model was trained with asymmetric instruction prefixes:
#   - "passage: " for documents being indexed (see ingestion/build_index.py)
#   - "query: "   for search queries at retrieval time
# Stripping this prefix causes retrieval quality to collapse.
QUERY_PREFIX = "query: "

# Module-level caches to avoid reloading model / index / chunks on every call
_MODEL: SentenceTransformer | None = None
_INDEX_CACHE: dict[str, faiss.Index] = {}
_CHUNKS_CACHE: dict[str, list[Chunk]] = {}


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(config.EMBEDDING_MODEL, local_files_only=True)
    return _MODEL


def _get_index(index_path: str) -> faiss.Index:
    if index_path not in _INDEX_CACHE:
        path = Path(index_path)
        if not path.exists():
            raise FileNotFoundError(f"FAISS index not found at: {index_path}")
        _INDEX_CACHE[index_path] = faiss.read_index(str(path))
    return _INDEX_CACHE[index_path]


def _get_chunks(chunks_path: str) -> list[Chunk]:
    if chunks_path not in _CHUNKS_CACHE:
        path = Path(chunks_path)
        if not path.exists():
            raise FileNotFoundError(f"Chunks file not found at: {chunks_path}")
        chunks: list[Chunk] = []
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                chunks.append(Chunk(**json.loads(line)))
        _CHUNKS_CACHE[chunks_path] = chunks
    return _CHUNKS_CACHE[chunks_path]


def retrieve(query: str, index_path: str, chunks_path: str, top_k: int = 6) -> list[Chunk]:
    """Embeds query with the 'query: ' prefix (REQUIRED — retrieval quality
    collapses without it), searches the FAISS index, returns top_k Chunks."""
    if not query.strip():
        return []

    model = _get_model()
    index = _get_index(index_path)
    chunks = _get_chunks(chunks_path)

    if index.ntotal == 0 or not chunks:
        return []

    # ⚠️ QUERY_PREFIX is mandatory for asymmetric multilingual-e5 retrieval
    prefixed_query = QUERY_PREFIX + query.strip()

    query_vec = model.encode(
        [prefixed_query],
        normalize_embeddings=True,  # L2-normalize; required for IndexFlatIP = cosine sim
        convert_to_numpy=True,
    )
    query_vec = np.array(query_vec, dtype=np.float32)

    k = min(top_k, index.ntotal)
    _, indices = index.search(query_vec, k)

    results: list[Chunk] = []
    for idx in indices[0]:
        if 0 <= idx < len(chunks):
            results.append(chunks[idx])

    return results


if __name__ == "__main__":
    import os

    index_file = os.path.join(config.INDEX_DIR, "index.faiss")
    chunks_file = os.path.join(config.INDEX_DIR, "chunks.jsonl")

    test_queries = [
        "what is a cell membrane",
        "difference between diffusion and osmosis",
        "structure of mitochondria",
        "plant tissue types",
    ]

    print(f"Testing retrieval using index: {index_file} ({chunks_file})\n")
    for q in test_queries:
        res = retrieve(q, index_file, chunks_file, top_k=3)
        print("=" * 80)
        print(f"QUERY: {q}")
        if not res:
            print("No results found.")
            continue
        top = res[0]
        preview = top.text[:150].replace("\n", " ")
        print(f"TOP RESULT CHUNK ID : {top.chunk_id}")
        print(f"SECTION HEADING     : {top.section_heading}")
        print(f"PAGE HINT           : {top.page_hint}")
        print(f"TEXT PREVIEW (~150c): {preview}...")
        print("=" * 80)
        print()
