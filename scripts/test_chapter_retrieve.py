import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.retriever import retrieve
import config

chunks = retrieve("Chapter 4 - Cells and Tissues", "data/bio9/index.faiss", "data/bio9/chunks.jsonl", top_k=10)
for i, c in enumerate(chunks):
    print(f"#{i+1} [{c.chunk_id}] {c.section_heading} ({c.chapter})")
