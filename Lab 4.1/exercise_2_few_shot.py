"""
Exercise 2: Few-Shot Examples to Lock Consistent Output
Demonstrates how examples fix the output format more reliably than instructions alone
"""

import os
import re
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# ZERO-SHOT - describes format but doesn't demonstrate
ZERO_SHOT_PROMPT = """Decide the moderation action (REMOVE, REVIEW, or ALLOW) and give one
short rationale. Respond in exactly this format: 'ACTION | rationale'.

Report: {report}"""

# FEW-SHOT - shows exact format with 3 labeled examples
FEW_SHOT_PROMPT = """Decide the moderation action (REMOVE, REVIEW, or ALLOW) and give one
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

# TEST CASES - 4 diverse reports
TEST_CASES = [
    "Someone posted 'this feature is garbage and you should be ashamed'.",
    "A user is spamming links to their blog in every thread.",
    "Posted: 'I will find you and make you regret this comment'.",
    "A 3000-word essay about why pineapple on pizza is acceptable.",
]

# Strict format regex
FORMAT_REGEX = re.compile(r"^(REMOVE|REVIEW|ALLOW)\s*\|\s*.+", re.IGNORECASE | re.MULTILINE)


def test_format_compliance(prompt_template, prompt_name):
    """Test format compliance with strict regex"""
    print(f"\n{'='*70}")
    print(f"Testing {prompt_name}")
    print(f"{'='*70}")

    compliant = 0
    total = len(TEST_CASES)

    for i, report in enumerate(TEST_CASES, 1):
        # Get model response
        response = client.messages.create(
            model=MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt_template.format(report=report)}]
        )

        output = response.content[0].text.strip()

        # Check format compliance
        matches_format = bool(FORMAT_REGEX.search(output))
        status = "✓" if matches_format else "✗"

        if matches_format:
            compliant += 1

        print(f"{i}. {report[:55]}...")
        print(f"   Output: {output[:65]}...")
        print(f"   Format compliant: {status}")

    compliance_rate = (compliant / total) * 100
    print(f"\n{prompt_name} Results:")
    print(f"  Format compliance: {compliant}/{total} ({compliance_rate:.0f}%)")

    return compliant, total


def main():
    print("\n" + "="*70)
    print("Exercise 2: Few-Shot Examples to Lock Consistent Output")
    print("="*70)
    print("\nComparing zero-shot instruction vs. few-shot examples.")
    print("Scoring: strict regex ^(REMOVE|REVIEW|ALLOW) \\| .+")

    # Test zero-shot
    zero_compliant, zero_total = test_format_compliance(ZERO_SHOT_PROMPT, "ZERO-SHOT")

    # Test few-shot
    few_compliant, few_total = test_format_compliance(FEW_SHOT_PROMPT, "FEW-SHOT")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Same model, same questions — only added examples.")
    print(f"\nZero-shot: {zero_compliant}/{zero_total} format compliance")
    print(f"Few-shot:  {few_compliant}/{few_total} format compliance")
    print(f"\n✓ Key takeaway: Show the format, don't just describe it.")
    print(f"  Examples lock casing, separator, and rationale length far more")
    print(f"  reliably than instructions alone.\n")


if __name__ == "__main__":
    main()
