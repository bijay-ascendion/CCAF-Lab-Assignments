"""
Demo 2/3 (S4): Scratchpad — disk-backed audit trail + checkpoint.
Per-mutation flush makes crash recovery possible.
"""

import json
from pathlib import Path


class Scratchpad:
    """A tiny JSON-on-disk store keyed by claim_id."""

    def __init__(self, path: str = "scratchpad.json"):
        self.path = Path(path)
        self._data: dict = {}

        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                # Corrupted file — start fresh but don't delete it.
                self._data = {}

    def status(self, claim_id: str) -> str:
        """Get the status of a claim (new, in_progress, done, failed)."""
        return self._data.get(claim_id, {}).get("status", "new")

    def log(self, claim_id: str, stage: str, payload) -> None:
        """Record what happened in a given stage for a given claim."""
        entry = self._data.setdefault(
            claim_id,
            {"status": "in_progress", "findings": []}
        )
        entry["findings"].append({"stage": stage, "payload": payload})
        self._flush()

    def mark_done(self, claim_id: str) -> None:
        """Mark a claim as successfully completed."""
        self._data[claim_id]["status"] = "done"
        self._flush()

    def mark_failed(self, claim_id: str, reason: str) -> None:
        """Mark a claim as failed with a reason."""
        entry = self._data.setdefault(claim_id, {"findings": []})
        entry["status"] = "failed"
        entry["failure_reason"] = reason
        self._flush()

    def _flush(self) -> None:
        """Write the entire scratchpad to disk. Every mutation flushes."""
        self.path.write_text(json.dumps(self._data, indent=2))
