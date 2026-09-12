# Sabaq — Sequential Build Order (Solo-First)

**How to use this document:** work top to bottom, in order. Each step says what to build, why it comes at this point, and what "done" looks like before you move on. If a teammate becomes available at any point, hand them the *next unstarted step*, not a random slice — that's the only coordination rule you need. This replaces the original 4-lane parallel plan, which only works if 4 people actually show up.

Reference `API_CONTRACTS.md` for every data shape and function signature mentioned below — don't let Antigravity invent shapes that aren't there.

---

## PHASE 0 — Setup (Hour 0-1)

1. Clone the repo, confirm Python 3.11, install a starter `requirements.txt`: `sentence-transformers`, `faiss-cpu`, `pypdf`, `streamlit`, `google-generativeai` (or your chosen LLM SDK), `python-dotenv`.
2. Get ONE API key for your chosen hosted LLM (Gemini Flash recommended per the original plan — free tier, strong Urdu, no local GPU needed). Put it in `.env`, never commit it.
3. Download the STBB Biology Class 9 (English Medium) PDF. Open it and manually check: does it have a real text layer (can you select/copy text), or is it scanned images? **This determines everything downstream — verify before writing any code.**

**Done when:** you can run `python -c "import faiss, sentence_transformers, streamlit"` with no errors, and you've confirmed the PDF has a real text layer.

---

## PHASE 1 — Freeze the Contracts (Hour 1-2)

Do this before writing any real logic, even solo. It costs little time and prevents you from having to rewrite things later when the shape of a "question" or "chunk" changes mid-build.

1. Create `contracts.py` with the exact dataclasses from `API_CONTRACTS.md` §1.
2. Create `fixtures/demo_fixtures.json` — hand-write 3 realistic `GeneratedQuestion` objects and 1 `GradeResult`, based on Chapter 4 (Cells and Tissues) content you can see in the PDF. These don't need to be AI-generated — write them yourself, they're just test data.
3. Create `core/mock_core.py` implementing `generate_questions()` and `grade_answer()` that return the fixtures. Signatures exactly per `API_CONTRACTS.md` §3.
4. Create `config.py` with `USE_MOCK_CORE = True` and the other flags listed in `API_CONTRACTS.md` §4.

**Done when:** `from core.mock_core import generate_questions, grade_answer` works and returns your fixture data.

**Why this step exists even solo:** it forces you to decide the exact shape of a "question" before you've built either the generator or the UI — so neither one has to be rewritten when the other reveals a missing field.

---

## PHASE 2 — Ingestion Pipeline (Hour 2-5)

This is pure backend, no UI needed yet. Build and test entirely from the command line.

1. `ingestion/parse_pdf.py` — extract text from Chapter 4 first (your primary demo chapter), split by heading into chunks (~300-400 tokens, ~60-token overlap). Signature per `API_CONTRACTS.md` §3.
   - **Verify immediately**: print 3 random chunks and read them. Garbled text here poisons everything downstream — catch it now, not on Day 2.
2. Extend to Chapter 1 and Chapter 6.
3. Write all chunks to `data/bio9/chunks.jsonl` in the exact format from `API_CONTRACTS.md` §2.
4. `ingestion/build_index.py` — embed all chunks with `multilingual-e5-base`, using the `"passage: "` prefix (this prefix is not optional — retrieval quality collapses without it), write to `data/bio9/index.faiss`.

**Done when:** `chunks.jsonl` exists with entries for all 3 chapters, and `index.faiss` exists and loads without error.

---

## PHASE 3 — Retrieval (Hour 5-6)

1. `core/retriever.py` — embed a test query with the `"query: "` prefix, search the index, return top-k chunks.
2. Manually test: query "what is a cell membrane" against the Chapter 4 index — does it actually retrieve the cell membrane passage? Test 3-4 queries by hand before moving on.

**Done when:** you've manually confirmed retrieval returns sensible, correct chunks for at least 3 different queries.

---

## PHASE 4 — Generation (Hour 6-9)

1. `core/generator.py` — implement `generate_questions()` for real: retrieve chunks → prompt the LLM with retrieved text + instructions ("use ONLY the provided content") → parse into `GeneratedQuestion` objects with `source_chunk_id` set.
2. Test from the CLI (no UI yet): request 5 MCQs on Chapter 4, print them, read every one. Do they make sense? Does each `source_chunk_id` actually resolve to a real chunk?

**Done when:** a CLI script `python -m core.cli --chapter bio9_ch04 --qtype mcq --n 5` prints 5 coherent questions with valid, resolvable source chunk IDs.

---

## PHASE 5 — Verification Layer (Hour 9-11)

This is your single most important differentiator — do not rush or skip testing it.

1. `core/verify.py` — implement `verify()`: an independent LLM call checking whether `question.model_answer` is actually supported by `source_chunk.text`.
2. **Deliberately test failure**: hand-write one bad question (wrong answer, or one referencing content not in the chunk) and confirm `verify()` actually returns `False` for it. If it doesn't, your verification isn't real — fix it before moving on. This is the exact thing a sharp judge will ask about, and you need to have actually seen it work, not assume it does.
3. Wire `verify()` into the end of `generate_questions()`'s output path so every question gets a real `verified` value before it's returned.

**Done when:** you have seen, with your own eyes, both a `True` and a `False` verification result on real test cases.

---

## PHASE 6 — Graceful Failure (Hour 11-12)

