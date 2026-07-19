"""
Demo 2: Tool Output Optimization via field whitelisting.

A raw lookup_orders call can return hundreds of rows with dozens of columns.
Pasting all of that into the conversation burns tokens, buries useful fields
under noise, and pushes earlier turns out of the context window. The fix:
optimize(tool, raw) keeps only the fields the current intent needs.
"""

# Fields we actually care about for each tool. Anything not in this list
# is dropped before the result reaches the model.
#
# Why whitelist instead of blacklist?
# - Defensive: a new column added upstream doesn't silently bloat the context.
# - Intent-aware: the union of fields any reasonable intent needs is usually
#   small and stable.
# - Auditable: you can see at a glance what the model is allowed to see.
RELEVANT_FIELDS = {
    "lookup_orders": ["order_id", "status", "placed_on", "total"],
    "get_order_details": ["order_id", "status", "placed_on", "total", "items"],
}


def optimize(tool_name: str, raw_result):
    """
    Trim a tool's raw output to just the whitelisted fields.

    TODO (Demo 2): Implement this function.

    Args:
        tool_name: The name of the tool that produced raw_result.
        raw_result: The raw output from the tool (list of dicts, single dict, or other).

    Returns:
        The same shape as raw_result but with only whitelisted fields kept.
        If tool_name has no whitelist entry, pass through untouched
        (in production you'd log a warning so unconfigured tools don't sneak past).

    Why this matters:
    A hundred-row order dump becomes a handful of relevant fields. Saves tokens,
    keeps the answer un-buried, and stops noise from pushing earlier turns out
    of the context window. The model answers faster and more accurately when it
    doesn't have to wade through SKUs and line-item quantities to find status.
    """
    keep = RELEVANT_FIELDS.get(tool_name)
    if keep is None:
        # No rule — pass through (consider logging a warning in production)
        return raw_result

    # Handle list of dicts (e.g. lookup_orders returns multiple orders)
    if isinstance(raw_result, list):
        return [{k: row[k] for k in keep if k in row} for row in raw_result]

    # Handle single dict (e.g. get_order_details returns one order)
    if isinstance(raw_result, dict):
        return {k: raw_result[k] for k in keep if k in raw_result}

    # Unknown shape — pass through
    return raw_result
