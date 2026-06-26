import json
from context import TicketContext
from gates import PipelineGateError, gate_classification, gate_enrichment, gate_draft
from subagents import run_classifier, run_crm_enricher, run_drafter, run_validator

SAMPLE_TICKET = """From: james.parker@innovatecorp.com
Subject: Critical - API authentication failing for production environment

Our production API keys stopped working around 8:30 AM today.
Multiple services are down and we're losing revenue. Need immediate assistance."""

CUSTOMER_EMAIL = "james.parker@innovatecorp.com"


def main():
    """
    Exercise 4 (Sabotage): Demonstrates gate failure behavior
    Intentionally corrupts classification data to trigger Gate 1 failure
    """
    ticket_ctx = TicketContext(
        ticket_id="TICKET-12345",
        raw_ticket=SAMPLE_TICKET,
        customer_email=CUSTOMER_EMAIL,
    )

    print("=" * 70)
    print("Pipeline execution with intentional gate failure")
    print("=" * 70)

    try:
        print("\n[Stage 1: Classification]")
        classification_output = run_classifier(ticket_ctx.raw_ticket)
        ticket_ctx.product_area = classification_output.get("product_area")
        ticket_ctx.severity = classification_output.get("severity")
        ticket_ctx.intent = classification_output.get("intent")
        print(json.dumps(classification_output, indent=2))

        # SABOTAGE: Clear severity field to trigger gate failure
        ticket_ctx.severity = None
        print("\n[!] Sabotage applied: severity field cleared")

        gate_classification(ticket_ctx)
        print(">> Gate 1: PASSED")  # This line will never execute

        print("\n[Stage 2: Customer Enrichment]")
        enrichment_output = run_crm_enricher(ticket_ctx.customer_email, classification_output)
        ticket_ctx.account_tier = enrichment_output.get("account_tier")
        ticket_ctx.sla_tier = enrichment_output.get("sla_tier")
        ticket_ctx.account_manager = enrichment_output.get("account_manager")
        print(json.dumps(enrichment_output, indent=2))

        gate_enrichment(ticket_ctx)
        print(">> Gate 2: PASSED")

        print("\n[Stage 3: Response Drafting]")
        ticket_ctx.draft_response = run_drafter(
            ticket_ctx.raw_ticket,
            {"product_area": ticket_ctx.product_area, "severity": ticket_ctx.severity, "intent": ticket_ctx.intent},
            {"account_tier": ticket_ctx.account_tier, "sla_tier": ticket_ctx.sla_tier, "account_manager": ticket_ctx.account_manager},
        )
        print(ticket_ctx.draft_response)

        gate_draft(ticket_ctx)
        print(">> Gate 3: PASSED")

        print("\n[Stage 4: Quality Validation]")
        ticket_ctx.validation_result = run_validator(
            ticket_ctx.draft_response,
            {"product_area": ticket_ctx.product_area, "severity": ticket_ctx.severity, "intent": ticket_ctx.intent},
            {"account_tier": ticket_ctx.account_tier, "sla_tier": ticket_ctx.sla_tier, "account_manager": ticket_ctx.account_manager},
        )
        print(ticket_ctx.validation_result)

        print("\n" + "=" * 70)
        print("Pipeline completed successfully")
        print("=" * 70)

    except PipelineGateError as gate_error:
        print(f"\n!!! PIPELINE HALTED !!!")
        print(f"Gate failure (expected): {gate_error}")
        print("\nThis demonstrates how gates prevent downstream stages from running")
        print("when upstream dependencies are not satisfied.")


if __name__ == "__main__":
    main()
