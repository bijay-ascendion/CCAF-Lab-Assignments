"""
Demo 1: Context Preservation via [CASE FACTS] block.

The CaseFacts store pins identity-class information (customer id, tier, active
order) so it survives even when the message history is trimmed. Every token here
is paid on every API call, so keep it minimal — only facts that must never be lost.
"""


class CaseFacts:
    """
    A tiny key-value store of facts that must survive every turn.

    Why this matters:
    Long sessions evict early messages. If customer_id only appeared in turn 2,
    by turn 18 it's either out of the window or its attention is weak. Pinning
    it into a [CASE FACTS] block that gets re-injected into the system prompt
    on every turn means the model never has to dig through history.
    """

    def __init__(self):
        self._facts: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        """Store a fact. Overwrites if key already exists."""
        self._facts[key] = value

    def get(self, key: str) -> str:
        """Retrieve a fact by key."""
        return self._facts.get(key, "")

    def as_system_block(self) -> str:
        """
        Render the facts as a single text block for injection into the system prompt.

        TODO (Demo 1): Implement this method.

        Returns a formatted string like:
            [CASE FACTS - these are confirmed and must be preserved]
            - customer_id: C-1001
            - tier: Gold

        If there are no facts, return an empty string.

        Keep it SHORT — every token here is paid for on every API call.
        """
        if not self._facts:
            return ""

        lines = ["[CASE FACTS - these are confirmed and must be preserved]"]
        for k, v in self._facts.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)
