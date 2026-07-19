"""
Lab 5.1: Managing Context — Preservation, Optimization & Escalation

Three production techniques for long-running support sessions:
1. Pin identity into a [CASE FACTS] block re-injected into system prompt every turn.
2. Route tool outputs through optimize(tool, raw) to keep only relevant fields.
3. Instruct the model to ASK on ambiguous requests instead of guessing.

Run: python main.py
Completes all three demos in sequence once the TODOs are done.
"""

import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

from case_facts import CaseFacts
from tool_optimizer import optimize
from sample_data import (
    get_orders_for_customer,
    get_open_orders_for_customer,
    get_customer,
    ORDERS,
)

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")

# System prompt with all three context-management rules
SYSTEM_BASE = (
    "You are a helpful support agent for an online retail company. "
    "Be concise. If a request is ambiguous (e.g. the customer has multiple "
    "open orders and didn't specify which), ASK a clarifying question "
    "instead of guessing. Always rely on the [CASE FACTS] block - those "
    "values are authoritative and you do not need to ask for them again."
)

# Tool definitions
TOOLS = [
    {
        "name": "lookup_orders",
        "description": "Retrieve all orders for a customer. Returns order_id, status, dates, totals, and line items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID (e.g. C-1001)"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "get_order_details",
        "description": "Get detailed information about a specific order including items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID (e.g. O-9001)"
                }
            },
            "required": ["order_id"]
        }
    }
]


def run_tool(name: str, args: dict) -> str:
    """
    Execute a tool, optimize the result, return JSON for the model.

    Why optimize here instead of after the model sees it?
    The model never needs to read the noise. Optimizing before serialization
    means the context window stays clean from the start.
    """
    if name == "lookup_orders":
        raw = get_orders_for_customer(args["customer_id"])
    elif name == "get_order_details":
        raw = ORDERS.get(args["order_id"]) or {"error": "Order not found"}
    else:
        raw = {"error": f"unknown tool {name}"}

    # Demo 2: route through optimizer
    trimmed = optimize(name, raw)
    return json.dumps(trimmed, indent=2)


def chat(messages: list, facts: CaseFacts) -> str:
    """
    Single turn of the chat loop. Builds system prompt with facts block,
    handles tool calls, returns the final assistant message.
    """
    # Demo 1: re-inject case facts into system prompt every turn
    system_prompt = SYSTEM_BASE
    facts_block = facts.as_system_block()
    if facts_block:
        system_prompt = system_prompt + "\n\n" + facts_block

    while True:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=TOOLS
        )

        # Check if model wants to use tools
        if response.stop_reason == "tool_use":
            # Add assistant's response to messages
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Execute each tool call
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Add tool results to messages
            messages.append({
                "role": "user",
                "content": tool_results
            })
        else:
            # No more tool calls, extract text response
            text_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text_content += block.text
            return text_content


def demo_1_case_facts():
    """
    Demo 1: Persistent case facts survive even when message history is trimmed.

    Scenario: Three unrelated turns about store hours, shipping, and payment,
    followed by "what is my customer ID and tier?" — the agent must still know
    without re-asking or calling a tool.
    """
    print("\n" + "=" * 80)
    print("DEMO 1: Context Preservation via [CASE FACTS]")
    print("=" * 80)

    facts = CaseFacts()
    facts.set("customer_id", "C-1001")
    facts.set("tier", "Gold")

    print(f"\n[Facts stored: customer_id=C-1001, tier=Gold]")
    print(f"\n[CASE FACTS block that will be injected into system prompt:]")
    print(facts.as_system_block())
    print()

    # Three unrelated turns (simulating a long session)
    turns = [
        "What are your store hours?",
        "Do you offer free shipping?",
        "What payment methods do you accept?"
    ]

    messages = []
    for i, turn in enumerate(turns, 1):
        print(f"\nTurn {i} USER: {turn}")
        messages.append({"role": "user", "content": turn})
        reply = chat(messages, facts)
        messages.append({"role": "assistant", "content": reply})
        print(f"Turn {i} AGENT: {reply}")

    # The key test: agent must remember facts without them being in recent history
    print("\n" + "-" * 80)
    print("CRITICAL TEST: Facts must survive even though not mentioned recently")
    print("-" * 80)

    final_query = "Quick check: what is my customer ID and what tier am I?"
    print(f"\nTurn 4 USER: {final_query}")
    messages.append({"role": "user", "content": final_query})
    reply = chat(messages, facts)
    print(f"Turn 4 AGENT: {reply}")

    if "C-1001" in reply and "Gold" in reply:
        print("\n✓ SUCCESS: Agent remembered customer_id and tier from [CASE FACTS]")
    else:
        print("\n✗ WARNING: Agent may have lost track of the facts")


