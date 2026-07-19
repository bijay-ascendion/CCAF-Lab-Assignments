# Lab 5.1: Managing Context — Preservation, Optimization & Escalation

## Overview

This lab demonstrates three production techniques for managing context in long-running AI agent sessions:

1. **Context Preservation**: Pin critical facts into a `[CASE FACTS]` block re-injected into the system prompt every turn
2. **Tool Output Optimization**: Route tool results through `optimize(tool, raw)` to keep only relevant fields
3. **Ambiguity Escalation**: Instruct the model to ASK clarifying questions instead of guessing

## Scenario

An e-commerce customer support agent handling multi-turn conversations about orders, returns, refunds, and shipping. The agent must maintain reliable behavior from turn 3 to turn 30 without:
- Forgetting customer identity
- Getting overwhelmed by verbose tool outputs
- Making costly mistakes on ambiguous requests

**Example Customer**: Aarti Sharma (C-1001), Gold tier, with 3 orders (delivered, shipped, processing)

## File Structure

```
Lab 5.1/
├── main.py                 # Entry point with 3 demos
├── case_facts.py           # Demo 1: CaseFacts store implementation
├── tool_optimizer.py       # Demo 2: Tool output optimization
├── sample_data.py          # Mock customer and order data
├── requirements.txt        # Dependencies (anthropic, python-dotenv)
├── .env.example           # API key template
└── README.md              # This file
```

## Setup

### 1. Create Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

**.env contents:**
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
MODEL_NAME=claude-sonnet-4-20250514
```

### 4. Run the Lab

```bash
python main.py
```

## Demo Breakdown

### Demo 1: Persistent Case Facts (~15 min)

**Problem**: Long sessions evict early messages. Customer ID mentioned in turn 2 may be lost by turn 18.

**Solution**: 
- Store critical facts (customer_id, tier) in a `CaseFacts` object
- Render as `[CASE FACTS]` block and append to system prompt on every API call
- Model never has to search history to remember identity

**Implementation** (`case_facts.py`):
```python
class CaseFacts:
    def as_system_block(self) -> str:
        """Render facts as formatted block for system prompt"""
        if not self._facts:
            return ""
        lines = ["[CASE FACTS - these are confirmed and must be preserved]"]
        for k, v in self._facts.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)
```

**Test**: After 3 unrelated conversation turns, agent still knows customer_id and tier without asking.

### Demo 2: Tool Output Optimization (~15 min)

**Problem**: Raw database queries return hundreds of rows with dozens of columns. This:
- Burns tokens unnecessarily
- Buries relevant information in noise
- Pushes earlier turns out of context window

**Solution**:
- Define `RELEVANT_FIELDS` whitelist per tool
- Route all tool outputs through `optimize(tool_name, raw)`
- Only whitelisted fields reach the model

**Implementation** (`tool_optimizer.py`):
```python
RELEVANT_FIELDS = {
    "lookup_orders": ["order_id", "status", "placed_on", "total"],
    "get_order_details": ["order_id", "status", "placed_on", "total", "items"],
}

def optimize(tool_name: str, raw_result):
    keep = RELEVANT_FIELDS.get(tool_name)
    if keep is None:
        return raw_result  # Pass through unknown tools
    
    if isinstance(raw_result, list):
        return [{k: row[k] for k in keep if k in row} for row in raw_result]
    if isinstance(raw_result, dict):
        return {k: raw_result[k] for k in keep if k in raw_result}
    return raw_result