1. Test asking `generate_questions()` for content that Chapter 6 (Enzymes) doesn't actually cover (e.g., "generate a question about the Krebs cycle" if that's genuinely absent from the chapter).
2. Confirm the system says "this isn't covered in your chapter" rather than inventing an answer. Adjust the prompt constraints in `generator.py` if it doesn't.

**Done when:** you have a reproducible example of the system correctly refusing to answer something outside the source material — save this exact example, it's your demo's second beat.

---

## PHASE 7 — UI (Hour 12-16)

Only start this once Phase 1-6 are solid, OR run it in parallel from Hour 2 if you have a second person — since it was built against mocks from the start, it never has to wait.

1. `app.py` + `ui/generate_view.py` — chapter dropdown (3 chapters) → qtype + count + language inputs → "Generate" button → question cards showing: question text, options (if MCQ), a ✅/⚠️ badge from `verified`, and a collapsible box showing the cited passage.
2. `ui/attempt_view.py` — pick a generated question → text input for student answer → "Submit" → shows `GradeResult` (score, feedback, missed point).
3. Language toggle: three buttons/tabs (English / اردو / Roman Urdu) switching which explanation field is displayed.
4. Keep `USE_MOCK_CORE = True` while building this — you're wiring UI to `mock_core`, not the real engine, so this phase never blocks on Phase 2-6 finishing.

**Done when:** the full 3-screen flow works end-to-end using mock data.

---

## PHASE 8 — Roman Urdu Render Pass (Hour 16-18)

1. `core/render_urdu.py` — few-shot prompt (2-3 natural examples) converting `explanation_en` into natural Roman Urdu. Low temperature.
2. Test on 2-3 real explanations. Read them out loud — do they sound like how a student actually texts, or stiff/formal? Iterate the few-shot examples if it sounds robotic.
3. Save one clean before/after pair (formal Urdu script vs. natural Roman Urdu) as a demo asset — you'll show this live.

**Done when:** you have one Roman Urdu output you're genuinely comfortable showing on stage.

---

## PHASE 9 — Integration (Hour 18-20)

1. Flip `USE_MOCK_CORE = False` in `config.py`.
2. Run the full UI flow against the real engine. If something breaks: check mocks still work (isolates whether it's a UI bug or engine bug) — this is the entire value of having built against mocks from the start.
3. Fix integration bugs. Budget real time here — this is where hidden assumptions between phases usually surface.

**Done when:** the deployed-looking full flow (select → generate → attempt) works with real generation, real verification, real grading — no mocks.

---

## PHASE 10 — Attempt Grading, End-to-End (Hour 20-22)

1. `core/grader.py` — implement `grade_answer()` for real if not already done: student answer vs. model answer + source chunk → score, feedback, missed point.
2. Test with a deliberately wrong/incomplete answer — does the feedback correctly identify what was missed, with reference to the actual source line?

**Done when:** one full real cycle works: generate a question → answer it (correctly and incorrectly) → see accurate, source-referenced feedback both times.

---

## PHASE 11 — Deploy (Hour 22-26, spilling into Day 2 morning)

1. Deploy to Streamlit Community Cloud (or HF Spaces). Put the API key in Streamlit secrets, not in code.
2. Test the live URL on a different device/network than the one you built on — cold starts and missing secrets are the most common deploy-day surprise.
3. Keep the app "warm" (visit it periodically) before judging so it's not cold-starting live.

**Done when:** you have a public URL that works from a phone on mobile data, not just your dev machine.

---

## PHASE 12 — Evaluation Artifacts (Day 2, whenever core is stable)

If you're solo and time is tight, this phase is lower priority than a working demo — but even 20-30 hand-checked Q&A pairs give you a real number to say instead of "trust me."

1. `eval/golden_set.jsonl` — hand-write or hand-verify 20-30 lines per the schema in `API_CONTRACTS.md` §2.
2. `eval/evaluate.py` — script that checks whether retrieval returns chunks matching `supporting_chunk_hint` for each golden question; outputs `retrieval_hit_rate` to `eval/metrics.csv`.

**Done when:** you can say one real sentence like "on our 25-question golden set, retrieval hit rate was X%" — even a modest honest number beats an unverified claim.

---

## PHASE 13 — Demo Prep (Day 2, last few hours)

1. Pre-generate and cache the exact questions you'll show live (don't rely on live API calls working perfectly under demo pressure) — but keep ONE live generation in the script to prove it's real.
2. Record a full backup video of the working app, in case live demo/wifi fails.
3. Rehearse the 60-second script (see below) at least twice, out loud, timed.

**Demo script (60 seconds, 3 moments):**
1. **Hook (10s):** the problem — generic apps, no grounding in the actual textbook.
2. **Moment 1 (20s):** generate 5 MCQs on Ch 4 → show the ✅ verified badge → open the citation box, showing the real textbook line.
3. **Moment 2 (10s):** ask about content Ch 6 doesn't cover → show the graceful refusal. This is the anti-hallucination beat — say explicitly "we won't invent content," since that's the line a judge remembers.
4. **Moment 3 (15s):** toggle one explanation to Roman Urdu, show the before/after.
5. **Close (5s):** one line on what's next (more chapters, more boards, OCR upload).

---

## What Gets Cut First If Time Runs Out (in this order)

1. Photo/OCR upload (never in critical path per PRD §5)
2. Chapter 1 and Chapter 6 (keep Chapter 4 rock-solid; the others are nice-to-have breadth)
3. Attempt-mode "strict vs friendly" tone toggle (keep one tone, working)
4. Full 20-30 line golden set (a working demo beats an evaluation script if you must choose)
5. **Never cut:** the verification layer and the graceful-failure case — these are the entire pitch.
