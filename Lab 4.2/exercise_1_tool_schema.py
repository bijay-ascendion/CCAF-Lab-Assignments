"""
Exercise 1: Force Structured Output with tool_use + JSON Schema
Demonstrates how tool schemas guarantee structured output
"""

import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# EVALUATE_TOOL - defines the structured output shape
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

# TEST CANDIDATES - 3 diverse profiles
CANDIDATES = [
    "Alex Park: 10 years experience as a senior backend engineer. Led the re-architecture of a payment system handling $2B annually. Strong Python and distributed systems expertise.",
    "Jordan Lee: 3 years as a full-stack developer. Solid fundamentals in React and Node.js. Completed multiple features end-to-end but hasn't led major projects.",
    "Sam Taylor: Recent bootcamp graduate with a background in sales. No prior professional software development experience. Enthusiastic but lacks technical depth.",
]


def evaluate_candidate(candidate_description):
    """Evaluate one candidate and return structured payload"""
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

    # Extract the structured payload from tool_use block
    for block in response.content:
        if block.type == "tool_use":
            return block.input  # This IS the structured object

    return None


def main():
    print("\n" + "=" * 70)
    print("Exercise 1: Force Structured Output with tool_use + JSON Schema")
    print("=" * 70)
    print("\nEvaluating 3 candidates for a senior backend engineer role.")
    print("Each evaluation returns a guaranteed structured payload.\n")

    for i, candidate in enumerate(CANDIDATES, 1):
        print(f"\n{'=' * 70}")
        print(f"Candidate {i}")
        print("=" * 70)
        print(f"Description: {candidate[:80]}...")

        payload = evaluate_candidate(candidate)

        if payload:
            print(f"\nStructured Evaluation:")
            print(json.dumps(payload, indent=2))
        else:
            print("\nError: No tool_use block found")

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)
    print("Every response is a dict with exactly 4 fields.")
    print("No prose, no markdown fences, no missing keys.")
    print("The tool's input_schema IS the contract.\n")


if __name__ == "__main__":
    main()