def demo_2_tool_optimization():
    """
    Demo 2: Tool output optimization keeps only relevant fields.

    Scenario: Customer asks to list their orders (just status and total).
    We'll print RAW vs OPTIMIZED side-by-side to show the token savings.
    """
    print("\n\n" + "=" * 80)
    print("DEMO 2: Tool Output Optimization")
    print("=" * 80)

    facts = CaseFacts()
    facts.set("customer_id", "C-1001")

    # Get raw data for comparison
    raw_orders = get_orders_for_customer("C-1001")
    optimized_orders = optimize("lookup_orders", raw_orders)

    print("\n--- RAW TOOL OUTPUT (what the DB returns) ---")
    print(json.dumps(raw_orders, indent=2))
    print(f"\nRAW size: {len(json.dumps(raw_orders))} characters")

    print("\n--- OPTIMIZED OUTPUT (what the model sees) ---")
    print(json.dumps(optimized_orders, indent=2))
    print(f"\nOPTIMIZED size: {len(json.dumps(optimized_orders))} characters")

    reduction = (1 - len(json.dumps(optimized_orders)) / len(json.dumps(raw_orders))) * 100
    print(f"\nReduction: {reduction:.1f}%")

    # Now let the agent answer using the optimized version
    messages = [
        {"role": "user", "content": "Please list my orders with their status and total."}
    ]

    print("\n" + "-" * 80)
    print("USER: Please list my orders with their status and total.")
    reply = chat(messages, facts)
    print(f"AGENT: {reply}")
    print("\n✓ Agent answered using only the optimized fields (order_id, status, placed_on, total)")


def demo_3_escalate_ambiguity():
    """
    Demo 3: Escalate ambiguity instead of guessing.

    Scenario: Customer with two open orders says "cancel my order".
    Agent must ASK which one, not pick randomly.
    """
    print("\n\n" + "=" * 80)
    print("DEMO 3: Ambiguity Escalation")
    print("=" * 80)

    facts = CaseFacts()
    facts.set("customer_id", "C-1001")

    open_orders = get_open_orders_for_customer("C-1001")
    print(f"\nCustomer C-1001 has {len(open_orders)} open orders:")
    for order in open_orders:
        print(f"  - {order['order_id']}: {order['status']}, ${order['total']}")

    print("\n" + "-" * 80)
    print("CRITICAL TEST: Ambiguous request must trigger clarification")
    print("-" * 80)

    messages = [
        {"role": "user", "content": "Please cancel my order."}
    ]

    print("\nUSER: Please cancel my order.")
    reply = chat(messages, facts)
    print(f"AGENT: {reply}")

    # Check if agent asked for clarification
    is_question = "?" in reply and ("which" in reply.lower() or "clarify" in reply.lower())
    has_both_orders = "O-9002" in reply and "O-9003" in reply

    if is_question and has_both_orders:
        print("\n✓ SUCCESS: Agent asked for clarification and listed both open orders")
    elif is_question:
        print("\n⚠ PARTIAL: Agent asked a question but may not have listed orders clearly")
    else:
        print("\n✗ WARNING: Agent should have asked which order to cancel")


def main():
    """Run all three demos in sequence."""
    print("\n" + "=" * 80)
    print("Lab 5.1: Managing Context — Preservation, Optimization & Escalation")
    print("=" * 80)
    print("\nScenario: E-commerce customer support agent handling multiple orders")
    print("Customer: Aarti Sharma (C-1001), Gold tier, 3 orders on file")

    try:
        demo_1_case_facts()
        demo_2_tool_optimization()
        demo_3_escalate_ambiguity()

        print("\n\n" + "=" * 80)
        print("ALL DEMOS COMPLETED")
        print("=" * 80)
        print("\nKey takeaways:")
        print("1. [CASE FACTS] preserves identity across long sessions")
        print("2. optimize() keeps tool outputs lean and focused")
        print("3. System prompt rules prevent costly ambiguity mistakes")
        print("\nAll three techniques work together to keep the agent reliable")
        print("at turn 3 and turn 30.")

    except Exception as e:
        print(f"\n\n✗ ERROR: {e}")
        print("\nCheck:")
        print("1. ANTHROPIC_API_KEY is set in .env")
        print("2. All TODOs in case_facts.py and tool_optimizer.py are complete")
        raise


if __name__ == "__main__":
    main()
