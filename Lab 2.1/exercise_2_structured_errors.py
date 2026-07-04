"""
Exercise 2: Structured Errors & Retries
Demonstrates how to handle flaky services with structured error envelopes and retry logic
"""

import os
import time
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# HTTP status codes that are retryable (transient failures)
RETRYABLE = {408, 429, 500, 502, 503, 504}


class ServiceError(Exception):
    """Custom exception for service errors"""
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


# Mock Orders service that can be configured to fail
_failure_queue = []


def inject_failure(status, message):
    """Queue a failure to be returned on the next call"""
    _failure_queue.append((status, message))


def orders_service(order_id):
    """Mock Orders service - returns order data or raises ServiceError"""
    # Check if we have a queued failure
    if _failure_queue:
        status, message = _failure_queue.pop(0)
        raise ServiceError(status, message)

    # Validate order ID format
    if not order_id.startswith("NP-") or len(order_id) != 9:
        raise ServiceError(400, f"Malformed order ID: {order_id}")

    # Check if order exists (simple check - only NP-1xxxxx range exists)
    order_num = int(order_id.split("-")[1])
    if order_num < 100000 or order_num >= 200000:
        raise ServiceError(404, f"Order {order_id} not found")

    # Success case
    return {
        "order_id": order_id,
        "status": "shipped",
        "items": ["Alpine Tent 4P", "Sleeping Bag -20F"],
        "tracking": "1Z999AA10123456784"
    }


def call_order_tool(order_id):
    """
    Wrapper that converts ServiceError into a structured dict.
    NEVER raises - always returns a dict with isError field.
    """
    try:
        data = orders_service(order_id)
        return {"isError": False, **data}
    except ServiceError as err:
        return {
            "isError": True,
            "isRetryable": err.status in RETRYABLE,
            "status": err.status,
            "error": err.message,
        }


def run_with_retry(order_id, max_attempts=4):
    """
    Retry loop with exponential backoff.
    - Retries transient failures (isRetryable=True) with backoff
    - Stops immediately on permanent failures (isRetryable=False)
    - Caps attempts at max_attempts
    """
    delay = 0.2
    for attempt in range(1, max_attempts + 1):
        print(f"  Attempt {attempt}/{max_attempts}...")
        result = call_order_tool(order_id)

        if not result["isError"]:
            print(f"  Success!")
            return result

        print(f"  Error: {result['error']} (status {result['status']}, retryable={result['isRetryable']})")

        if result["isRetryable"] and attempt < max_attempts:
            print(f"  Waiting {delay}s before retry...")
            time.sleep(delay)
            delay *= 2  # exponential backoff
            continue

        # Either non-retryable or out of attempts
        if not result["isRetryable"]:
            print(f"  Permanent error - stopping immediately")
        else:
            print(f"  Out of attempts - stopping")
        return result


# Tool definition for the agent
GET_ORDER_TOOL = {
    "name": "get_order_status",
    "description": (
        "Retrieve the status of an EXISTING customer order by its order ID. "
        "Returns shipping status, items, and tracking information."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "Order ID in the format 'NP-XXXXXX'.",
                "pattern": "^NP-[0-9]{6}$"
            },
        },
        "required": ["order_id"],
    },
}


def run_agent_turn(user_message, injected_failures=None):
    """Run one agent turn with the flaky Orders service"""
    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print(f"{'='*60}")

    # Inject failures if specified
    if injected_failures:
        for status, message in injected_failures:
            inject_failure(status, message)

    messages = [{"role": "user", "content": user_message}]

    # Agent loop
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[GET_ORDER_TOOL],
        messages=messages
    )

    # Process tool calls
    while response.stop_reason == "tool_use":
        # Extract tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                print(f"\nTool call: {tool_name}({tool_input})")

                # Execute tool with retry logic
                result = run_with_retry(tool_input["order_id"])

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

        # Continue conversation
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=[GET_ORDER_TOOL],
            messages=messages
        )

    # Extract final text response
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    print(f"\nAssistant: {final_text}")


def offline_self_check():
    """Self-check without using API - validates the envelope structure"""
    print("\n" + "="*60)
    print("OFFLINE SELF-CHECK (no API calls)")
    print("="*60)

    # Test 1: Success case
    print("\n1. Testing success case...")
    result = call_order_tool("NP-100245")
    assert result["isError"] == False, "Success should have isError=False"
    assert "order_id" in result, "Success should include order_id"
    print(f"   OK: {result}")

    # Test 2: 404 (non-retryable)
    print("\n2. Testing 404 (non-retryable)...")
    result = call_order_tool("NP-999999")
    assert result["isError"] == True, "404 should have isError=True"
    assert result["isRetryable"] == False, "404 should be non-retryable"
    assert result["status"] == 404, "Should have status 404"
    print(f"   OK: {result}")

    # Test 3: 503 (retryable)
    print("\n3. Testing 503 (retryable)...")
    inject_failure(503, "Service temporarily unavailable")
    result = call_order_tool("NP-100245")
    assert result["isError"] == True, "503 should have isError=True"
    assert result["isRetryable"] == True, "503 should be retryable"
    assert result["status"] == 503, "Should have status 503"
    print(f"   OK: {result}")

    # Test 4: 400 (non-retryable)
    print("\n4. Testing 400 malformed ID (non-retryable)...")
    result = call_order_tool("100245")
    assert result["isError"] == True, "400 should have isError=True"
    assert result["isRetryable"] == False, "400 should be non-retryable"
    assert result["status"] == 400, "Should have status 400"
    print(f"   OK: {result}")

    print("\n" + "="*60)
    print("All self-checks passed!")
    print("="*60)


def main():
    import sys

    if "--check" in sys.argv:
        offline_self_check()
        return

    print("\nExercise 2: Structured Errors & Retries")
    print("Demonstrating retry logic with a flaky Orders service")

    # Case A: Transient failure (504) that succeeds on retry
    print("\n\nCASE A: Transient 504 timeout - should retry and succeed")
    run_agent_turn(
        "Where is my order NP-100245?",
        injected_failures=[(504, "Gateway timeout")]
    )

    # Case B: Permanent failure (404) - no retry
    print("\n\nCASE B: Permanent 404 not found - should stop immediately")
    run_agent_turn(
        "Where is my order NP-999999?",
        injected_failures=[]
    )

    # Case C: Malformed ID (400) - no retry
    print("\n\nCASE C: Malformed order ID - should stop immediately")
    run_agent_turn(
        "Where is order 100245?",
        injected_failures=[]
    )

    print("\n" + "="*60)
    print("Key takeaway: Return failures as data, not exceptions.")
    print("The structured envelope lets the loop retry transient errors")
    print("and stop immediately on permanent ones.")
    print("="*60)


if __name__ == "__main__":
    main()
