---
description: Review changes and output a structured JSON verdict for automation
allowed-tools: Bash(git diff:*), Bash(git status:*), Read, Grep
---

Review the current changes (run `git diff`) for the NorthPeak refunds service.

Judge correctness, missing tests, and input validation. Then output **only** a
single JSON object - no prose, no Markdown fences - in exactly this shape:

{
  "decision": "approve" | "request_changes",
  "issues": [
    { "severity": "blocker" | "warning" | "nit", "message": "<one sentence>" }
  ]
}

Rules:
- Use "request_changes" if there is any blocker (a real bug, a behaviour change
  with no test, or unvalidated input). Otherwise use "approve".
- Keep each message to one sentence. If there are no issues, return an empty list.
- Output nothing except the JSON object.