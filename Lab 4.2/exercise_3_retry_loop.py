"""
Exercise 3: Retry-and-Feedback Loop that Self-Corrects
Demonstrates how to feed validation errors back to the model for self-correction
"""

import os
import sys
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# EVALUATE_TOOL - same as exercises 1 & 2
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
    """Validate payload - same as exercise 2"""
    errors = []

    if not isinstance(payload, dict):
        return False, ["payload is not an object"]

    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name must be a non-empty string")

    rec = payload.get("recommendation")
    if rec not in RECS:
        errors.append(f"recommendation must be one of {sorted(RECS)}")

    score = payload.get("score")
    is_int = isinstance(score, int) and not isinstance(score, bool)
    if not is_int:
        errors.append("score must be an integer")
    elif not (0 <= score <= 10):
        errors.append("score must be between 0 and 10")

    reason = payload.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("reason must be a non-empty string")

    # Cross-field policy
    if rec == "strong_hire" and is_int and score < 8:
        errors.append("a 'strong_hire' must score >= 8")
    if rec == "no_hire" and is_int and score > 4:
        errors.append("a 'no_hire' must score <= 4")

    return (len(errors) == 0), errors


def assess_with_retry(candidate_description, max_attempts=3):
    """
    Evaluate candidate with retry loop.
    On validation failure, feed error back as tool_result with is_error=True.
    Returns (payload, errors) - errors is empty list if valid.
    """
    messages = [
        {
            "role": "user",
            "content": f"Evaluate this candidate for a senior backend engineer role:\n\n{candidate_description}",
        }
    ]

    last_payload = None

    for attempt in range(1, max_attempts + 1):
        # Call API
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            tools=[EVALUATE_TOOL],
            tool_choice={"type": "tool", "name": "record_evaluation"},
            messages=messages,
        )

        # Extract tool_use block
        tool_use = None
        for block in response.content:
            if block.type == "tool_use":
                tool_use = block
                break

        if not tool_use:
            return None, ["No tool_use block found"]

        last_payload = tool_use.input

        # Validate
        ok, errors = validate(last_payload)

        print(f"  attempt {attempt}: {'valid' if ok else 'invalid'}", end="")
        if errors:
            print(f" -> {errors}")
        else:
            print()

        if ok:
            return last_payload, []

        # Feed error back as tool_result
        error_message = (
            "Validation failed: "
            + "; ".join(errors)
            + ". Call record_evaluation again with corrected values."
        )

        messages.append({"role": "assistant", "content": response.content})
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "is_error": True,
                        "content": error_message,
                    }
                ],
            }
        )

    # Cap reached
    return last_payload, errors


def demo_retry_loop():
    """Offline demo: simulate retry loop without API calls"""
    print("\n" + "=" * 70)
    print("OFFLINE DEMO: Simulating retry loop")
    print("=" * 70)

    candidate = "Alex Park: 10 years experience, led major re-architecture."

    print(f"\nCandidate: {candidate}")
    print("\nSimulated attempts:")

    # Attempt 1: policy violation
    print("\n  Attempt 1:")
    payload1 = {
        "name": "Alex Park",
        "recommendation": "strong_hire",
        "score": 5,
        "reason": "Good experience but score doesn't match.",
    }
    ok1, errors1 = validate(payload1)
    print(f"    Payload: {json.dumps(payload1)}")
    print(f"    Valid: {ok1}")
    if errors1:
        print(f"    Errors: {errors1}")
        print(
            f"\n  Would feed back: 'Validation failed: {'; '.join(errors1)}. Call record_evaluation again...'"
        )

    # Attempt 2: corrected
    print("\n  Attempt 2:")
    payload2 = {
        "name": "Alex Park",
        "recommendation": "strong_hire",
        "score": 9,
        "reason": "Excellent technical depth and leadership.",
    }
    ok2, errors2 = validate(payload2)
    print(f"    Payload: {json.dumps(payload2)}")
    print(f"    Valid: {ok2}")
    print("\n  Loop stops - validation passed!")

    print(f"\n{'=' * 70}")
    print("The model sees its tool_use followed by the failure,")
    print("then corrects on the next attempt. max_attempts caps the loop.\n")


def main():
    # Handle --demo flag
    if "--demo" in sys.argv:
        demo_retry_loop()
        return

    print("\n" + "=" * 70)
    print("Exercise 3: Retry-and-Feedback Loop")
    print("=" * 70)

    candidate = "Alex Park: 10 years experience as a senior backend engineer. Led the re-architecture of a payment system handling $2B annually. Strong Python and distributed systems expertise."

    print(f"\nCandidate: {candidate[:80]}...\n")
    print("Running assess_with_retry (max 3 attempts):\n")

    payload, errors = assess_with_retry(candidate, max_attempts=3)

    print(f"\n{'=' * 70}")
    print("FINAL RESULT")
    print("=" * 70)

    if payload:
        print("\nPayload:")
        print(json.dumps(payload, indent=2))
        print(f"\nErrors: {errors if errors else 'None'}")
    else:
        print(f"\nFailed after 3 attempts. Errors: {errors}")

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)
    print("On validation failure, tool_result with is_error=True")
    print("feeds the specific error back. Model self-corrects.")
    print("max_attempts cap guarantees termination.\n")


if __name__ == "__main__":
    main()
