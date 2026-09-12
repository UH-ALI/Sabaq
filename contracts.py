from dataclasses import dataclass, field


@dataclass
class Chunk:
    chunk_id: str          # e.g. "bio9_ch04_c014" — format: {book}_{chapter}_c{seq:03d}
    book: str              # "Biology 9 (STBB, English Medium)"
    chapter: str           # "Chapter 4 - Cells and Tissues"
    section_heading: str   # e.g. "Cell Membrane"
    page_hint: int         # page number in source PDF, for citation display
    text: str              # raw passage text, English


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
    verified: bool               # output of verify.py — drives the UI badge
    verification_note: str       # short human-readable reason, shown in the citation box
    explanation_en: str
    explanation_ur: str
    explanation_ur_roman: str    # from render_urdu.py; toggle display only, never used for grounding


@dataclass
class GradeResult:
    score: float            # 0.0-10.0
    feedback: str
    missed_point: str       # the textbook line/idea the student's answer missed, or "" if none
    source_chunk_id: str


@dataclass
class GenerateRequest:
    book: str               # fixed: "Biology 9 (STBB, English Medium)" for MVP
    chapter: str            # one of the 3 in-scope chapters, exact string match required
    qtype: str              # "mcq" | "short"
    count: int              # 1-10
    language: str           # "en" | "ur"


@dataclass
class GradeRequest:
    question: GeneratedQuestion
    student_answer: str
    tone: str               # "strict" | "friendly"
