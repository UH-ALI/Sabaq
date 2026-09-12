# Sabaq — API & Data Contracts

**Purpose of this document:** every data shape and function signature in the system, frozen, so an AI coding agent (or a teammate) has zero ambiguity to fill in with a guess. If Antigravity ever needs to invent a field name or return type that isn't here, stop and add it here first — then build.

---

## 1. Core Data Shapes (`contracts.py`)

```python
from dataclasses import dataclass, field

@dataclass
class Chunk:
    chunk_id: str          # e.g. "bio9_ch04_c014" — format: {book}_{chapter}_c{seq:03d}
    book: str              # "Biology 9 (STBB, English Medium)"
    chapter: str            # "Chapter 4 - Cells and Tissues"
    section_heading: str    # e.g. "Cell Membrane"
    page_hint: int          # page number in source PDF, for citation display
    text: str               # raw passage text, English

@dataclass
class GeneratedQuestion:
    q_id: str                    # uuid4 hex string
    qtype: str                   # exactly "mcq" | "short" — no other values
    question: str
    options: list[str]           # length 4 for mcq, empty list for short
    correct_option_index: int    # 0-3 for mcq, -1 for short
    model_answer: str
    marks: int                   # 1 for mcq, 2-5 for short
    language: str                # "en" | "ur" — the language questions/answers are generated in
    source_chunk_id: str         # MUST resolve to a real chunk_id in chunks.jsonl
    verified: bool                # output of verify.py — drives the UI badge
    verification_note: str        # short human-readable reason, shown in the citation box
    explanation_en: str
    explanation_ur: str
    explanation_ur_roman: str     # from render_urdu.py; toggle display only, never used for grounding

@dataclass
class GradeResult:
    score: float            # 0.0-10.0
    feedback: str
    missed_point: str       # the textbook line/idea the student's answer missed, or "" if none
    source_chunk_id: str

@dataclass
class GenerateRequest:
    book: str                # fixed: "Biology 9 (STBB, English Medium)" for MVP
    chapter: str              # one of the 3 in-scope chapters, exact string match required
    qtype: str                # "mcq" | "short"
    count: int                # 1-10
    language: str             # "en" | "ur"

@dataclass
class GradeRequest:
    question: GeneratedQuestion
    student_answer: str
    tone: str                 # "strict" | "friendly"
```

**Rule:** these dataclasses are the single source of truth. Every function below takes/returns exactly these — no ad-hoc dicts, no renaming fields mid-pipeline.

---

## 2. File Formats

### `data/bio9/chunks.jsonl`
One JSON object per line, matching the `Chunk` schema exactly:
```json
{"chunk_id": "bio9_ch04_c014", "book": "Biology 9 (STBB, English Medium)", "chapter": "Chapter 4 - Cells and Tissues", "section_heading": "Cell Membrane", "page_hint": 42, "text": "The cell membrane is a selectively permeable layer..."}
```

### `data/bio9/index.faiss`
A FAISS `IndexFlatIP` (exact cosine similarity after L2-normalized embeddings). One index file per book. Vector order must match line order in the corresponding `chunks.jsonl` so index position `i` = chunk on line `i`.

