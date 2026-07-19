"""
Lab 5.3 - Demo 2: Provenance - Cite the Source Line (S6)

This module handles the Claude review passes and attaches provenance.

Key principles:
- The model returns only line numbers, NOT quote text
- Quotes are attached locally from the real report data
- Parse failures degrade gracefully to zero findings
- Out-of-range line numbers are dropped (unverifiable)

TODO: Implement the _parse_findings() function below.
"""

import os
import json
import anthropic
from sample_report import get_quote


# Model configuration
MODEL_NAME = os.environ.get("MODEL_NAME", "claude-sonnet-4-5")

# Two different prompts for independent review passes
PROMPT_STRICT = """You are a strict compliance reviewer. Review this quarterly financial report line by line.

Flag any line that contains:
- Unusual changes without disclosure
- Numbers that appear inconsistent
- Missing risk disclosures
- Vague or evasive language

For each issue, return JSON with:
- "line": line number (1-indexed)
- "flag": brief description of the issue
- "confidence": float 0.0 to 1.0 (how certain you are this is a real issue)

Return ONLY a JSON array of findings, nothing else.
Example: [{"line": 4, "flag": "unusual_change_without_disclosure", "confidence": 0.85}]

Report:
{report}"""

PROMPT_GENERAL = """You are a compliance reviewer. Review this quarterly financial report.

Look for potential compliance issues such as:
- Important disclosures that may be missing
- Financial statements that need clarification
- Risk factors not adequately explained

For each concern, return JSON with:
- "line": line number (1-indexed)
- "flag": what the concern is
- "confidence": 0.0 to 1.0 (how confident you are)

Return a JSON array of findings only.
Example: [{"line": 4, "flag": "needs_clarification", "confidence": 0.70}]

Report:
{report}"""


def _parse_json_array(text):
    """
    Parse JSON array from model output, tolerantly.

    - Strips markdown code fences (```)
    - Returns [] on parse failure (don't crash)

    Args:
        text: Raw model output

    Returns:
        List of findings, or [] if parse fails
    """
    # Strip markdown code fences
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence
        lines = text.split("\n")
        lines = lines[1:]  # Skip first line with ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Remove closing ```
        text = "\n".join(lines).strip()

    # Strip "json" language identifier if present
    if text.startswith("json"):
        text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Treat parse failure as zero findings (safe degradation)
        return []


def _parse_findings(raw_findings):
    """
    Parse raw findings from model and attach provenance.

    Key steps:
    1. Extract line number from model's JSON
    2. Attach the REAL quote via get_quote(line) - never trust the model
    3. Drop findings with out-of-range line numbers (unverifiable)
    4. Extract flag and confidence, with safe defaults

    Args:
        raw_findings: List of dicts from model (after JSON parse)

    Returns:
        List of provenance-backed findings with shape:
        {"line": int, "quote": str, "flag": str, "confidence": float}
    """

    cleaned = []

    for f in raw_findings:
        # Get line number
        line = f.get("line")
        if not line or not isinstance(line, int):
            continue  # Skip if no valid line number

        # Attach quote from OUR data, by line number
        # This is provenance - we never trust the model to copy text
        quote = get_quote(line)
        if not quote:
            # Line out of range -> drop (unverifiable)
            continue

        # Extract flag and confidence with safe defaults
        flag = str(f.get("flag", "unspecified"))
        confidence = float(f.get("confidence", 0.0))

        # Clamp confidence to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))

        cleaned.append({
            "line": line,
            "quote": quote,
            "flag": flag,
            "confidence": confidence
        })

    return cleaned


def review(report_text, mode="strict"):
    """
    Run a single review pass with Claude.

    Args:
        report_text: The numbered report text
        mode: "strict" or "general" (selects prompt)

    Returns:
        List of findings with provenance attached
    """

    # Select prompt based on mode
    if mode == "strict":
        prompt = PROMPT_STRICT.format(report=report_text)
    else:
        prompt = PROMPT_GENERAL.format(report=report_text)

    # Call Claude
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=4096,
        temperature=0.3,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Parse response
    response_text = message.content[0].text
    raw_findings = _parse_json_array(response_text)

    # Attach provenance and return
    return _parse_findings(raw_findings)
