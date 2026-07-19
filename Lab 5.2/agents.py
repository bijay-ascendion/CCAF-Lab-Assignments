"""
Demo 1 (S3): StageResult envelope and three subagents.
Each subagent returns StageResult and NEVER raises into the coordinator.
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Any
from anthropic import Anthropic

# Load environment variables
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-5")
_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Covered procedures for validation
COVERED_PROCEDURES = {"99213", "99214", "99215"}

INTAKE_SYSTEM = """You are a claims intake specialist. Extract structured data from the claim.
Return JSON with: member_id, procedure_code, amount, member_active (boolean)."""


@dataclass
class StageResult:
    """Envelope every subagent must return. Failures are first-class."""
    stage: str
    ok: bool
    data: Any = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def run_intake(claim: dict) -> StageResult:
    """Call Claude to produce a clean structured summary of the claim."""
    try:
        response = _client.messages.create(
            model=MODEL_NAME,
            max_tokens=400,
            system=INTAKE_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(claim)}],
        )
        text = "".join(b.text for b in response.content if b.type == "text").strip()

        # Be forgiving about ```json fences
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        parsed = json.loads(text)
        return StageResult(stage="intake", ok=True, data=parsed)
    except Exception as exc:
        return StageResult(
            stage="intake",
            ok=False,
            error=f"{type(exc).__name__}: {exc}"
        )


def run_validation(claim: dict) -> StageResult:
    """Check policy rules. Fail fast and loudly."""
    if not claim.get("member_active", False):
        return StageResult(
            stage="validation",
            ok=False,
            error="member_not_active"
        )

    if claim.get("procedure_code") not in COVERED_PROCEDURES:
        return StageResult(
            stage="validation",
            ok=False,
            error=f"procedure_not_covered:{claim.get('procedure_code')}"
        )

    return StageResult(
        stage="validation",
        ok=True,
        data={"checks_passed": True}
    )


def run_adjudication(claim: dict) -> StageResult:
    """Deterministic decision based on amount."""
    amount = claim.get("amount", 0)

    if amount < 500:
        decision = "approved"
    elif amount < 2000:
        decision = "hold_for_review"
    else:
        decision = "denied"

    return StageResult(
        stage="adjudication",
        ok=True,
        data={"decision": decision, "amount": amount}
    )
