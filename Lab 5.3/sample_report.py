"""
Lab 5.3 - Sample Financial Report Data

This module provides the mock quarterly financial report and utilities
to retrieve quotes by line number.

In a real system, this would read from a database or document store.
"""


# Mock quarterly financial report (one statement per line)
SAMPLE_REPORT = [
    "Q2 2025 Financial Report - TechCorp Inc.",
    "Revenue increased 15% year-over-year to $250M.",
    "Operating expenses were $180M, up from $150M last quarter.",
    "We experienced some challenges in the European market.",
    "Net income was $45M compared to $42M in Q1.",
    "Cash reserves stand at $500M.",
    "We have made certain adjustments to our accounting methods.",
    "R&D spending increased significantly to support new initiatives.",
    "Customer acquisition costs rose due to market expansion.",
    "We anticipate continued growth in the coming quarters.",
    "Some restructuring charges were incurred during the quarter.",
    "Our cloud services segment performed well above expectations.",
    "Debt levels remain at $200M with favorable terms.",
    "We are monitoring several emerging risks in the market.",
    "Management remains confident in our strategic direction.",
]


def get_numbered_report():
    """
    Get the report with line numbers for display to the model.

    Returns:
        String with each line numbered (1-indexed)
    """
    lines = []
    for i, line in enumerate(SAMPLE_REPORT, start=1):
        lines.append(f"{i}. {line}")
    return "\n".join(lines)


def get_quote(line_num):
    """
    Get the exact quote for a given line number.

    This is provenance - we attach the real text from our data,
    never trusting the model to copy it correctly.

    Args:
        line_num: 1-indexed line number

    Returns:
        The exact line text, or None if out of range
    """
    if not isinstance(line_num, int):
        return None

    # Convert to 0-indexed
    idx = line_num - 1

    if 0 <= idx < len(SAMPLE_REPORT):
        return SAMPLE_REPORT[idx]
    else:
        # Out of range - unverifiable
        return None
