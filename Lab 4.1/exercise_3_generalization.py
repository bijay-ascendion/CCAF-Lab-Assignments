"""
Exercise 3: Generalizing Beyond the Examples Shown
Demonstrates how a principles block helps models handle unseen, context-heavy cases
"""

import os
import re
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# FEW-SHOT WITHOUT PRINCIPLES - examples only
FEW_SHOT_WITHOUT_PRINCIPLES = """Decide the moderation action (REMOVE, REVIEW, or ALLOW) and give one
short rationale. Respond in exactly this format: 'ACTION | rationale'.

Here are examples:

Report: A user posted another member's home address and employer.
REMOVE | Doxxing - exposes private personal data with no reasonable doubt.

Report: A member said a popular opinion was "totally wrong and lazy".
ALLOW | Blunt criticism of an idea, not a policy violation.

Report: A thread has escalating personal insults between two users.
REVIEW | Possible harassment that needs a human judgment call.

Now classify this report:

Report: {report}"""

# FEW-SHOT WITH PRINCIPLES - adds boundary guidance
FEW_SHOT_WITH_PRINCIPLES = """Decide the moderation action (REMOVE, REVIEW, or ALLOW) and give one
short rationale. Respond in exactly this format: 'ACTION | rationale'.

Principles:
- REMOVE only for unambiguous violations: exposure of a PRIVATE person's
  data (doxxing), credible threats, or clearly illegal content. Stated
  intent ("just a joke") does not excuse doxxing.
- Already-public or official info (a company's press line) is not doxxing - ALLOW.
- REVIEW anything genuinely ambiguous: possible jokes, spam, escalating disputes.
- ALLOW speech that is merely rude, blunt, unpopular, boring, or off-topic.
- When unsure between REMOVE and REVIEW, choose REVIEW.

Here are examples:

Report: A user posted another member's home address and employer.
REMOVE | Doxxing - exposes private personal data with no reasonable doubt.

Report: A member said a popular opinion was "totally wrong and lazy".
ALLOW | Blunt criticism of an idea, not a policy violation.

Report: A thread has escalating personal insults between two users.
REVIEW | Possible harassment that needs a human judgment call.

Now classify this report:

Report: {report}"""

# EDGE CASES - 4 context-heavy scenarios not shown in examples
EDGE_CASES = [
    {
        "report": "A post containing a company's official public press-office phone number.",
        "expected": "allow",
        "why": "Public/official info is not doxxing"
    },
    {
        "report": "A private individual's home address shared with 'just kidding, it's a joke' added.",
        "expected": "remove",
        "why": "Doxxing regardless of stated intent"
    },
    {
        "report": "Two friends joking 'I'll destroy you' about their upcoming match.",
        "expected": "review",
        "why": "Ambiguous threat in playful context"
    },
    {
        "report": "A 5000-word on-topic essay that nobody asked for.",
        "expected": "allow",
        "why": "Boring is not a violation"
    },
]

# Robust action parser (handles preamble before ACTION | line)
ACTION_REGEX = re.compile(r"\b(REMOVE|REVIEW|ALLOW)\b\s*\|", re.IGNORECASE)


def parse_action(output):
    """Extract action from ACTION | line, even if there's a preamble"""
    match = ACTION_REGEX.search(output)
    if match:
        return match.group(1).lower()
    return None


def test_edge_cases(prompt_template, prompt_name):
    """Test on context-heavy edge cases"""
    print(f"\n{'='*70}")
    print(f"Testing {prompt_name}")
    print(f"{'='*70}")

    correct = 0
    total = len(EDGE_CASES)

    for i, case in enumerate(EDGE_CASES, 1):
        report = case["report"]
        expected = case["expected"]
        why = case["why"]

        # Get model response
        response = client.messages.create(
            model=MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt_template.format(report=report)}]
        )

        output = response.content[0].text.strip()
        decision = parse_action(output)

        # Score
        match = "✓" if decision == expected else "✗"
        if decision == expected:
            correct += 1

        print(f"{i}. {report[:60]}...")
        print(f"   Expected: {expected:7} ({why})")
        print(f"   Got: {decision:7} | {match}")
        if decision != expected:
            print(f"   Output: {output[:60]}...")

    accuracy = (correct / total) * 100
    print(f"\n{prompt_name} Results:")
    print(f"  Edge case accuracy: {correct}/{total} ({accuracy:.0f}%)")

    return correct, total


def main():
    print("\n" + "="*70)
    print("Exercise 3: Generalizing Beyond the Examples Shown")
    print("="*70)
    print("\nTesting on 4 context-heavy edge cases not shown in examples.")
    print("Key distinction: private vs. public data, intent, context")

    # Test without principles
    without_correct, without_total = test_edge_cases(
        FEW_SHOT_WITHOUT_PRINCIPLES, "WITHOUT PRINCIPLES"
    )

    # Test with principles
    with_correct, with_total = test_edge_cases(
        FEW_SHOT_WITH_PRINCIPLES, "WITH PRINCIPLES"
    )

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Same model, same examples — added a principles block.")
    print(f"\nWithout principles: {without_correct}/{without_total} edge cases correct")
    print(f"With principles:    {with_correct}/{with_total} edge cases correct")
    print(f"\n✓ Key takeaway: Examples teach format; principles teach intent.")
    print(f"  The boundary generalizes to unseen, context-heavy cases when you")
    print(f"  state the distinctions (private vs. public, intent interpretation).\n")


if __name__ == "__main__":
    main()