```

**Test**: RAW output shows full order records. OPTIMIZED output shows only 4 key fields. Typical reduction: 60-70%.

### Demo 3: Ambiguity Escalation (~15 min)

**Problem**: "Cancel my order" when customer has 2 open orders. Guessing wrong is costly (refunds, callbacks, escalations).

**Solution**:
- Add explicit instruction to system prompt: "If ambiguous, ASK a clarifying question"
- Model honors this throughout the session without code guards

**Implementation** (`main.py`):
```python
SYSTEM_BASE = (
    "You are a helpful support agent for an online retail company. "
    "Be concise. If a request is ambiguous (e.g. the customer has multiple "
    "open orders and didn't specify which), ASK a clarifying question "
    "instead of guessing. Always rely on the [CASE FACTS] block - those "
    "values are authoritative and you do not need to ask for them again."
)
```

**Test**: Customer with 2 open orders says "cancel my order". Agent lists both orders and asks which one to cancel.

## Why These Three Together?

Each fixes a different failure mode, and they reinforce each other:

1. **Case facts** → Agent doesn't re-ask what it knows → Conversations stay short
2. **Tool optimization** → Each response stays small → Case facts don't get crowded out
3. **Ambiguity escalation** → Agent stays honest → Prevents mistakes even when first two saved tokens

Drop any one and long sessions degrade in the others.

## Key Takeaways

### What Belongs in [CASE FACTS]?
✅ Identity-class facts: customer_id, tier, active_order_id  
✅ Facts that must survive history trimming  
❌ Long lists (those belong in tool output)  
❌ Facts that change frequently  

### When to Use optimize()?
✅ Tools that return many rows/columns  
✅ Database lookups with verbose schemas  
❌ Tools already returning minimal data  
❌ When you need content-aware summarization (use LLM for that)

### System Prompt vs Code Guards?
**System prompt** (escalation rule):
- Applies to ALL intents uniformly
- Model reasons about ambiguity naturally
- Single sentence covers all cases

**Code guards** (e.g., around cancel_order()):
- Only catches one tool
- Model still guesses elsewhere
- Requires maintenance per tool

## Common Mistakes

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Stuffing facts into first user turn | Evicted when history trimmed | Put in system prompt, rebuild every turn |
| Letting raw tool output reach model | Hundreds of rows evict earlier turns | Route through `optimize(tool, raw)` |
| Over-fitting whitelist to one demo | Breaks next intent needing different fields | Whitelist union of all reasonable fields |
| Encoding escalation as code guard | Only catches one tool, model guesses elsewhere | Put ASK rule in system prompt |
| Bloating [CASE FACTS] block | Every token paid on every call | Keep to identity-class facts only |
| Not marking block as authoritative | Model asks anyway out of politeness | State "these values are authoritative" |

## Expected Output

When all TODOs are complete and you run `python main.py`:

```
================================================================================
DEMO 1: Context Preservation via [CASE FACTS]
================================================================================
[Facts stored: customer_id=C-1001, tier=Gold]
...
✓ SUCCESS: Agent remembered customer_id and tier from [CASE FACTS]

================================================================================
DEMO 2: Tool Output Optimization
================================================================================
RAW size: 1847 characters
OPTIMIZED size: 445 characters
Reduction: 75.9%
✓ Agent answered using only the optimized fields

================================================================================
DEMO 3: Ambiguity Escalation
================================================================================
Customer C-1001 has 2 open orders:
  - O-9002: Shipped, $89.99
  - O-9003: Processing, $249.99
✓ SUCCESS: Agent asked for clarification and listed both open orders

ALL DEMOS COMPLETED
```

## Self-Check Questions

Before finishing the lab, answer these without looking back:

1. **Why re-inject [CASE FACTS] every turn** instead of saving early messages once?
   - Early messages get trimmed; system prompt stays visible

2. **Which fields belong in CaseFacts** vs ordinary chat history?
   - CaseFacts: identity-class (customer_id, tier) that must survive
   - History: conversational flow, specific requests

3. **How does optimize() differ from summarization?**
   - optimize(): Content-blind field whitelisting by name
   - Summarization: Content-aware reduction of text fields

4. **Why system prompt for escalation** vs code guard?
   - System prompt applies to ALL intents uniformly
   - Code guard only catches specific tool calls

5. **How do the three techniques reinforce each other?**
   - Facts keep agent from re-asking → shorter conversations
   - Optimization keeps responses small → facts don't get crowded out
   - Escalation prevents mistakes → even when first two saved tokens

## Model & Cost

- **Model**: Claude Sonnet 4 (configurable via `MODEL_NAME` in .env)
- **Cost**: Minimal (~dozen short turns + 2 tool calls)
- **Data**: Fictional customer/orders, no PII

## Further Reading

- [Anthropic API Overview](https://docs.claude.com/en/api/overview)
- [Tool Use Guide](https://docs.claude.com/en/docs/build-with-claude/tool-use)
- Skilljar Module 1: Introduction to Agent Skills
- Skilljar Module 1: Introduction to Subagents

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Copy `.env.example` to `.env`
- Add your actual API key

### "ModuleNotFoundError"
- Activate virtual environment
- Run `pip install -r requirements.txt`

### "TODOs not complete"
- Implement `as_system_block()` in `case_facts.py`
- Implement `optimize()` in `tool_optimizer.py`
- Both are already implemented in this version

### Agent doesn't remember facts
- Check that `as_system_block()` returns formatted string
- Verify facts_block is appended to system_prompt in chat()

### Tool output not optimized
- Check `RELEVANT_FIELDS` has entry for your tool
- Verify `optimize()` is called before JSON serialization in `run_tool()`

## License

Educational material for CCA-F Module 5.
