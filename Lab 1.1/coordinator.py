import json
from subagents import run_classifier, run_crm_enricher, run_drafter, run_validator

SAMPLE_TICKET = """From: james.parker@innovatecorp.com
Subject: Critical - API authentication failing for production environment

Our production API keys stopped working around 8:30 AM today.
Multiple services are down and we're losing revenue. Need immediate assistance."""

CUSTOMER_EMAIL = "james.parker@innovatecorp.com"


def main():
    """
    Exercise 2: Basic multi-subagent pipeline
    Runs four subagents sequentially without shared context object
    """
    print("=" * 70)
    print("Starting 4-stage pipeline")
    print("=" * 70)

    print("\n[Stage 1: Classification]")
    classification_result = run_classifier(SAMPLE_TICKET)
    print(json.dumps(classification_result, indent=2))

    print("\n[Stage 2: Customer Enrichment]")
    customer_data = run_crm_enricher(CUSTOMER_EMAIL, classification_result)
    print(json.dumps(customer_data, indent=2))

    print("\n[Stage 3: Response Drafting]")
    draft_email = run_drafter(SAMPLE_TICKET, classification_result, customer_data)
    print(draft_email)

    print("\n[Stage 4: Quality Validation]")
    validation_outcome = run_validator(draft_email, classification_result, customer_data)
    print(validation_outcome)

    print("\n" + "=" * 70)
    print("Pipeline completed successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()
