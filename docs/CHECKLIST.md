# Sabaq — Running Checklist

Tick these off in order. This is the "am I on track" gut check — cross-reference `BUILD_ORDER.md` for the how.

## Pre-flight
- [ ] Python 3.11 + requirements installed
- [ ] LLM API key working (test with a single hello-world call)
- [ ] STBB Biology 9 PDF downloaded, text layer confirmed (not scanned images)

## Contracts (do this before any real logic)
- [ ] `contracts.py` written
- [ ] `fixtures/demo_fixtures.json` written by hand
- [ ] `core/mock_core.py` returns fixtures with correct signatures
- [ ] `config.py` exists with `USE_MOCK_CORE = True`

## Engine
- [ ] Chapter 4 PDF parsed into chunks, manually spot-checked for garbling
- [ ] Chapters 1 and 6 parsed (lower priority — cut first if behind)
- [ ] `chunks.jsonl` written for all chapters
- [ ] FAISS index built and loads without error
- [ ] Retrieval manually tested on 3+ queries — results make sense
- [ ] Generator produces coherent questions with valid `source_chunk_id`
- [ ] Verification pass tested on a KNOWN-BAD question — confirmed it returns False
- [ ] Verification pass tested on a KNOWN-GOOD question — confirmed it returns True
- [ ] Graceful-failure case reproduced and saved (Ch 6, off-topic question)
- [ ] Grader tested with a correct AND an incorrect student answer

## UI
- [ ] Chapter select → generate flow works on mocks
- [ ] Question cards show verified badge + citation box
- [ ] Attempt mode works on mocks (question → answer → graded result)
- [ ] Language toggle (EN / Urdu / Roman Urdu) switches displayed text

## Roman Urdu
- [ ] Few-shot prompt written with natural examples
- [ ] Output tested — read aloud, sounds natural, not robotic
- [ ] One clean before/after pair saved for the demo

## Integration
- [ ] `USE_MOCK_CORE = False` flipped
- [ ] Full flow retested with real engine
- [ ] Integration bugs fixed

## Deploy
- [ ] Deployed to Streamlit Cloud / HF Spaces
- [ ] API key in secrets, not in code
- [ ] Tested from a different device/network
- [ ] App kept "warm" before judging

## Evaluation (nice-to-have, cut if behind)
- [ ] Golden set written (20-30 lines)
- [ ] `evaluate.py` produces a real hit-rate number

## Demo prep
- [ ] Demo questions pre-generated and cached
- [ ] Backup video recorded
- [ ] 60-second script rehearsed out loud, timed, at least twice
- [ ] One live generation kept in the script to prove it's real

## Never cut, no matter how behind you are
- [ ] Verification layer is real and tested
- [ ] Graceful-failure case works and is demo-ready
