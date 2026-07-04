# Lab 2.1: Designing Reliable Tools

**Module:** M2 — Reliable Tool Use  
**Duration:** ~45 minutes  
**Focus:** Interfaces, Errors & Selection Control

## Overview

This lab builds three properties that make tool use reliable:
1. **Tool Interfaces (Ex 1):** Design tools the model selects correctly
2. **Structured Errors (Ex 2):** Handle failures as data, with retry logic
3. **Selection Control (Ex 3):** Use tool_choice to control which tool runs

## Setup

### Prerequisites

- Python 3.9+
- Anthropic SDK: `pip install "anthropic>=0.40.0"`
- API Key: Set `ANTHROPIC_API_KEY` environment variable

### Environment Variables

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-sonnet-4-20250514  # optional, defaults to a Sonnet model
```

## Exercises

### Exercise 1: Tool Interfaces (~15 min)

**Goal:** Design strong tool interfaces that drive correct selection.

**Run:**
```bash
python exercise_1_tool_interfaces.py
```

**What it does:**
- Compares WEAK vs STRONG tool interfaces
- Tests 6 support questions against both toolsets
- Measures routing accuracy with the same model

**Key concepts:**
- Use `object + action` names (e.g., `search_products`, `get_order_status`)
- Include when-to-use AND when-NOT-to-use in descriptions
- Type parameters with patterns (e.g., `"pattern": "^NP-[0-9]{6}$"`)

### Exercise 2: Structured Errors & Retries (~15 min)

**Goal:** Wrap flaky services to return failures as data, not exceptions.

**Run:**
```bash
# Self-check without API calls
python exercise_2_structured_errors.py --check

# Live agent with flaky service
python exercise_2_structured_errors.py
```

**What it does:**
- Wraps a flaky Orders service with structured error envelopes
- Implements retry loop with exponential backoff
- Tests 3 scenarios: transient 504, permanent 404, malformed 400

**Key concepts:**
- Return `{"isError": True/False, "isRetryable": bool, ...}`
- Retry transient errors (408, 429, 500, 502, 503, 504) with backoff
- Stop immediately on permanent errors (400, 404)

### Exercise 3: Selection Control with tool_choice (~15 min)

**Goal:** Use `tool_choice` to make triage deterministic.

**Run:**
```bash
python exercise_3_tool_choice.py
```

**What it does:**
- Runs 4 support tickets under 3 tool_choice modes
- Compares auto / any / forced behavior
- Shows which mode reliably produces one classification per ticket

**Key concepts:**
- `{"type": "auto"}` — may talk / any tool / no tool
- `{"type": "any"}` — must call SOME tool (model picks)
- `{"type": "tool", "name": "classify_ticket"}` — must call exactly this tool

## Scenario

You're building a customer-support agent for **NorthPeak Outfitters**, an outdoor gear store. The agent must:
- Route catalog questions ("do you sell tents?") to `search_products`
- Route order questions ("where is NP-100245?") to `get_order_status`
- Survive a flaky backend with smart retry logic
- Classify tickets deterministically before routing

## Key Takeaways

1. **Selection reliability is an interface problem** — precise names, descriptions that say when NOT to use a tool, and typed parameters make the model choose correctly.

2. **Return failures as data, never exceptions** — the envelope lets the loop retry a timeout and stop on a 404.

3. **tool_choice scopes a turn** — use the narrowest setting that still works; forcing the classifier makes triage deterministic.

## Reflection Questions

### Exercise 1
- What does the accuracy jump from weak to strong tools tell you about tool-selection reliability?
- What does the `pattern` field buy you beyond helping the model route?
- Why is explicit negative contrast ("Do NOT use this...") more reliable than implicit boundaries?

### Exercise 2
- What breaks if a tool raises an exception instead of returning an error envelope?
- What goes wrong if you drop the retry cap? What if you drop the backoff?
- Should 404 and 400 be phrased identically to the customer?

### Exercise 3
- Why is "use the narrowest setting that still works" the right default?
- For triage, why is "called the wrong tool" worse than "called no tool"?
- Where would you catch a confident-but-wrong classification?

## Files

```
Lab 2.1/
├── README.md                           # This file
├── exercise_1_tool_interfaces.py      # Tool interface comparison
├── exercise_2_structured_errors.py    # Error handling and retries
└── exercise_3_tool_choice.py          # tool_choice modes
```

## Further Reading

- [Anthropic API — Tool Use](https://docs.claude.com/en/docs/build-with-claude/tool-use)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- Lab 1.x materials on tool-use loops and stop_reason
