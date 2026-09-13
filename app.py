"""
app.py

Main entry point for the Sabaq Streamlit web application.
Coordinates the 3-screen matric exam preparation flow:
1. Chapter Selection & Parameter Configuration
2. Verified Question Generation (with citation & multi-lingual explanations)
3. Practice Attempt & AI Rubric Grading (with missed textbook point callout)
"""

from __future__ import annotations

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import config
from ui.generate_view import render_generate_screen
from ui.attempt_view import render_attempt_screen

# Set page configuration
st.set_page_config(
    page_title="Sabaq • سبق — AI Matric Exam Prep",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Design System CSS (Crisp High-Contrast Dark Theme)
CUSTOM_CSS = """
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap');

html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #0b0f19 !important;
    color: #f1f5f9 !important;
}

/* App Background & Padding */
.main .block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 1200px;
    background-color: #0b0f19 !important;
}

/* Headings Crisp Contrast */
h1, h2, h3, h4, .main-title {
    color: #ffffff !important;
    font-weight: 700;
}

/* General Button Styling for Crisp Readability */
div.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: #ffffff !important;
    background-color: #1e293b !important;
    border: 1px solid #475569 !important;
}

div.stButton > button:hover {
    background-color: #334155 !important;
    border-color: #64748b !important;
    color: #ffffff !important;
}

div.stButton > button[kind="primary"], div.stButton > button[data-testid="baseButton-primary"] {
    background: #059669 !important;
    border: 1px solid #10b981 !important;
    color: #ffffff !important;
}

/* Sidebar Radio Labels Crisp White */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #f1f5f9 !important;
}

/* Top Navbar Branding */
.brand-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    padding: 22px 28px;
    border-radius: 14px;
    border: 1px solid #334155;
    color: #ffffff;
    margin-bottom: 20px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.35);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.brand-title {
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-badge {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.4);
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Card Containers */
.control-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 24px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    margin-bottom: 24px;
    color: #f1f5f9;
}

.question-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    color: #f1f5f9;
}

/* Badges */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    padding: 5px 14px;
    border-radius: 9999px;
}

.badge-verified {
    background-color: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.4);
}

.badge-unverified {
    background-color: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.4);
}

/* MCQ Option Rows */
.option-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 10px;
    margin-bottom: 8px;
    font-size: 1rem;
    line-height: 1.4;
}

.option-default {
    background: #0f172a;
    border: 1px solid #334155;
    color: #f1f5f9;
}

.option-correct {
    background: rgba(16, 185, 129, 0.15);
    border: 1.5px solid #10b981;
    color: #ecfdf5;
    font-weight: 600;
}

.option-letter {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: #1e293b;
    border: 1px solid #475569;
    font-weight: 700;
    font-size: 0.88rem;
    color: #e2e8f0;
}

.option-correct .option-letter {
    background: #10b981;
    color: #ffffff;
    border-color: #059669;
}

/* Graded Result Card */
.result-card {
    background: #1e293b;
    border: 1.5px solid #475569;
    border-radius: 16px;
    padding: 28px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    color: #f1f5f9;
}

.score-badge {
    display: inline-block;
    padding: 8px 18px;
    border-radius: 12px;
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
}

.score-excellent {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.5);
}

.score-moderate {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.5);
}

.score-low {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.5);
}

/* Missed Point Callout */
.missed-point-box {
    background: #3c1117;
    border: 1.5px solid #f43f5e;
    border-left: 6px solid #e11d48;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 20px;
}

/* Multilingual & RTL Styling */
.urdu-text {
    font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', serif;
    font-size: 1.25rem;
    line-height: 2.2;
    direction: rtl;
    text-align: right;
    color: #ffffff !important;
}

.explanation-box {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 0.98rem;
    line-height: 1.6;
    color: #e2e8f0;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
}

/* Custom Button Styling */
div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Session State Defaults
if "current_view" not in st.session_state:
    st.session_state["current_view"] = "generate"
if "questions" not in st.session_state:
    st.session_state["questions"] = []
if "active_attempt_question" not in st.session_state:
    st.session_state["active_attempt_question"] = None

# Top Branding Banner
st.markdown(
    """
    <div class="brand-header">
        <div>
            <div class="brand-title">
                📖 Sabaq <span style="font-family: 'Noto Nastaliq Urdu', serif; font-size: 1.4rem; font-weight: normal; margin-left: 4px;">سبق</span>
                <span class="brand-badge">Sindh Board Bio 9</span>
            </div>
            <div style="font-size: 0.92rem; color: #cbd5e1; margin-top: 4px;">
                Verified Matric Exam Prep Engine • Strictly Grounded in Textbooks • Anti-Hallucination Verified
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8;">Coverage</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #38bdf8;">Chapters 1, 4 & 6</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Prominent Labeled Top Navigation Bar
col_nav1, col_nav2, col_spacer = st.columns([1.5, 1.5, 3])
with col_nav1:
    gen_selected = st.session_state["current_view"] == "generate"
    if st.button(
        "⚡ Generate Questions",
        type="primary" if gen_selected else "secondary",
        use_container_width=True,
        key="top_nav_gen",
    ):
        st.session_state["current_view"] = "generate"
        st.rerun()

with col_nav2:
    att_selected = st.session_state["current_view"] == "attempt"
    if st.button(
        "✍️ Attempt Mode",
        type="primary" if att_selected else "secondary",
        use_container_width=True,
        key="top_nav_att",
    ):
        st.session_state["current_view"] = "attempt"
        st.rerun()

st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

# Sidebar: Navigation, In-Scope Syllabus, and Simplified Plain-English Status
with st.sidebar:
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h3 style="margin: 0 0 6px 0; font-size: 1.15rem; font-weight: 700; color: #ffffff;">Navigation</h3>
            <p style="margin: 0; color: #94a3b8; font-size: 0.85rem;">Switch between generator and attempt mode</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sidebar_selection = st.radio(
        "Navigation:",
        options=["⚡ Generate Questions", "✍️ Attempt Mode"],
        index=0 if st.session_state["current_view"] == "generate" else 1,
        key="sidebar_nav_radio",
        label_visibility="collapsed",
    )

    if sidebar_selection == "⚡ Generate Questions" and st.session_state["current_view"] != "generate":
        st.session_state["current_view"] = "generate"
        st.rerun()
    elif sidebar_selection == "✍️ Attempt Mode" and st.session_state["current_view"] != "attempt":
        st.session_state["current_view"] = "attempt"
        st.rerun()

    st.markdown("---")

    # Textbook Chapters & Coverage
    st.markdown(
        """
        <div style="margin-bottom: 12px;">
            <h4 style="margin: 0 0 4px 0; font-size: 0.95rem; font-weight: 700; color: #ffffff;">📘 In-Scope Syllabus</h4>
            <div style="font-size: 0.82rem; color: #94a3b8;">Sindh Textbook Board, Class 9 Biology</div>
        </div>
        <div style="font-size: 0.85rem; line-height: 1.7; color: #cbd5e1;">
            <div>• <b>Ch 4:</b> Cells and Tissues (65 sections)</div>
            <div>• <b>Ch 1:</b> Intro to Biology (50 sections)</div>
            <div>• <b>Ch 6:</b> Enzymes (17 sections)</div>
        </div>
        <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 10px; line-height: 1.5;">
            Custom document/chapter upload is planned for a future version — currently limited to the chapters above.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Engine Status Info - Plain Language (User-Facing)
    status_text = (
        "Running in demo mode with sample questions"
        if config.USE_MOCK_CORE
        else "Connected to live generation engine"
    )
    st.markdown(
        f"""
        <div style="margin-bottom: 14px;">
            <h4 style="margin: 0 0 6px 0; font-size: 0.95rem; font-weight: 700; color: #ffffff;">⚙️ System Status</h4>
            <div style="font-size: 0.85rem; font-weight: 600; color: #38bdf8;">• {status_text}</div>
            <div style="font-size: 0.82rem; color: #94a3b8; margin-top: 8px; line-height: 1.5;">
                Anti-hallucination guard verified: queries outside textbook scope (such as the Krebs cycle) are cleanly separated and refused.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Demo Mode Transparency Banner
if config.USE_MOCK_CORE:
    st.markdown(
        """
        <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(251, 191, 36, 0.4); border-radius: 8px; padding: 10px 16px; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; font-size: 0.9rem; color: #fde68a; font-weight: 500;">
            <span style="font-size: 1.1rem;">⚠️</span>
            <span><b>Demo mode:</b> showing sample data (offline mock core). Real generation and grading will activate once integrated.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Screen Router
if st.session_state["current_view"] == "generate":
    render_generate_screen()
elif st.session_state["current_view"] == "attempt":
    render_attempt_screen()

# Scope Disclaimer Note
st.markdown(
    """
    <div style="font-size: 0.82rem; color: #94a3b8; margin-top: 40px; text-align: center; border-top: 1px solid #334155; padding-top: 16px;">
        Currently supports Sindh Textbook Board Biology 9 (Chapters 1, 4, 6). Custom textbook upload is planned for a future version.
    </div>
    """,
    unsafe_allow_html=True,
)
