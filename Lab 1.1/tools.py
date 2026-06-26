import random

# Mock classification values for simulation
CLASSIFICATION_OPTIONS = {
    "product_area": ["Payments", "API Access", "Data Export", "Authentication", "Account Management"],
    "severity":     ["Critical", "High", "Medium", "Low"],
    "intent":       ["Issue Report", "Information Request", "Enhancement", "Account Query"],
}


def classify_ticket(ticket_text: str, fields_needed: list[str]) -> dict:
    """
    Simulates ticket classification by returning random values for requested fields.

    In a real implementation, this would use ML models or rule-based systems.
    For this lab exercise, it returns mock data to demonstrate the agentic loop pattern.

    Parameters:
        ticket_text: Raw text content from the support ticket
        fields_needed: List of classification fields to return

    Returns:
        Dictionary mapping each requested field to a simulated classification value
    """
    result = {}
    for field in fields_needed:
        if field in CLASSIFICATION_OPTIONS:
            result[field] = random.choice(CLASSIFICATION_OPTIONS[field])
    return result
