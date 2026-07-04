"""
Exercise 3: Selection Control with tool_choice
Demonstrates how tool_choice controls which tool runs on a turn
"""

import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Tool choice modes
MODES = {
    "auto": {"type": "auto"},           # May talk / any tool / no tool
    "any": {"type": "any"},             # Must call SOME tool (model picks)
    "FORCED": {"type": "tool", "name": "classify_ticket"},  # Must call exactly this tool
}

# Classification tool with closed enum for categories
CLASSIFY_TOOL = {
    "name": "classify_ticket",
    "description": "Classify a support ticket into exactly one routing category.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["order_issue", "product_question", "return_request", "other"]
            },
            "reason": {"type": "string"},
        },
        "required": ["category", "reason"],
    },
}

# A second tool that the model can wander toward under 'auto' or 'any' mode
DRAFT_REPLY_TOOL = {
    "name": "draft_customer_reply",
    "description": "Draft a reply to send to the customer.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reply": {"type": "string"},
        },
        "required": ["reply"],
    },
}

# Test tickets
TEST_TICKETS = [
    "My order NP-100245 hasn't arrived yet. Can you check the status?",
    "Do you have any waterproof hiking boots in stock?",
    "I'd like to return the tent I ordered last week.",
    "Can you tell me the warranty on your sleeping bags?",
]


def test_tool_choice_mode(mode_name, tool_choice):
    """Test triage behavior under a specific tool_choice mode"""
    print(f"\n{'='*60}")
    print(f"Testing mode: {mode_name}")
    print(f"tool_choice = {tool_choice}")
    print(f"{'='*60}")

    for i, ticket in enumerate(TEST_TICKETS, 1):
        print(f"\n{i}. Ticket: {ticket}")

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=[CLASSIFY_TOOL, DRAFT_REPLY_TOOL],
            tool_choice=tool_choice,
            messages=[{
                "role": "user",
                "content": f"Classify this support ticket: {ticket}"
            }]
        )

        # Check what happened
        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    if tool_name == "classify_ticket":
                        category = tool_input.get("category", "???")
                        reason = tool_input.get("reason", "")
                        print(f"   Tool: classify_ticket")
                        print(f"   Category: {category}")
                        print(f"   Reason: {reason[:60]}...")
                    else:
                        print(f"   Tool: {tool_name} (WRONG TOOL!)")
                        print(f"   Input: {json.dumps(tool_input)[:80]}...")
        elif response.stop_reason == "end_turn":
            # Model didn't call a tool - just returned text
            text_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text_content += block.text
            print(f"   No tool call - plain text response:")
            print(f"   {text_content[:80]}...")
        else:
            print(f"   Unexpected stop_reason: {response.stop_reason}")


def main():
    print("\nExercise 3: Selection Control with tool_choice")
    print("Comparing auto / any / forced tool_choice modes for deterministic triage")

    # Test all three modes
    for mode_name, tool_choice in MODES.items():
        test_tool_choice_mode(mode_name, tool_choice)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print("auto:   May return plain text or call wrong tool")
    print("any:    Guarantees a tool call, but may pick the wrong tool")
    print("FORCED: Guarantees classify_ticket is called every time")
    print()
    print("Key takeaway: Use the NARROWEST tool_choice that still does the job.")
    print("Force a tool when you need deterministic behavior (like triage).")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
