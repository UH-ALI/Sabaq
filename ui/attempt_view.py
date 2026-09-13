"""
ui/attempt_view.py

Streamlit view for Screen 3:
- Question attempt interface (student answer input)
- Tone selection (strict vs friendly)
- Grading evaluation display:
  - Score badge (0-10)
  - Detailed rubric feedback
  - Highlighted "Textbook Point Missed" citation callout
  - Direct model answer comparison
  - Collapsible source chunk citation
"""

from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

import config
from contracts import GradeRequest, GradeResult, GeneratedQuestion
from core.mock_core import grade_answer  # Mock grading active until Phase 10


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


def render_attempt_screen():
    # Load available questions
    questions: list[GeneratedQuestion] = st.session_state.get("questions", [])
    active_q: GeneratedQuestion | None = st.session_state.get("active_attempt_question")

    # If no questions generated yet, show prompt to generate
    if not questions and not active_q:
        st.markdown(
            """
            <div style="margin-bottom: 24px;">
                <h1 style="font-size: 2.2rem; font-weight: 700; margin-bottom: 6px; color: #ffffff;">
                    Practice & Attempt Mode
                </h1>
                <p style="color: #94a3b8; font-size: 1.05rem; margin: 0;">
                    Attempt exam questions and receive instant textbook-grounded rubric feedback.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("No questions generated yet. Please generate questions first!")
        if st.button("← Go to Question Generator", type="primary"):
            st.session_state["current_view"] = "generate"
            st.rerun()
        return

    # If active question not set or not in list, default to first question
    if not active_q and questions:
        active_q = questions[0]
        st.session_state["active_attempt_question"] = active_q

    chunk_lookup = load_chunk_lookup()

    # Top Navigation Back Button - Clean layout, no overlapping divider
    if st.button("← Back to Question Generator", key="btn_back_to_gen"):
        st.session_state["current_view"] = "generate"
        st.rerun()

    st.markdown(
        """
        <div style="margin-top: 14px; margin-bottom: 20px;">
            <h1 style="font-size: 2.2rem; font-weight: 700; margin-bottom: 6px; color: #ffffff;">
                Practice & Attempt Mode
            </h1>
            <p style="color: #94a3b8; font-size: 1.02rem; margin: 0;">
                Write your response and test your recall against the official Sindh Board textbook standard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Question selector if multiple questions exist
    if len(questions) > 1:
        q_options = [f"Q{i+1}: {q.question[:70]}..." for i, q in enumerate(questions)]
        cur_idx = 0
        for i, q in enumerate(questions):
            if active_q and q.q_id == active_q.q_id:
                cur_idx = i
                break
        selected_q_label = st.selectbox(
            "Select Question to Attempt",
            options=q_options,
            index=cur_idx,
            key="active_q_selector",
        )
        selected_index = q_options.index(selected_q_label)
        active_q = questions[selected_index]
        st.session_state["active_attempt_question"] = active_q

    assert active_q is not None

    # Main Attempt Layout: Question on Left, Attempt Form on Right / Stacked
    with st.container():
        st.markdown('<div class="control-card">', unsafe_allow_html=True)

        # Header Badge and Marks
        badge_html = (
            '<span class="badge badge-verified">✅ Verified against textbook</span>'
            if active_q.verified
            else '<span class="badge badge-unverified">⚠️ Unverified / Outside text</span>'
        )

        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <div>
                    <span style="background: #0f172a; color: #38bdf8; border: 1px solid #38bdf8; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.9rem;">
                        {active_q.qtype.upper()}
                    </span>
                    <span style="color: #94a3b8; font-size: 0.9rem; margin-left: 10px; font-weight: 500;">
                        Allocated: {active_q.marks} {'mark' if active_q.marks == 1 else 'marks'}
                    </span>
                </div>
                <div>
                    {badge_html}
                </div>
            </div>
            <div style="font-size: 1.25rem; font-weight: 600; color: #ffffff; line-height: 1.5; margin-bottom: 18px;">
                {active_q.question}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # If MCQ, show choices cleanly
        if active_q.qtype == "mcq" and active_q.options:
            st.markdown(
                '<div style="font-weight: 600; color: #cbd5e1; font-size: 0.9rem; margin-bottom: 8px;">Options:</div>',
                unsafe_allow_html=True,
            )
            for opt_idx, opt in enumerate(active_q.options):
                letter = chr(65 + opt_idx)
                st.markdown(
                    f"""
                    <div class="option-row option-default" style="margin-bottom: 8px;">
                        <span class="option-letter">{letter}</span>
                        <span>{opt}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

    # Student Input Section
    with st.container():
        st.markdown('<div class="question-card" style="margin-top: 18px;">', unsafe_allow_html=True)
        st.markdown(
            """
            <h3 style="margin-top: 0; margin-bottom: 12px; font-size: 1.2rem; color: #ffffff;">
                ✍️ Your Answer
            </h3>
            """,
            unsafe_allow_html=True,
        )

        # Option selection helper for MCQs or Free text
        if active_q.qtype == "mcq" and active_q.options:
            mcq_choice = st.radio(
                "Select your option:",
                options=[f"{chr(65+i)}: {opt}" for i, opt in enumerate(active_q.options)],
                key=f"mcq_radio_{active_q.q_id}",
            )
            default_ans = mcq_choice if mcq_choice else ""
            student_answer = st.text_area(
                "Add your explanation / reasoning:",
                value=st.session_state.get(f"ans_{active_q.q_id}", default_ans),
                placeholder="Explain why this option is correct based on the textbook passage...",
                height=100,
                key=f"ans_input_{active_q.q_id}",
            )
        else:
            student_answer = st.text_area(
                "Write your complete textbook answer:",
                value=st.session_state.get(
                    f"ans_{active_q.q_id}",
                    "The cell membrane is selectively permeable and controls what enters the cell.",
                ),
                placeholder="Type your answer here in detail according to your textbook concepts...",
                height=130,
                key=f"ans_input_{active_q.q_id}",
            )

        col_tone, col_submit = st.columns([1.2, 1], gap="medium")
        with col_tone:
            tone = st.radio(
                "Grading Rubric Tone:",
                options=["strict", "friendly"],
                index=0,
                format_func=lambda x: "🎯 Strict Exam Rubric (Board Criteria)" if x == "strict" else "🤝 Friendly Mentor (Encouraging)",
                horizontal=True,
            )

        with col_submit:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            submit_btn = st.button(
                "🚀 Submit & Grade Answer",
                type="primary",
                use_container_width=True,
                key=f"submit_btn_{active_q.q_id}",
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # Grading trigger and result presentation
    grade_key = f"grade_res_{active_q.q_id}"

    if submit_btn:
        if not student_answer.strip():
            st.warning("Please enter your answer before submitting.")
        else:
            req = GradeRequest(
                question=active_q,
                student_answer=student_answer.strip(),
                tone=tone,
            )
            with st.spinner("Grading your answer against textbook rubric..."):
                res: GradeResult = grade_answer(req)
                st.session_state[grade_key] = res
                st.session_state[f"ans_{active_q.q_id}"] = student_answer.strip()
                st.toast("Evaluation complete!", icon="🎓")

    # If graded result exists, render the comprehensive score report
    if grade_key in st.session_state:
        res: GradeResult = st.session_state[grade_key]
        render_grade_report(res, active_q, chunk_lookup)


def render_grade_report(
    res: GradeResult, q: GeneratedQuestion, chunk_lookup: dict[str, dict]
):
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)

    # Determine score badge styling
    score = res.score
    if score >= 8.0:
        score_class = "score-excellent"
        score_label = "Excellent • Board Standard"
    elif score >= 5.0:
        score_class = "score-moderate"
        score_label = "Partial Credit • Key Points Missing"
    else:
        score_class = "score-low"
        score_label = "Needs Review • Concept Incomplete"

    with st.container():
        # Attempt Mode's grading uses mock until Phase 10
        mock_notice_html = (
            '<div style="background: rgba(245, 158, 11, 0.15); border: 1.5px solid rgba(251, 191, 36, 0.5); border-radius: 8px; padding: 10px 16px; margin-bottom: 18px; display: flex; align-items: center; gap: 10px; font-size: 0.88rem; color: #fde68a; font-weight: 500; line-height: 1.5;">'
            '<span style="font-size: 1.15rem;">⚠️</span>'
            '<span><b>Demo mode:</b> this feedback is a fixed sample response and doesn\'t reflect the answer you actually submitted. Real answer-specific grading activates once the live engine is connected (Phase 10).</span>'
            '</div>'
        )

        st.markdown(
            f"""<div class="result-card">
{mock_notice_html}
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 16px; margin-bottom: 20px;">
<div>
<span style="font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8;">Evaluation Result</span>
<h2 style="margin: 4px 0 0 0; font-size: 1.6rem; font-weight: 700; color: #ffffff;">Board Exam Graded Feedback</h2>
</div>
<div style="text-align: right;">
<div class="score-badge {score_class}">
{score:.1f} <span style="font-size: 1rem; font-weight: 500; opacity: 0.8;">/ 10.0</span>
</div>
<div style="font-size: 0.82rem; font-weight: 600; color: #94a3b8; margin-top: 4px;">{score_label}</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )

        # Feedback text
        st.markdown(
            f"""
            <div style="margin-bottom: 20px;">
                <div style="font-weight: 700; color: #ffffff; font-size: 1.05rem; margin-bottom: 8px;">
                    📝 Examiner's Assessment
                </div>
                <div style="color: #f1f5f9; font-size: 1rem; line-height: 1.65; background: #0f172a; padding: 14px 18px; border-radius: 8px; border: 1px solid #334155;">
                    {res.feedback}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Highlighted Missed Point Callout (The critical anti-hallucination differentiator)
        if res.missed_point:
            st.markdown(
                f"""
                <div class="missed-point-box">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; color: #fecdd3; font-size: 1rem; margin-bottom: 6px;">
                        <span>⚠️</span> Textbook Point Missed in Your Answer:
                    </div>
                    <div style="color: #ffe4e6; font-size: 0.95rem; line-height: 1.6; font-style: italic; background: #25090e; padding: 12px 14px; border-radius: 6px; border: 1px solid #fda4af;">
                        {res.missed_point}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Model Answer & Grounding Comparison
        with st.expander("🔍 Compare with Official Textbook Model Answer"):
            st.markdown(
                f"""
                <div style="background: #0f172a; border-left: 4px solid #38bdf8; padding: 12px 16px; border-radius: 6px; margin-bottom: 12px;">
                    <div style="font-weight: 700; color: #38bdf8; font-size: 0.9rem; margin-bottom: 4px;">Official Model Answer:</div>
                    <div style="color: #f1f5f9; font-size: 0.95rem; line-height: 1.5;">{q.model_answer}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Source Chunk
            src_chunk = chunk_lookup.get(res.source_chunk_id or q.source_chunk_id)
            if src_chunk:
                st.markdown(
                    f"""
                    <div style="margin-top: 10px;">
                        <div style="font-weight: 600; color: #34d399; font-size: 0.88rem; margin-bottom: 4px;">
                            📖 Grounded Textbook Passage ({src_chunk.get('section_heading', '')} • Page {src_chunk.get('page_hint', '')}):
                        </div>
                        <blockquote style="margin: 0; padding: 10px 14px; background: #0f172a; border-left: 4px solid #10b981; color: #a7f3d0; font-size: 0.9rem; border-radius: 4px;">
                            {src_chunk.get('text', '')}
                        </blockquote>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Explanation Language Toggle in Result View
        st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-weight: 600; color: #cbd5e1; font-size: 0.9rem; margin-bottom: 6px;'>Detailed Topic Explanations:</div>", unsafe_allow_html=True)
        tab_en, tab_ur, tab_roman = st.tabs(["English", "اردو وضاحت", "Roman Urdu"])

        with tab_en:
            st.markdown(f"<div class='explanation-box'>{q.explanation_en or 'No explanation available.'}</div>", unsafe_allow_html=True)
        with tab_ur:
            st.markdown(
                f"<div class='explanation-box urdu-text' dir='rtl'>{q.explanation_ur or 'کوئی وضاحت دستیاب نہیں ہے۔'}</div>",
                unsafe_allow_html=True,
            )
        with tab_roman:
            st.markdown(
                f"<div class='explanation-box'>{q.explanation_ur_roman or 'Roman Urdu explanation available.'}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
