"""
Exercise 2: Schema + Semantic Validation
Demonstrates how to validate cross-field policy that JSON Schema cannot express
"""

import os
import sys
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# EVALUATE_TOOL - same as exercise 1
EVALUATE_TOOL = {
    "name": "record_evaluation",
    "description": "Record a structured screening evaluation for one job candidate.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Candidate name."},
            "recommendation": {
                "type": "string",
                "enum": ["strong_hire", "hire", "no_hire"],
                "description": "Screening recommendation.",
            },
            "score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 10,
                "description": "Overall fit, 0 (poor) to 10 (excellent).",
            },
            "reason": {"type": "string", "description": "One-sentence justification."},
        },
        "required": ["name", "recommendation", "score", "reason"],
    },
}

RECS = {"strong_hire", "hire", "no_hire"}


def validate(payload):
    """
    Validate payload against schema rules AND cross-field policy.
    Returns (ok: bool, errors: list[str]).
    """
    errors = []

    # Defensive: accept anything, return structured verdict
    if not isinstance(payload, dict):
        return False, ["payload is not an object"]

    # Check name
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name must be a non-empty string")

    # Check recommendation
    rec = payload.get("recommendation")
    if rec not in RECS:
        errors.append(f"recommendation must be one of {sorted(RECS)}")

    # Check score (watch out for bool!)
    score = payload.get("score")
    is_int = isinstance(score, int) and not isinstance(score, bool)
    if not is_int:
        errors.append("score must be an integer")
    elif not (0 <= score <= 10):
        errors.append("score must be between 0 and 10")

    # Check reason
    reason = payload.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("reason must be a non-empty string")

    # Cross-field policy (semantic rules)
    if rec == "strong_hire" and is_int and score < 8:
        errors.append("a 'strong_hire' must score >= 8")
    if rec == "no_hire" and is_int and score > 4:
        errors.append("a 'no_hire' must score <= 4")

    return (len(errors) == 0), errors


def check():
    """Offline check: test validate() on fixtures without API calls"""
    print("\n" + "=" * 70)
    print("OFFLINE CHECK: Testing validate() on fixtures")
    print("=" * 70)

    fixtures = [
        {
            "name": "Good Record",
            "payload": {
                "name": "Alex Park",
                "recommendation": "strong_hire",
                "score": 9,
                "reason": "Excellent technical depth and leadership experience.",
            },
            "expect_valid": True,
        },
        {
            "name": "Bad Structure",
            "payload": {
                "name": "",
                "recommendation": "maybe",
                "score": 15,
                "reason": "",
            },
            "expect_valid": False,
        },
        {
            "name": "Policy Violation",
            "payload": {
                "name": "Jordan Lee",
                "recommendation": "strong_hire",
                "score": 4,
                "reason": "Decent fundamentals but lacks senior experience.",
            },
            "expect_valid": False,
        },
    ]

    all_passed = True
    for fixture in fixtures:
        name = fixture["name"]
        payload = fixture["payload"]
        expect_valid = fixture["expect_valid"]

        ok, errors = validate(payload)

        status = "PASS" if ok == expect_valid else "FAIL"
        if ok != expect_valid:
            all_passed = False

        print(f"\n[{status}] {name}")
        print(f"  Expected valid: {expect_valid}, Got: {ok}")
        if errors:
            print(f"  Errors: {errors}")

    print(f"\n{'=' * 70}")
    if all_passed:
        print("All checks passed!")
    else:
        print("Some checks failed!")
        sys.exit(1)


def evaluate_candidate(candidate_description):
    """Evaluate one candidate and validate the result"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        tools=[EVALUATE_TOOL],
        tool_choice={"type": "tool", "name": "record_evaluation"},
        messages=[
            {
                "role": "user",
                "content": f"Evaluate this candidate for a senior backend engineer role:\n\n{candidate_description}",
            }
        ],
    )

    # Extract payload
    for block in response.content:
        if block.type == "tool_use":
            payload = block.input
            ok, errors = validate(payload)
            return payload, ok, errors

    return None, False, ["No tool_use block found"]


def main():
    # Handle --check flag
    if "--check" in sys.argv:
        check()
        return

    print("\n" + "=" * 70)
    print("Exercise 2: Schema + Semantic Validation")
    print("=" * 70)
    print("\nEvaluating candidate and validating against policy rules.")

    candidate = "Alex Park: 10 years experience as a senior backend engineer. Led the re-architecture of a payment system handling $2B annually."

    print(f"\nCandidate: {candidate[:80]}...\n")

    payload, ok, errors = evaluate_candidate(candidate)

    if payload:
        print("Structured Evaluation:")
        print(json.dumps(payload, indent=2))
        print(f"\nValidation: {'valid' if ok else 'INVALID'}")
        if errors:
            print(f"Errors: {errors}")
    else:
        print(f"Error: {errors}")

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)
    print("Schema enforces shape (types, enum, range).")
    print("validate() enforces meaning (cross-field policy).")
    print("strong_hire => score >= 8; no_hire => score <= 4.\n")


if __name__ == "__main__":
    main()
