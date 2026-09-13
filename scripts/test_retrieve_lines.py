import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.retriever import _get_model, _get_index, _get_chunks, QUERY_PREFIX
import numpy as np

print("Line 1: getting model...")
model = _get_model()
print("Model loaded.")

print("Line 2: getting index...")
index = _get_index("data/bio9/index.faiss")
print(f"Index loaded. Total vectors: {index.ntotal}")

print("Line 3: getting chunks...")
chunks = _get_chunks("data/bio9/chunks.jsonl")
print(f"Chunks loaded. Total chunks: {len(chunks)}")

print("Line 4: encoding query...")
prefixed_query = QUERY_PREFIX + "what is cell membrane"
query_vec = model.encode(
    [prefixed_query],
    normalize_embeddings=True,
    convert_to_numpy=True,
)
print("Query encoded. Shape:", query_vec.shape)

print("Line 5: faiss search...")
query_vec = np.array(query_vec, dtype=np.float32)
distances, indices = index.search(query_vec, 3)
print("Search succeeded! Indices:", indices)
print("Retrieved chunk:", chunks[indices[0][0]].chunk_id)
