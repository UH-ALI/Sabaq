# 📚 Sabaq

*AI-generated, syllabus-grounded practice for the Sindh Textbook Board.*

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sabaq-prep.streamlit.app/)

## 🚀 Why Sabaq?

Most AI educational tools fail in Pakistani classrooms for two critical reasons:
1. **Hallucination & Syllabus Mismatch:** They invent facts or test concepts outside the student's actual syllabus, leading to confusion and wasted study time.
2. **Language Barrier:** They default to formal Urdu script or awkward English, rather than the natural **Roman Urdu** that students actually use to communicate.

**Sabaq fixes this.** It is an AI practice generator explicitly locked to the **Sindh Textbook Board (Class 9, Biology)**. Every single question it generates is backed by a real passage from the textbook, verified before it's shown, and can provide explanations in natural Roman Urdu. 

It doesn't just guess; it knows exactly what the student is supposed to learn.

## ✨ Core Features

- **Strictly Grounded Generation**: Questions (MCQs and Short Answers) are generated strictly from FAISS-indexed textbook chunks. It never relies on the LLM's general knowledge.
- **Independent Verification Pass**: A separate AI verification step confirms the generated question and answer are actually supported by the source text before showing it to the student. If it's not in the book, it doesn't get asked.
- **Attempt Mode with Rubric Grading**: Students can type answers and receive a 0-10 score, along with specific feedback pointing out exactly what detail they missed from the textbook.
- **Graceful Failure**: If queried about a topic outside the chapter's scope, it refuses to generate questions rather than hallucinating an answer.
- **Multilingual Support**: Explanations and feedback are available in English, formal Urdu script, and colloquial Roman Urdu.

## 🏗️ High-Level Architecture

Sabaq is built for speed, stability, and verifiable accuracy:

1. **Ingestion & Embedding**: Textbook PDFs are extracted, semantically chunked, and embedded using `intfloat/multilingual-e5-base`.
2. **Retrieval (RAG)**: A local FAISS vector store retrieves the most relevant textbook passages based on the student's selected chapter and topic.
3. **Generation**: **Gemini 2.5 Flash** generates questions based *only* on the retrieved context. (Includes an automatic fallback to `gemini-2.5-flash-lite` for rate-limit resilience).
4. **Verification & Grading**: Secondary LLM passes grade both the generated questions (to prevent hallucinations) and the student's attempts (for accurate feedback).
5. **Frontend**: A clean, responsive Streamlit UI providing the Select, Generate, and Attempt flows.

## 💻 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- A Google Gemini API Key

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sabaq.git
   cd sabaq
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables**
   Create a `.env` file in the root directory (you can copy `.env.example` if available):
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

5. **Run the Application**
   ```bash
   streamlit run app.py
   ```
   The app will open in your browser at `http://localhost:8501`.

## 📖 Documentation & Design Decisions

For a deep dive into the design decisions, API contracts, and hackathon build history, check out the [`docs/`](./docs/) folder:
- **[Product Requirements (PRD)](./docs/PRD.md)**: What we built, what we cut, and why.
- **[API Contracts](./docs/API_CONTRACTS.md)**: The data shapes and schemas that power the core engine.
- **[Build Order](./docs/BUILD_ORDER.md)**: A phase-by-phase history of the project's construction.

---
*Built for the students of Sindh. Note: This project is an independent educational tool and is not officially affiliated with the Sindh Textbook Board.*
