"""
Exercise 1: Explicit Criteria to Cut False Positives
Demonstrates how explicit, testable criteria reduce wrongful "remove" calls
"""

import os
import re
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# VAGUE PROMPT - leaves "remove" undefined, tends to over-fire
VAGUE_PROMPT = """Decide the moderation action for this reported post:
remove, review, or allow.

Report: {report}

Answer with one word only."""

# EXPLICIT PROMPT - testable definitions with tie-break rule
EXPLICIT_PROMPT = """Decide the moderation action for this reported post.
Choose the action using these exact definitions:

- remove: a clear, unambiguous violation - doxxing or exposure of private
  personal data, a credible threat against a specific person, or clearly
  illegal content. Reserve this for cases with no reasonable doubt.

- review: may violate policy but needs a human - likely spam, borderline
  harassment, ambiguous threats said in jest, heated arguments.

- allow: rude, blunt, off-topic, or unpopular but not a violation.

If unsure between remove and review, choose review - do not remove unless
the violation is unambiguous.

Report: {report}

Answer with one word only: remove, review, or allow."""

# TEST CASES - 8 labeled reports with ground truth
TEST_CASES = [
    {"report": "A user posted another member's home address and phone number.", "expected": "remove"},
    {"report": "Someone said 'your opinion is stupid and lazy'.", "expected": "allow"},
    {"report": "Multiple identical posts promoting a cryptocurrency scheme.", "expected": "review"},
    {"report": "A credible threat: 'I know where you live and I'm coming for you'.", "expected": "remove"},
    {"report": "Two users calling each other names in an escalating argument.", "expected": "review"},
    {"report": "A strongly worded but legitimate criticism of a public figure.", "expected": "allow"},
    {"report": "Someone jokingly said 'I'll destroy you' about a video game match.", "expected": "review"},
    {"report": "A post containing illegal content involving minors.", "expected": "remove"},
]


def test_prompt(prompt_template, prompt_name):
    """Test a prompt against all cases and score accuracy + false removes"""
    print(f"\n{'='*70}")
    print(f"Testing {prompt_name}")
    print(f"{'='*70}")

    correct = 0
    false_removes = 0
    total = len(TEST_CASES)

    for i, case in enumerate(TEST_CASES, 1):
        report = case["report"]
        expected = case["expected"]

        # Get model response
        response = client.messages.create(
            model=MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt_template.format(report=report)}]
        )

        # Extract the decision (one word)
        decision_text = response.content[0].text.strip().lower()
        decision = None

        # Parse the decision (handle various formats)
        if "remove" in decision_text:
            decision = "remove"
        elif "review" in decision_text:
            decision = "review"
        elif "allow" in decision_text:
            decision = "allow"

        # Score
        match = "✓" if decision == expected else "✗"
        if decision == expected:
            correct += 1

        # Track false removes (wrongful takedowns)
        if decision == "remove" and expected != "remove":
            false_removes += 1

        print(f"{i}. {report[:60]}...")
        print(f"   Expected: {expected:7} | Got: {decision:7} | {match}")

    accuracy = (correct / total) * 100
    print(f"\n{prompt_name} Results:")
    print(f"  Accuracy: {correct}/{total} ({accuracy:.0f}%)")
    print(f"  Wrongful 'remove' calls: {false_removes}")

    return correct, total, false_removes


def main():
    print("\n" + "="*70)
    print("Exercise 1: Explicit Criteria to Cut False Positives")
    print("="*70)
    print("\nComparing vague vs. explicit criteria on 8 moderation reports.")
    print("Key metric: Wrongful 'remove' calls (false positives)")

    # Test vague prompt
    vague_correct, vague_total, vague_false_removes = test_prompt(VAGUE_PROMPT, "VAGUE PROMPT")

    # Test explicit prompt
    explicit_correct, explicit_total, explicit_false_removes = test_prompt(EXPLICIT_PROMPT, "EXPLICIT PROMPT")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Same model, same questions — only the criteria changed.")
    print(f"\nVague prompt:    {vague_correct}/{vague_total} accuracy, {vague_false_removes} wrongful removes")
    print(f"Explicit prompt: {explicit_correct}/{explicit_total} accuracy, {explicit_false_removes} wrongful removes")
    print(f"\n✓ Key takeaway: Explicit, testable criteria reduce false positives.")
    print(f"  The tie-break rule ('if unsure, choose review') prevents wrongful")
    print(f"  takedowns by routing ambiguous cases to human review.\n")


if __name__ == "__main__":
    main()
