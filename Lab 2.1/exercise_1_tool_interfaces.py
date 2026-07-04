"""
Exercise 1: Tool Interfaces
Demonstrates how strong tool interfaces improve selection reliability
"""

import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# WEAK TOOLS - vague names, overlapping descriptions, loose parameters
WEAK_TOOLS = [
    {
        "name": "search",
        "description": "Search for stuff in the system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "q": {"type": "string"},
            },
            "required": ["q"],
        },
    },
    {
        "name": "lookup",
        "description": "Look up things by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "q": {"type": "string"},
            },
            "required": ["q"],
        },
    },
]

# STRONG TOOLS - precise names, explicit descriptions with when-NOT-to-use, typed parameters
STRONG_TOOLS = [
    {
        "name": "search_products",
        "description": (
            "Search the NorthPeak product CATALOG for items we sell (tents, "
            "sleeping bags, stoves, boots, etc.) by free-text query. Use this for "
            "availability, price, or whether a product exists. Do NOT use this to "
            "check something a customer already bought — for an existing purchase "
            "use get_order_status instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Free-text product query, e.g. '4 person tent'."},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_order_status",
        "description": (
            "Retrieve the status of an EXISTING customer order by its order ID "
            "(shipping status, items, tracking). Use this whenever the customer "
            "gives an order number or references a purchase. Do NOT use this to "
            "browse the catalog — for products use search_products instead."
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
    },
]

# TEST CASES - 6 support questions with expected tool
TEST_CASES = [
    {"question": "Do you carry a four-person tent?", "expected_tool": "search_products"},
    {"question": "Where is my order NP-100245?", "expected_tool": "get_order_status"},
    {"question": "What sleeping bags do you have?", "expected_tool": "search_products"},
    {"question": "Can you track order NP-100311?", "expected_tool": "get_order_status"},
    {"question": "Do you sell hiking boots?", "expected_tool": "search_products"},
    {"question": "What's the status of NP-100190?", "expected_tool": "get_order_status"},
]


def test_tool_selection(tools, toolset_name):
    """Test which tool the model selects for each question"""
    print(f"\n{'='*60}")
    print(f"Testing {toolset_name} toolset")
    print(f"{'='*60}")

    correct = 0
    total = len(TEST_CASES)

    for i, case in enumerate(TEST_CASES, 1):
        question = case["question"]
        expected = case["expected_tool"]

        # Map weak tool names to strong equivalents for comparison
        expected_weak = "search" if expected == "search_products" else "lookup"
        expected_name = expected_weak if toolset_name == "WEAK" else expected

        # Force a tool call with tool_choice={"type": "any"}
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            tool_choice={"type": "any"},
            messages=[{"role": "user", "content": question}]
        )

        # Extract which tool was called
        selected_tool = None
        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use":
                    selected_tool = block.name
                    break

        match = "OK" if selected_tool == expected_name else "MISS"
        if selected_tool == expected_name:
            correct += 1

        print(f"{i}. {question}")
        print(f"   Expected: {expected_name} | Selected: {selected_tool} | {match}")

    print(f"\n{toolset_name} Score: {correct}/{total} ({100*correct//total}%)")
    return correct, total


def main():
    print("\nExercise 1: Tool Interfaces")
    print("Comparing weak vs. strong tool interfaces for selection reliability")

    # Test weak tools
    weak_correct, weak_total = test_tool_selection(WEAK_TOOLS, "WEAK")

    # Test strong tools
    strong_correct, strong_total = test_tool_selection(STRONG_TOOLS, "STRONG")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Same model, same questions — only the interface changed.")
    print(f"Weak tools:   {weak_correct}/{weak_total} correct")
    print(f"Strong tools: {strong_correct}/{strong_total} correct")
    print(f"\nKey takeaway: Selection reliability comes from interface design,")
    print(f"not model size. Strong names, descriptions, and schemas win.")


if __name__ == "__main__":
    main()
