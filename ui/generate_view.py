"""
ui/generate_view.py

Streamlit view for Screen 1 & 2:
- Chapter selection (Class 9 Biology, STBB)
- Question generation parameters (Type, Count, Language)
- Question cards with:
  - Verified badge (✅ Verified / ⚠️ Unverified)
  - Collapsible textbook citation box
  - Language toggle for explanations (English, اردو, Roman Urdu)
  - Action button to attempt the question
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import streamlit as st

import config
from contracts import GenerateRequest, GeneratedQuestion, Chunk

if config.USE_MOCK_CORE:
    from core.mock_core import generate_questions
else:
    from core.generator import generate_questions

CHAPTER_OPTIONS = [
    "Chapter 4 - Cells and Tissues",
    "Chapter 1 - Introduction to Biology",
    "Chapter 6 - Enzymes",
]

CHAPTER_DESCRIPTIONS = {
    "Chapter 4 - Cells and Tissues": "Primary Demo • 65 indexed sections covering microscopy, organelles, and tissues",
    "Chapter 1 - Introduction to Biology": "Secondary Demo • 50 sections covering branches, careers, and biological organization",
    "Chapter 6 - Enzymes": "Graceful Failure Demo • 17 sections covering enzyme characteristics and mechanisms",
}


@st.cache_data
def load_chunk_lookup() -> dict[str, dict]:
    chunks_path = Path(config.INDEX_DIR) / "chunks.jsonl"
    lookup = {}
    if chunks_path.exists():
        with open(chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    lookup[item["chunk_id"]] = item
    return lookup


def render_generate_screen():
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <h1 style="font-size: 2.2rem; font-weight: 700; margin-bottom: 6px; color: #ffffff;">
                Practice Question Generator
            </h1>
            <p style="color: #94a3b8; font-size: 1.05rem; margin: 0;">
                Generate textbook-grounded exam questions verified against Sindh Textbook Board Biology 9.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top Control Card
    with st.container():
        st.markdown('<div class="control-card">', unsafe_allow_html=True)
        st.markdown(
            '<p style="color: #cbd5e1; font-size: 0.96rem; margin: 0 0 16px 0;">'
            'Pick a chapter, generate practice questions grounded in your actual textbook, then try answering them yourself.'
            '</p>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns([1.6, 1.2], gap="large")

        with col1:
            selected_chapter = st.selectbox(
                "Select Textbook Chapter",
                options=CHAPTER_OPTIONS,
                index=0,
                help="Class 9 Biology (English Medium), Sindh Textbook Board (STBB)",
            )
            st.caption(f"📘 {CHAPTER_DESCRIPTIONS.get(selected_chapter, '')}")

        with col2:
            sub_col1, sub_col2, sub_col3 = st.columns([1, 1, 1])
            with sub_col1:
                qtype = st.selectbox("Type", options=["MCQ", "Short"], index=0)
            with sub_col2:
                count = st.number_input("Count", min_value=1, max_value=10, value=3, step=1)
            with sub_col3:
                lang = st.selectbox("Language", options=["English (en)", "Urdu (ur)"], index=0)

        gen_button = st.button(
            "⚡ Generate Practice Questions",
            type="primary",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Generation trigger
    if gen_button:
        lang_code = "ur" if "Urdu" in lang else "en"
        qtype_code = "mcq" if qtype == "MCQ" else "short"

        req = GenerateRequest(
            book="Biology 9 (STBB, English Medium)",
            chapter=selected_chapter,
            qtype=qtype_code,
            count=int(count),
            language=lang_code,
        )

        with st.spinner("Retrieving verified textbook passages and generating questions..."):
            questions = generate_questions(req)
            st.session_state["questions"] = questions
            st.session_state["selected_chapter"] = selected_chapter
            st.toast(f"Generated {len(questions)} verified questions!", icon="✅")

    # Render questions if available
    questions: list[GeneratedQuestion] = st.session_state.get("questions", [])
    chunk_lookup = load_chunk_lookup()

    if questions:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 28px 0 16px 0;">
                <h3 style="margin: 0; font-size: 1.4rem; font-weight: 700; color: #ffffff;">
                    Generated Questions ({len(questions)})
                </h3>
                <span style="background: #334155; color: #e2e8f0; padding: 4px 12px; border-radius: 9999px; font-size: 0.85rem; font-weight: 500;">
                    Mode: {'Mock Core (Offline)' if config.USE_MOCK_CORE else 'Live LLM Engine'}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for idx, q in enumerate(questions, 1):
            render_question_card(idx, q, chunk_lookup)
    else:
        st.info("👆 Click **'Generate Practice Questions'** above to load practice questions from your textbook.")


def render_question_card(idx: int, q: GeneratedQuestion, chunk_lookup: dict[str, dict]):
    with st.container():
        st.markdown('<div class="question-card">', unsafe_allow_html=True)

        # Card Header: Number, Marks, and Verification Badge
        badge_html = (
            '<span class="badge badge-verified">✅ Verified against textbook</span>'
            if q.verified
            else '<span class="badge badge-unverified">⚠️ Unverified / Outside text</span>'
        )

        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <div>
                    <span style="background: #0f172a; color: #38bdf8; border: 1px solid #38bdf8; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">Q{idx}</span>
                    <span style="color: #94a3b8; font-size: 0.88rem; margin-left: 8px;">{q.qtype.upper()} • {q.marks} {'mark' if q.marks == 1 else 'marks'}</span>
                </div>
                <div>
                    {badge_html}
                </div>
            </div>
            <div style="font-size: 1.15rem; font-weight: 600; color: #ffffff; line-height: 1.5; margin-bottom: 16px;">
                {q.question}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Options if MCQ
        if q.qtype == "mcq" and q.options:
            st.markdown('<div style="margin-bottom: 16px;">', unsafe_allow_html=True)
            for opt_idx, opt in enumerate(q.options):
                is_correct = opt_idx == q.correct_option_index
                letter = chr(65 + opt_idx)
                if is_correct:
                    st.markdown(
                        f"""
                        <div class="option-row option-correct">
                            <span class="option-letter">{letter}</span>
                            <span style="flex-grow: 1;">{opt}</span>
                            <span style="color: #059669; font-weight: 600; font-size: 0.85rem;">✓ Correct Answer</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="option-row option-default">
                            <span class="option-letter">{letter}</span>
                            <span>{opt}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)

        # Model Answer Box (for Short questions or collapsible for review)
        if q.qtype == "short":
            st.markdown(
                f"""
                <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 4px; margin-bottom: 14px;">
                    <div style="font-weight: 600; color: #1e3a8a; font-size: 0.88rem; margin-bottom: 4px;">Standard Textbook Answer:</div>
                    <div style="color: #334155; font-size: 0.95rem; line-height: 1.5;">{q.model_answer}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Collapsible Citation Box
        src_chunk = chunk_lookup.get(q.source_chunk_id)
        section_title = src_chunk.get("section_heading", "Textbook Section") if src_chunk else "Textbook Section"
        page_no = src_chunk.get("page_hint", "PDF") if src_chunk else "PDF"
        chunk_text = src_chunk.get("text", "") if src_chunk else ""

        with st.expander(f"📖 Cited from your textbook ({section_title} • Page {page_no})"):
            if q.verification_note:
                st.markdown(f"**Verification note:** *{q.verification_note}*")
            if chunk_text:
                st.markdown(
                    f"""
                    <blockquote style="margin: 8px 0; padding: 10px 16px; background: #ffffff; border-left: 4px solid #10b981; color: #334155; font-size: 0.92rem; border-radius: 4px;">
                        {chunk_text}
                    </blockquote>
                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 6px;">
                        Source Chunk ID: <code>{q.source_chunk_id}</code>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.caption(f"Source chunk: {q.source_chunk_id}")

        # Multilingual Explanation Toggle
        st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
        tab_en, tab_ur, tab_roman = st.tabs(["English Explanation", "اردو وضاحت", "Roman Urdu"])

        with tab_en:
            st.markdown(f"<div class='explanation-box'>{q.explanation_en or 'No explanation provided.'}</div>", unsafe_allow_html=True)
        with tab_ur:
            st.markdown(
                f"<div class='explanation-box urdu-text' dir='rtl'>{q.explanation_ur or 'وضاحت دستیاب نہیں ہے۔'}</div>",
                unsafe_allow_html=True,
            )
        with tab_roman:
            st.markdown(
                f"<div class='explanation-box'>{q.explanation_ur_roman or 'Roman Urdu explanation available in attempt view.'}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Attempt Button
        st.markdown("<div style='margin-top: 16px; text-align: right;'>", unsafe_allow_html=True)
        if st.button(f"✍️ Attempt Question {idx} in Practice Mode", key=f"btn_attempt_{q.q_id}"):
            st.session_state["active_attempt_question"] = q
            st.session_state["current_view"] = "attempt"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