### `eval/golden_set.jsonl`
One hand-written Q&A per line, used to sanity-check retrieval and generation quality:
```json
{"q_id": "g001", "book": "Biology 9 (STBB, English Medium)", "chapter": "Chapter 4 - Cells and Tissues", "qtype": "mcq", "question": "...", "answer": "...", "supporting_chunk_hint": "Cell Membrane section", "page_hint": 42}
```
Target: 30-50 lines, hand-written or hand-checked, not LLM-generated (they're your ground truth).

### `eval/metrics.csv`
Columns: `run_id, timestamp, retrieval_hit_rate, num_questions_generated, num_verified_pass, num_verified_fail, avg_grade_latency_sec`

---

## 3. Core Function Signatures

```python
# ingestion/parse_pdf.py
def parse_pdf(pdf_path: str, book_name: str, chapter_name: str) -> list[Chunk]:
    """Extracts text from the PDF's text layer (no OCR), splits by heading,
    ~300-400 tokens per chunk with ~60-token overlap. Raises ValueError if
    extracted text fails a basic sanity check (alphabetic ratio < 0.5)."""

# ingestion/build_index.py
def build_index(chunks: list[Chunk], index_out_path: str) -> None:
    """Embeds each chunk.text with the 'passage: ' prefix (multilingual-e5-base),
    L2-normalizes, writes an IndexFlatIP to index_out_path."""

# core/retriever.py
def retrieve(query: str, index_path: str, chunks_path: str, top_k: int = 6) -> list[Chunk]:
    """Embeds query with the 'query: ' prefix (REQUIRED — retrieval quality
    collapses without it), searches the FAISS index, returns top_k Chunks."""

# core/generator.py
def generate_questions(req: GenerateRequest) -> list[GeneratedQuestion]:
    """Retrieves relevant chunks for req.chapter, prompts the LLM to generate
    req.count questions of req.qtype in req.language, using ONLY the retrieved
    chunk text. Each returned question must have source_chunk_id set to the
    actual chunk_id it was grounded in. Does NOT set `verified` — that's verify.py's job."""

# core/verify.py
def verify(question: GeneratedQuestion, source_chunk: Chunk) -> tuple[bool, str]:
    """Independent LLM check: is question.model_answer actually supported by
    source_chunk.text? Returns (verified: bool, verification_note: str).
    This function must be called on every generated question before display —
    never skip it, never default to True."""

# core/render_urdu.py
def render_roman_urdu(explanation_en: str) -> str:
    """Renders explanation_en into natural Roman Urdu using a few-shot prompt
    (3 example pairs of formal->natural Roman Urdu). Low temperature.
    Applied to explanations ONLY — never called on questions or model_answer."""

# core/grader.py
def grade_answer(req: GradeRequest) -> GradeResult:
    """Grades req.student_answer against req.question.model_answer and the
    original source chunk. Returns score 0-10, feedback text, and the specific
    missed_point if the answer was incomplete or wrong."""

# core/mock_core.py  — build this FIRST, before any real logic
def generate_questions(req: GenerateRequest) -> list[GeneratedQuestion]:
    """Returns 3 hardcoded GeneratedQuestion objects from fixtures/demo_fixtures.json.
    Same signature as the real generator — UI code never needs to change its import."""

def grade_answer(req: GradeRequest) -> GradeResult:
    """Returns one hardcoded GradeResult. Same signature as the real grader."""
```

**Golden rule:** `core/mock_core.py` implements the exact same function names and signatures as the real `core/generator.py` + `core/grader.py`. The UI imports from `mock_core` on day one and only ever changes ONE line later (`config.py`'s `USE_MOCK_CORE` flag) to point at the real implementation. This is what lets you build the UI and the engine without either one blocking the other, even solo — you can build the UI against mocks in the morning and the real engine in the afternoon without them fighting over the same half-finished code.

---

## 4. Config (`config.py`) — the only shared state file

```python
USE_MOCK_CORE: bool = True   # flip to False only when generator.py + verify.py pass their CLI smoke test
INDEX_DIR: str = "data/bio9"
LLM_MODEL: str = "gemini-2.0-flash"   # or your chosen hosted API
EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"
DEFAULT_TOP_K: int = 6
```
No logic lives in this file — only paths, model names, and flags. If you catch yourself writing an `if` statement here, it belongs somewhere else.

## 5. Hallucination Guard — Non-Negotiable Contract

Every `GeneratedQuestion` MUST go through `verify()` before it is displayed. There is no code path where a question reaches the UI with `verified` unset or defaulted to `True` without actually running the check. If `verify()` returns `False`, the question is either discarded or shown with an explicit "could not verify against your textbook" state — never silently upgraded to look verified.
