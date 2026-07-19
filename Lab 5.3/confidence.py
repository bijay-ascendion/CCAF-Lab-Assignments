"""
Lab 5.3 - Demo 1: Confidence Calibration & Routing (S5)

This module implements the bucketing logic that routes findings based on:
1. Agreement between two passes (confirmed vs. contested)
2. Confidence threshold for auto-clear vs. human review

TODO: Implement the bucket() function below.
"""

# The confidence threshold for auto-clearing
# Findings with avg confidence >= this value will auto-clear
# Findings below this value route to human review
CONFIDENCE_THRESHOLD = 0.75


def bucket(pass_a, pass_b):
    """
    Bucket findings into auto_clear, human_review, and contested.

    Logic:
    - If a line appears in BOTH passes → confirmed
      - Average the confidence scores
      - If avg >= CONFIDENCE_THRESHOLD → auto_clear
      - If avg < CONFIDENCE_THRESHOLD → human_review
    - If a line appears in only ONE pass → contested

    Args:
        pass_a: List of findings from first review pass
        pass_b: List of findings from second review pass

    Returns:
        Dictionary with three keys:
            - auto_clear: High-confidence confirmed findings
            - human_review: Low-confidence confirmed findings
            - contested: Findings from only one pass
    """

    auto_clear = []
    human_review = []
    contested = []

    # Build lookup dictionaries by line number
    lines_a = {f["line"]: f for f in pass_a}
    lines_b = {f["line"]: f for f in pass_b}

    # Get all unique line numbers from both passes
    all_lines = set(lines_a.keys()) | set(lines_b.keys())

    for line_num in sorted(all_lines):
        finding_a = lines_a.get(line_num)
        finding_b = lines_b.get(line_num)

        if finding_a and finding_b:
            # Confirmed: present in both passes
            avg_conf = (finding_a["confidence"] + finding_b["confidence"]) / 2

            entry = {
                "line": line_num,
                "quote": finding_a["quote"],  # Both should have same quote
                "flag": finding_a["flag"],     # Use pass_a's flag description
                "avg_confidence": avg_conf,
                "confidence_a": finding_a["confidence"],
                "confidence_b": finding_b["confidence"]
            }

            # Route by confidence threshold
            if avg_conf >= CONFIDENCE_THRESHOLD:
                auto_clear.append(entry)
            else:
                human_review.append(entry)

        else:
            # Contested: only one pass flagged this line
            finding = finding_a or finding_b

            entry = {
                "line": line_num,
                "quote": finding["quote"],
                "flag_pass_a": finding_a["flag"] if finding_a else None,
                "flag_pass_b": finding_b["flag"] if finding_b else None,
                "confidence_a": finding_a["confidence"] if finding_a else None,
                "confidence_b": finding_b["confidence"] if finding_b else None
            }

            contested.append(entry)

    return {
        "auto_clear": auto_clear,
        "human_review": human_review,
        "contested": contested
    }
