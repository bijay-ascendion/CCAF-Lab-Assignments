from context import TicketContext


class PipelineGateError(Exception):
    """Raised when a pipeline gate condition fails"""
    pass


def gate_classification(ctx: TicketContext) -> None:
    """
    Gate 1: Ensures classification stage completed successfully.
    Blocks pipeline if product_area, severity, or intent are missing.
    """
    if ctx.classification_complete():
        return

    missing_fields = []
    if ctx.product_area is None:
        missing_fields.append("product_area")
    if ctx.severity is None:
        missing_fields.append("severity")
    if ctx.intent is None:
        missing_fields.append("intent")

    raise PipelineGateError(
        f"Ticket {ctx.ticket_id}: Classification incomplete. "
        f"Missing fields: {missing_fields}. Cannot proceed to enrichment stage."
    )


def gate_enrichment(ctx: TicketContext) -> None:
    """
    Gate 2: Ensures customer enrichment stage completed successfully.
    Blocks pipeline if account_tier or sla_tier are missing.
    """
    if ctx.enrichment_complete():
        return

    missing_fields = []
    if ctx.account_tier is None:
        missing_fields.append("account_tier")
    if ctx.sla_tier is None:
        missing_fields.append("sla_tier")

    raise PipelineGateError(
        f"Ticket {ctx.ticket_id}: Customer enrichment incomplete. "
        f"Missing fields: {missing_fields}. Cannot proceed to response drafting."
    )


def gate_draft(ctx: TicketContext) -> None:
    """
    Gate 3: Ensures response draft was generated.
    Blocks pipeline if draft_response is None.
    """
    if ctx.draft_complete():
        return

    raise PipelineGateError(
        f"Ticket {ctx.ticket_id}: Response draft missing. "
        f"Cannot proceed to validation stage."
    )
