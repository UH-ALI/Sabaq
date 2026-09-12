# Sabaq — Planning Docs

This folder holds the planning documents for Sabaq, written before the build started. They're kept here (not deleted after the hackathon) so anyone reading this repo — teammates, judges, or future contributors — can see the actual scope, contracts, and reasoning behind what was built, not just the code itself.

**Read them in this order:**

1. **[PRD.md](./PRD.md)** — what Sabaq is, the exact MVP scope (chapters, features in/out), and how we defined "done." Start here if you want to know *what* we set out to build and *why* certain things (other boards, OCR upload, SLO claims) were deliberately left out.
2. **[API_CONTRACTS.md](./API_CONTRACTS.md)** — every data shape and function signature used in the codebase (`Chunk`, `GeneratedQuestion`, `GradeResult`, etc.), plus file formats for `chunks.jsonl`, the FAISS index, and the evaluation golden set. If you're extending the code, this is the source of truth for shapes — check here before adding a new field anywhere.
3. **[BUILD_ORDER.md](./BUILD_ORDER.md)** — the phase-by-phase order the project was actually built in, from setup through demo prep, plus what got cut if time ran short. Useful as a map of the codebase's history and as a template for extending it (e.g., adding a new chapter or board follows roughly the same phases).
4. **[CHECKLIST.md](./CHECKLIST.md)** — a flat progress checklist mirroring the build order.

## Status

These documents reflect the plan going into the hackathon. If the shipped project diverged from any of this (scope cuts, changed decisions), that's expected and normal — check the main [README](../README.md) for what was actually delivered, and treat this folder as the historical plan and design record.

## Key decisions worth knowing before reading the code

- **Scope is locked to one board, one subject, one class**: Sindh Textbook Board, Biology, Class 9, three chapters. This was deliberate, not a shortcut — see PRD §2-4 for the reasoning.
- **Every generated question is independently verified** against its source textbook passage before being shown. This is the project's main technical claim — see API_CONTRACTS.md §5 for the non-negotiable contract around it.
- **We do not claim SLO (Student Learning Outcome) alignment** — no official SLO documents were sourced for this subject, so the claim is scoped down to "aligned with the textbook and board exercise style." See PRD §4.
- **Roman Urdu is applied to explanations only**, never to question generation or grounding — see PRD §6 and API_CONTRACTS.md §3 (`render_roman_urdu`).
