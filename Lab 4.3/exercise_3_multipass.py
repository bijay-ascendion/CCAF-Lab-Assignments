"""
Exercise 3: Multi-Pass Review for Higher Quality
Demonstrates draft -> critique -> refine pattern
"""

import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Briefing quality standards
STANDARDS = (
    "Briefing standards: lead with the single most important development; balance "
    "positive and negative coverage fairly; be specific (numbers, who/what); stay "
    "neutral in tone; no speculation beyond the headlines; keep it under 120 words."
)

# Morning headlines to summarize
HEADLINES = [
    "Helix Robotics announces breakthrough in autonomous warehouse navigation",
    "Helix Robotics faces regulatory probe over safety protocols",
    "Helix stock rises 12% on strong quarterly earnings report",
    "Workers union raises concerns about Helix automation plans",
    "Helix Robotics partners with major retailer for pilot program",
]


def ask(client, prompt):
    """Simple API call wrapper"""
    response = client.messages.create(
        model=MODEL, max_tokens=300, messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


def draft(client, headlines):
    """Generate initial briefing from headlines"""
    joined = "\n".join(f"- {h}" for h in headlines)
    prompt = f"Write a brief morning briefing summarizing these Helix Robotics headlines:\n\n{joined}\n\nKeep it concise and balanced."
    return ask(client, prompt)


def critique(client, headlines, draft_text):
    """
    Critique the draft against standards.
    Returns a list of specific, actionable problems - NOT a rewrite.
    """
    joined = "\n".join(f"- {h}" for h in headlines)
    prompt = (
        f"{STANDARDS}\n\n"
        f"Headlines:\n{joined}\n\n"
        f"Draft briefing:\n{draft_text}\n\n"
        "Critique the draft against the standards above. List specific, actionable "
        "problems as short bullets (e.g. buries the regulatory probe, omits the "
        "12% figure, too long, leans positive). Do NOT rewrite — only list issues."
    )
    return ask(client, prompt)


def refine(client, headlines, draft_text, critique_text):
    """
    Refine the draft to address all critique points.
    Returns only the final briefing text.
    """
    joined = "\n".join(f"- {h}" for h in headlines)
    prompt = (
        f"{STANDARDS}\n\n"
        f"Headlines:\n{joined}\n\n"
        f"Draft briefing:\n{draft_text}\n\n"
        f"Critique to address:\n{critique_text}\n\n"
        "Rewrite the briefing so it fixes every point in the critique and meets the "
        "standards. Output only the final briefing text."
    )
    return ask(client, prompt)


def main():
    print("\n" + "=" * 70)
    print("Exercise 3: Multi-Pass Review for Higher Quality")
    print("=" * 70)
    print("\nGenerating morning briefing with draft → critique → refine pattern.\n")

    # Step 1: Draft
    print("Generating DRAFT...")
    draft_text = draft(client, HEADLINES)

    print(f"\n{'=' * 70}")
    print("DRAFT")
    print("=" * 70)
    print(draft_text)

    # Step 2: Critique
    print(f"\n\nGenerating CRITIQUE...")
    critique_text = critique(client, HEADLINES, draft_text)

    print(f"\n{'=' * 70}")
    print("CRITIQUE")
    print("=" * 70)
    print(critique_text)

    # Step 3: Refine
    print(f"\n\nGenerating REFINED briefing...")
    refined_text = refine(client, HEADLINES, draft_text, critique_text)

    print(f"\n{'=' * 70}")
    print("REFINED")
    print("=" * 70)
    print(refined_text)

    # Summary
    print(f"\n{'=' * 70}")
    print("TAKEAWAYS")
    print("=" * 70)
    print("• Separate generate from judge - fresh attention on output")
    print("• Critique lists issues, doesn't rewrite - keeps it focused")
    print("• Refine addresses every point - concrete checklist to fix")
    print("• Multi-pass catches what single-shot misses\n")


if __name__ == "__main__":
    main()
