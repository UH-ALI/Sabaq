"""
scripts/build_index_step.py

Stepwise version of build_index for debugging silent failures.
Prints output at each stage so we can see exactly where it dies.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Step 1: imports...", flush=True)
import faiss
import numpy as np
print("  faiss OK", flush=True)

from sentence_transformers import SentenceTransformer
print("  sentence_transformers OK", flush=True)

import config
from contracts import Chunk
print("Step 1 done.\n", flush=True)

print("Step 2: load chunks...", flush=True)
chunks_path = Path(config.INDEX_DIR) / "chunks.jsonl"
chunks = []
with chunks_path.open(encoding="utf-8") as f:
    for line in f:
        if line.strip():
            obj = json.loads(line)
            chunks.append(Chunk(**obj))
print(f"  Loaded {len(chunks)} chunks.\n", flush=True)

print("Step 3: load model...", flush=True)
model = SentenceTransformer(config.EMBEDDING_MODEL)
print(f"  Model loaded. Dimension: {model.get_sentence_embedding_dimension()}\n", flush=True)

print("Step 4: embed (batch_size=16)...", flush=True)
PASSAGE_PREFIX = "passage: "
texts = [PASSAGE_PREFIX + c.text for c in chunks]
embeddings = model.encode(
    texts,
    batch_size=16,          # smaller batch to reduce peak RAM
    show_progress_bar=True,
    normalize_embeddings=True,
    convert_to_numpy=True,
)
import numpy as np
embeddings = np.array(embeddings, dtype=np.float32)
print(f"  Embeddings shape: {embeddings.shape}\n", flush=True)

print("Step 5: build and write FAISS index...", flush=True)
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)
out_path = Path(config.INDEX_DIR) / "index.faiss"
faiss.write_index(index, str(out_path))
print(f"  Written: {out_path} ({index.ntotal} vectors)\n", flush=True)

print("Step 6: verify round-trip...", flush=True)
loaded = faiss.read_index(str(out_path))
assert loaded.ntotal == len(chunks), f"Mismatch: {loaded.ntotal} vs {len(chunks)}"
print(f"  OK: {loaded.ntotal} vectors == {len(chunks)} chunks\n", flush=True)

print("Phase 2 rebuild complete.", flush=True)
