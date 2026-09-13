import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

with open("err.log", "w", encoding="utf-8") as f_err:
    f_err.write("Script started\n")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        f_err.write("Loaded dotenv\n")
        print("Step 1: Testing imports...")
        import config
        from contracts import Chunk, GenerateRequest
        from core.retriever import retrieve
        from core.generator import _get_genai_client, _build_prompt

        print("Step 2: Testing retrieve()...")
        chunks = retrieve("Chapter 4 - Cells and Tissues", "data/bio9/index.faiss", "data/bio9/chunks.jsonl", top_k=6)
        print(f"Retrieved {len(chunks)} chunks:")
        for c in chunks[:2]:
            print("  -", c.chunk_id, c.section_heading)

        print("Step 3: Testing Gemini API client...")
        client = _get_genai_client()
        print("Client initialized successfully.")

        print("Step 4: Testing Gemini generation call...")
        from google.genai import types
        resp = client.models.generate_content(
            model=config.LLM_MODEL,
            contents="Return a JSON array with one test item: [{\"test\": true}]",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        print("Gemini response:", resp.text)

    except Exception as e:
        f_err.write("Exception occurred:\n")
        traceback.print_exc(file=f_err)
        f_err.flush()
        print("Error caught and written to err.log")
        raise
    else:
        f_err.write("Completed with success!\n")
