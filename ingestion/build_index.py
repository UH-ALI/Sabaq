"""
ingestion/build_index.py

Embeds each chunk with multilingual-e5-base using the "passage: " prefix
(mandatory — add a code comment flagging this so it's never accidentally
stripped later), L2-normalizes, writes an IndexFlatIP FAISS index to
index_out_path.

Vector order matches line order in chunks.jsonl so that index position i
corresponds to the chunk on line i of the matching chunks.jsonl.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import Chunk
import config


# ⚠️  IMPORTANT: The "passage: " prefix is REQUIRED by multilingual-e5-base.
# The model was trained with instruction prefixes:
#   - "passage: " for documents being indexed
#   - "query: "   for queries at retrieval time (see core/retriever.py)
# Stripping this prefix causes retrieval quality to collapse significantly.
# Do NOT remove it. See: https://huggingface.co/intfloat/multilingual-e5-base
PASSAGE_PREFIX = "passage: "


def build_index(chunks: list[Chunk], index_out_path: str) -> None:
    """Embeds each chunk.text with the 'passage: ' prefix (multilingual-e5-base),
    L2-normalizes, writes an IndexFlatIP to index_out_path."""

    if not chunks:
        raise ValueError("Cannot build index from empty chunk list.")

    print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
    model = SentenceTransformer(config.EMBEDDING_MODEL, local_files_only=True)

    # ⚠️  PASSAGE_PREFIX is mandatory — see module-level comment above.
    texts = [PASSAGE_PREFIX + chunk.text for chunk in chunks]

    print(f"Embedding {len(texts)} chunks ...")
    # normalize_embeddings=True does L2 normalization in-model for efficiency
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,  # L2-normalize; required for IndexFlatIP = cosine sim
        convert_to_numpy=True,
    )

    embeddings = np.array(embeddings, dtype=np.float32)
    dimension = embeddings.shape[1]
    print(f"Embedding dimension: {dimension}  |  shape: {embeddings.shape}")

    # Sanity check: verify embeddings are already L2-normalized (norms ≈ 1.0)
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-4), (
        f"Embeddings are not L2-normalized — mean norm={norms.mean():.4f}. "
        "Check normalize_embeddings=True."
    )

    # IndexFlatIP = exact inner-product search.
    # Because vectors are L2-normalized, inner product = cosine similarity.
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    out_path = Path(index_out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(out_path))
    print(f"FAISS index written to: {out_path}  ({index.ntotal} vectors)")


# ---------------------------------------------------------------------------
# CLI entry point — builds the index from chunks.jsonl
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    chunks_path = Path(config.INDEX_DIR) / "chunks.jsonl"
    index_path = Path(config.INDEX_DIR) / "index.faiss"

    print(f"Reading chunks from: {chunks_path}")
    chunks: list[Chunk] = []
    with chunks_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            chunks.append(Chunk(**obj))

    print(f"Loaded {len(chunks)} chunks.")
    build_index(chunks, str(index_path))

    # Verify: load the written index and confirm ntotal matches
    loaded = faiss.read_index(str(index_path))
    assert loaded.ntotal == len(chunks), (
        f"Index has {loaded.ntotal} vectors but expected {len(chunks)}"
    )
    print(f"\n✓ Index verified: {loaded.ntotal} vectors, dimension {loaded.d}")
    print("Phase 2 complete.")
