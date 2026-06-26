import re
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Use Claude Haiku for fast, cost-effective subagent tasks
MODEL_ID = "claude-haiku-4-5-20251001"

client = anthropic.Anthropic()


def run_classifier(ticket: str) -> dict:
    """
    Classifier Agent: Analyzes ticket and extracts structured classification fields.
    Returns product_area, severity, and intent as JSON.
    """
    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=256,
        system=(
            "You are a ticket classification expert. Analyze the support ticket and return "
            "a JSON object with three fields: product_area, severity, and intent. "
            "Be concise and output only valid JSON."
        ),
        messages=[{"role": "user", "content": ticket}],
    )
    raw_text = response.content[0].text.strip()
    # Clean up markdown code fences if present
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)
    return json.loads(raw_text)


def run_crm_enricher(customer_email: str, classification: dict) -> dict:
    """
    CRM Enricher Agent: Looks up customer account details.

    Note: In production, this would call a real CRM API via MCP tools.
    For this lab, we simulate the lookup with hardcoded values.
    """
    # Make a dummy API call to demonstrate the pattern
    # (In practice, this would invoke an MCP tool for actual CRM integration)
    client.messages.create(
        model=MODEL_ID,
        max_tokens=64,
        system="You are simulating a CRM database lookup. Respond with mock account data.",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Email: {customer_email}\n"
                    f"Ticket classification: {json.dumps(classification)}"
                ),
            }
        ],
    )

    # Return simulated customer data
    return {
        "account_tier": "Enterprise",
        "sla_tier": "Gold",
        "account_manager": "Alex Morgan",
        "contract_value": "$150,000",
    }


def run_drafter(ticket: str, classification: dict, crm: dict) -> str:
    """
    Drafter Agent: Generates a professional first-response email.
    Uses classification and CRM data to personalize the response.
    """
    input_context = (
        f"Original ticket:\n{ticket}\n\n"
        f"Classification data:\n{json.dumps(classification, indent=2)}\n\n"
        f"Customer account info:\n{json.dumps(crm, indent=2)}"
    )

    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=512,
        system=(
            "You are a support response specialist. Draft a professional, empathetic "
            "first-response email addressing the customer's issue. Reference their SLA tier "
            "and acknowledge the severity appropriately. Keep it concise and action-focused."
        ),
        messages=[{"role": "user", "content": input_context}],
    )
    return response.content[0].text


def run_validator(draft: str, classification: dict, crm: dict) -> str:
    """
    Validator Agent: Reviews draft response for quality and accuracy.
    Checks product area alignment, SLA commitments, and tone.
    """
    validation_prompt = (
        f"Review this draft response:\n\n{draft}\n\n"
        f"Context:\n"
        f"- Product area: {classification.get('product_area')}\n"
        f"- Severity: {classification.get('severity')}\n"
        f"- Customer tier: {crm.get('account_tier')}\n"
        f"- SLA: {crm.get('sla_tier')}\n"
    )

    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=256,
        system=(
            "You are a quality assurance reviewer for customer support responses. "
            "Verify the draft addresses the correct product area, honors SLA commitments, "
            "and maintains professional tone. Output 'APPROVED' if all checks pass, "
            "otherwise list specific concerns."
        ),
        messages=[{"role": "user", "content": validation_prompt}],
    )
    return response.content[0].text
