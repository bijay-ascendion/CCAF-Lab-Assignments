# Lab 3.3 — From Refinement to Pipeline (NorthPeak Refunds Service)

Starter project for **Lab 3.3: Iterative Workflows & CI/CD Integration**.
The repo ships green; the exercises extend it.

## What's in here

    src/northpeak/refunds.py            refund logic (refined with the TDD loop in Ex 1)
    src/tests/test_refunds.py           pytest suite (6 tests; grows to 8 in Ex 1)
    CLAUDE.md                           TDD working style + "never weaken a test" rule
    .claude/commands/pr-review.md       /pr-review -> strict {decision, issues} JSON
    .github/workflows/claude-review.yml headless `claude -p` review as a PR gate
    scripts/review_gate.py              JSON verdict -> exit 0 (pass) / 1 (fail)
    samples/sample_review*.json         approve / request_changes examples for the gate

## Setup (do this before the session)

1. Get this bundle onto your Blue Labs VM and open it in VS Code.
2. Create a virtual environment and install the test dependency:

       python -m venv .venv && source .venv/bin/activate
       # Windows: .venv\Scripts\activate
       pip install -r requirements.txt

3. Confirm the suite is green and the gate works on the samples (no API calls):

       pytest -q                                                  # expect: 6 passed
       python scripts/review_gate.py samples/sample_review.json        # PASS (exit 0)
       python scripts/review_gate.py samples/sample_review_fail.json   # FAIL (exit 1)

## Notes

- Exercises 1 and 3 need no network. Only the live headless review (Exercise 2)
  calls the API: set `ANTHROPIC_API_KEY` and have Claude Code installed, or push
  to GitHub and add it as an Actions secret.
- For the interactive steps (Exercises 1 and 3) run `claude` and sign in when
  prompted.
- This project is already a git repository with a committed baseline, so
  `/pr-review`'s `git diff` sees your changes.
