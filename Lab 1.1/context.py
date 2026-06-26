from dataclasses import dataclass
from typing import Optional


@dataclass
class TicketContext:
    """
    Shared state object that flows through the entire pipeline.
    Each stage populates its own fields and downstream stages depend on prior completion.
    """

    # Initial ticket data (required)
    ticket_id: str
    raw_ticket: str
    customer_email: str

    # Stage 1: Classification fields
    product_area: Optional[str] = None
    severity: Optional[str] = None
    intent: Optional[str] = None

    # Stage 2: Customer data enrichment
    account_tier: Optional[str] = None
    sla_tier: Optional[str] = None
    account_manager: Optional[str] = None

    # Stage 3 & 4: Response generation and validation
    draft_response: Optional[str] = None
    validation_result: Optional[str] = None

    def classification_complete(self) -> bool:
        """Check if all classification fields are populated"""
        return all([
            self.product_area is not None,
            self.severity is not None,
            self.intent is not None
        ])

    def enrichment_complete(self) -> bool:
        """Check if customer enrichment fields are populated"""
        return all([
            self.account_tier is not None,
            self.sla_tier is not None
        ])

    def draft_complete(self) -> bool:
        """Check if response draft has been generated"""
        return self.draft_response is not None
