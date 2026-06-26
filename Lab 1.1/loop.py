import json
import time
import anthropic
from dotenv import load_dotenv
from tools import classify_ticket

load_dotenv()

TICKET = """From: james.parker@innovatecorp.com
Subject: Critical - API authentication failing for production environment

Our production API keys stopped working around 8:30 AM today.
Multiple services are down and we're losing revenue. Need immediate assistance."""

tool_definitions = [
    {
        "name": "classify_ticket",
        "description": (
            "Analyzes a support ticket and returns classification values for the specified fields. "
            "You may call this tool multiple times until you have confirmed values for all three "
            "required classification fields: product_area, severity, and intent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_text": {
                    "type": "string",
                    "description": "The full text content of the support ticket to analyze.",
                },
                "fields_needed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Array of classification field names to return. "
                        "Accepted values: \"product_area\", \"severity\", \"intent\"."
                    ),
                },
            },
            "required": ["ticket_text", "fields_needed"],
        },
    }
]

client = anthropic.Anthropic()

conversation = [
    {
        "role": "user",
        "content": (
            "Analyze and classify this support ticket. Extract three classification fields: "
            "product_area, severity, and intent. Use the classify_ticket tool repeatedly "
            "until all three fields are confirmed. Continue calling until complete.\n\n"
            f"{TICKET}"
        ),
    }
]

loop_iteration = 0
while True:
    loop_iteration += 1

    # Retry logic for API rate limiting
    for retry_attempt in range(5):
        try:
            response = client.messages.create(
                model="claude-opus-4-8",
                max_tokens=1024,
                tools=tool_definitions,
                messages=conversation,
            )
            break
        except anthropic.OverloadedError:
            backoff_seconds = 2 ** retry_attempt
            print(f"  [Rate limited] Retrying in {backoff_seconds}s...")
            time.sleep(backoff_seconds)
    else:
        raise RuntimeError("API overloaded after 5 retry attempts.")

    print(f"\n--- Loop iteration {loop_iteration} | Stop reason: {response.stop_reason} ---")

    # Critical: Always append assistant response before branching on stop_reason
    conversation.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        # Extract final text response
        final_output = next(
            (block.text for block in response.content if block.type == "text"),
            "(No final text generated)",
        )
        print(f"\n=== Classification Complete ===\n{final_output}")
        break

    if response.stop_reason == "tool_use":
        # Execute tool calls and collect results
        tool_outputs = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                print(f"  Tool call: {content_block.name}({json.dumps(content_block.input)})")
                tool_output = classify_ticket(**content_block.input)
                print(f"  Output: {tool_output}")
                tool_outputs.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": json.dumps(tool_output),
                    }
                )
        # Append tool results as user message to continue the loop
        conversation.append({"role": "user", "content": tool_outputs})
