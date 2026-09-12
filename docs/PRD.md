# Sabaq — Product Requirements Document (PRD)

**Status:** FROZEN for hackathon duration. Do not change scope after Hour 1 without crossing it out here, visibly, with a reason.
**Owner:** You (solo-first; teammates slot in if/when available).
**Duration:** 2 days.

---

## 1. One-Sentence Definition

Sabaq is a Streamlit app where a student picks a specific textbook chapter, gets AI-generated practice questions that are grounded in and verified against that chapter's actual text, and can attempt them for feedback — in English, Urdu script, or Roman Urdu.

## 2. The Exact MVP (no more, no less)

**Book/Board/Class/Subject:** Sindh Textbook Board (STBB), English Medium, Biology, Class 9. Nothing else.

**Chapters (exactly 3, no more):**
| Chapter | Role |
|---|---|
| Ch 1 — Introduction to Biology | Warm-up / secondary demo |
| Ch 4 — Cells and Tissues | **Primary demo chapter** — build and polish this one first, always |
| Ch 6 — Enzymes | Used only to demonstrate graceful failure (asking about content it doesn't cover) |

**Core user flow (exactly 3 screens):**
1. **Select** — student picks chapter (dropdown, not upload, for MVP — see §5)
2. **Generate** — picks question type (MCQ / short) + count + language → sees questions, each with a ✅ verified badge and a collapsible "from your textbook" citation
3. **Attempt** — types an answer to one question → gets a score + feedback + the textbook line they missed

## 3. Features IN scope

- [ ] Chapter text extraction from PDF (text-layer extraction, not OCR — see §5)
- [ ] Chunking + embedding + retrieval (FAISS + multilingual-e5-base)
- [ ] Question generation (MCQ + short answer), grounded only in retrieved chunks
- [ ] Verification pass: reject/flag any question whose answer isn't actually supported by the source chunk
- [ ] Citation display: the literal retrieved passage shown to the student
- [ ] Graceful refusal: if asked about content not in the chapter, say so — never invent
- [ ] Attempt mode: student answer → rubric-graded feedback referencing the source
- [ ] Language toggle for explanations: English / Urdu script / Roman Urdu
- [ ] Deployed, working Streamlit URL (not just localhost)

## 4. Features EXPLICITLY out of scope — say this in the pitch

- Any board other than Sindh Textbook Board
- Any subject other than Biology, any class other than 9
- Adaptive difficulty / spaced repetition
- Accounts, login, payments, mobile app, voice
- SLO (Student Learning Outcome) alignment claims — no official SLO docs were found for this subject; the claim is **"aligned with your textbook and board exercise style,"** never "SLO-aligned"
- Roman Urdu question *generation* — Roman Urdu applies to explanations only; questions themselves stay English/Urdu-script

## 5. Photo/OCR upload: DEFERRED, not core path

Original plan included photo upload with Tesseract + Gemini-vision fallback. **For a solo/small-team build, this is cut from the critical path.** Reasoning: OCR is a second entire pipeline (preprocessing, engine routing, fallback logic) competing for the same 48 hours as your actual differentiator (verified generation). Build the PDF-text-layer path first, fully, and polished. Only add OCR photo upload on Day 2 if the core flow is done, tested, and deployed with time to spare. If it doesn't make it in, the pitch honestly says "PDF upload today; photo/OCR is the next feature" — this is a completely normal and forgivable scope cut, not a weakness.

## 6. The Differentiators (what you say when judges ask "so what")

1. **Grounded, not generic** — every question traces to an actual retrieved passage from the real textbook, not the model's general knowledge.
2. **Verified, not trusted blindly** — an independent check confirms the answer is actually supported by the source before showing it. This is the single most defensible technical claim in the project — protect it, test it, don't fake it.
3. **Graceful failure over hallucination** — asked about something outside the chapter, it says so. This is the moment that separates you from every prompt-wrapper hackathon project a judge has already seen ten of.
4. **Roman Urdu explanations** — most tools default to formal Urdu script or awkward transliteration; natural Roman Urdu (how students actually text) is a real, visible, checkable difference.

## 7. Success Criteria (how you'll know it's actually done)

- Running the CLI on Chapter 4 with a request for 5 MCQs returns 5 questions, each with a `source_chunk_id` that resolves to a real chunk in `chunks.jsonl`.
- Asking for a question about "Krebs cycle" against Chapter 6 (Enzymes) returns a graceful refusal, not a hallucinated answer.
- The verification pass actually rejects at least one deliberately-bad test question during development — if it never rejects anything in testing, you haven't tested it hard enough, and you cannot honestly claim it works on stage.
- The Streamlit app is reachable via a public URL, not just localhost, at the time of judging.
- One full attempt-mode cycle (question → student answer → graded feedback with source reference) works end-to-end without manual intervention.

## 8. Risk Register (carried from original plan, still valid)

| Risk | Mitigation |
|---|---|
| PDF extraction garbled | Verify Hour 1, before anything else is built on top of it |
| LLM hallucinates beyond the chapter | Verification pass + constrained prompt + you must deliberately test a failure case |
| Roman Urdu sounds robotic | Few-shot prompt with natural examples, pre-generate demo pairs the night before |
| API quota runs out mid-demo | Cache/pre-generate the actual demo content; live-generate only once on stage |
| Solo build runs out of time | Section 5 (OCR) is the first thing cut; core 3-screen flow is never cut |
