"""
Lab 5.3 - Trust & Traceability: Human Review, Confidence & Provenance

Main entry point: Runs two review passes and prints the three buckets.

Usage:
    python main.py

The three buckets:
    - auto_clear: Confirmed findings with high confidence (>= 0.75)
    - human_review: Confirmed findings with lower confidence
    - contested: Findings flagged by only one of the two passes
"""

import os
from dotenv import load_dotenv
from reviewer import review
from confidence import bucket
from sample_report import get_numbered_report

# Load environment variables
load_dotenv()


def main():
    """Run the compliance reviewer end-to-end."""

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment.")
        print("   Create a .env file with: ANTHROPIC_API_KEY=your_key_here")
        return

    print("="*80)
    print("AI COMPLIANCE REVIEWER")
    print("Trust & Traceability: Human Review, Confidence & Provenance")
    print("="*80)
    print()

    # Get the sample report
    report_text = get_numbered_report()

    print("📄 Sample Report Loaded")
    print(f"   {len(report_text.splitlines())} lines")
    print()

    # Run two independent review passes
    print("🔍 Running Review Pass A (Strict)...")
    pass_a = review(report_text, mode="strict")
    print(f"   → Found {len(pass_a)} potential findings")
    print()

    print("🔍 Running Review Pass B (General)...")
    pass_b = review(report_text, mode="general")
    print(f"   → Found {len(pass_b)} potential findings")
    print()

    # Bucket the findings
    print("📊 Bucketing findings...")
    buckets = bucket(pass_a, pass_b)
    print()

    # Display results
    print("="*80)
    print("RESULTS")
    print("="*80)
    print()

    # Auto-clear bucket
    print(f"✅ AUTO-CLEAR ({len(buckets['auto_clear'])} findings)")
    print("   Confirmed by both passes, high confidence (>= 0.75)")
    print("-"*80)
    for finding in buckets['auto_clear']:
        print(f"   Line {finding['line']}: {finding['flag']}")
        print(f"   Confidence: {finding['avg_confidence']:.2f}")
        print(f"   Quote: \"{finding['quote']}\"")
        print()

    # Human review bucket
    print(f"⚠️  HUMAN REVIEW ({len(buckets['human_review'])} findings)")
    print("   Confirmed by both passes, but lower confidence")
    print("-"*80)
    for finding in buckets['human_review']:
        print(f"   Line {finding['line']}: {finding['flag']}")
        print(f"   Confidence: {finding['avg_confidence']:.2f}")
        print(f"   Quote: \"{finding['quote']}\"")
        print()

    # Contested bucket
    print(f"🔀 CONTESTED ({len(buckets['contested'])} findings)")
    print("   Flagged by only one pass - needs human adjudication")
    print("-"*80)
    for finding in buckets['contested']:
        print(f"   Line {finding['line']}")
        print(f"   Pass A: {finding['flag_pass_a'] or '(not flagged)'}")
        print(f"   Pass B: {finding['flag_pass_b'] or '(not flagged)'}")
        print(f"   Quote: \"{finding['quote']}\"")
        print()

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Auto-clear:    {len(buckets['auto_clear'])} findings")
    print(f"Human review:  {len(buckets['human_review'])} findings")
    print(f"Contested:     {len(buckets['contested'])} findings")
    print(f"Total:         {len(buckets['auto_clear']) + len(buckets['human_review']) + len(buckets['contested'])} findings")
    print()


if __name__ == "__main__":
    main()
