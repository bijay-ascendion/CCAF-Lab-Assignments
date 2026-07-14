# Lab 4.2: Enforcing Structure - tool_use Schemas with Validation & Retry

**Module:** M4 — Prompt Engineering & Structured Output  
**Duration:** ~45 minutes  
**Focus:** tool_use + JSON Schema, Validation & Retry Loops

## Overview

This lab builds reliable structured output into a candidate-screening evaluator using tool schemas alone:
1. **Tool Schema + tool_choice (Ex 1):** Force structured output through tool definitions
2. **Schema + Semantic Validation (Ex 2):** Add cross-field policy validation
3. **Retry-and-Feedback Loop (Ex 3):** Build self-correcting loops with tool_result feedback

Each exercise demonstrates a layer of reliability that makes output structured, correct, and self-healing.

## Scenario

You're building the screening step for a **recruiting platform**. Each application becomes a structured evaluation that feeds a recruiter dashboard. The output must be:

- **Machine-readable** — every record has the same 4 fields with the same types
- **Consistent** — a `strong_hire` scored 5 cannot slip through
- **Guaranteed** — no parsing prose, no missing fields, no stray preambles

**Target record:**
```json
{
  "name": "string",
  "recommendation": "strong_hire" | "hire" | "no_hire",
  "score": 0-10,
  "reason": "string"
}
```

**Cross-field policy:**
- `strong_hire` must score ≥ 8
- `no_hire` must score ≤ 4

## Setup

### Prerequisites

- Python 3.9+
- Anthropic SDK: `pip install "anthropic>=0.40.0"`
- API Key: Set `ANTHROPIC_API_KEY` environment variable

### Installation

1. Navigate to the lab directory:
```bash
cd "Lab 4.2"
```

2. Create a Python virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your API key:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

5. Load environment variables:
```bash
# On Unix/Mac:
export $(grep -v '^#' .env | xargs)

# On Windows (PowerShell):
Get-Content .env | ForEach-Object {
    if ($_ -notmatch '^#' -and $_ -match '=') {
        $name, $value = $_ -split '=', 2
        Set-Item -Path "env:$name" -Value $value
    }
}
```

## Exercises

### Exercise 1: Force Structured Output with tool_use + JSON Schema (~15 min)

**Goal:** Use a tool's input_schema to guarantee structured output every time.

**What it demonstrates:**
- Asking for "JSON" in prose is unreliable (markdown fences, missing fields, invented keys)
- Defining the target as a tool's `input_schema` + forcing `tool_choice` makes the tool arguments ARE your structured object
- No parsing, no regex, no `json.loads` — just read `block.input`

**Run:**
```bash
python exercise_1_tool_schema.py
```

**What to observe:**
- 3 candidates evaluated: strong, mid-level, junior
- Each returns a clean dict with exactly 4 fields
- No prose, no markdown fences, no missing keys
- The schema is the contract

**Key concepts:**
- Define complete `input_schema` with all properties, types, constraints
- Use `enum` for recommendation field
- Use `integer` with `minimum`/`maximum` for score
- Mark all fields as `required`
- Force tool with `tool_choice={"type": "tool", "name": "record_evaluation"}`
- Read structured payload from `tool_use.input`

### Exercise 2: Schema + Semantic Validation (~15 min)

**Goal:** Add validation for rules that JSON Schema cannot express.

**What it demonstrates:**
- JSON Schema handles syntax (types, enums, ranges)
- Your validator handles semantics (cross-field policy)
- Policy: `strong_hire` ⇒ score ≥ 8; `no_hire` ⇒ score ≤ 4

**Test offline first:**
```bash
python exercise_2_validation.py --check
```

**Then run live:**
```bash
python exercise_2_validation.py
```

**What to observe:**
- Offline: 3 fixtures tested (good record, bad structure, policy violation)
- Live: candidate evaluation validated against all rules
- Validator returns `(ok: bool, errors: list[str])`
- Cross-field rules catch semantic violations

**Key concepts:**
- Validator is defensive: accepts anything, returns structured verdict
- Check `isinstance(payload, dict)` first
- Filter bool from int: `isinstance(score, int) and not isinstance(score, bool)`
- Cross-field rules checked after basic type validation
- Return tuple `(ok, errors)` not exceptions
- Offline `--check` mode tests logic before API calls

**Validation rules:**
1. name is non-empty string
2. recommendation in `["strong_hire", "hire", "no_hire"]`
3. score is integer 0-10 (watch out for bool!)
4. reason is non-empty string
5. `strong_hire` ⇒ score ≥ 8
6. `no_hire` ⇒ score ≤ 4

### Exercise 3: Retry-and-Feedback Loop (~15 min)

**Goal:** Build a self-correcting loop that feeds validation errors back to the model.

**Test offline first:**
```bash
python exercise_3_retry_loop.py --demo
```

**Then run live:**
```bash
python exercise_3_retry_loop.py
```

**What to observe:**
- Offline: simulates 2 attempts (invalid → corrected)
- Live: model typically passes on attempt 1, or self-corrects on attempt 2
- On failure, error fed back as `tool_result` with `is_error=True`
- Loop capped at `max_attempts` to guarantee termination

**Key concepts:**
- Build `messages` array with conversation history
- On validation failure:
  1. Append assistant's `response.content`
  2. Append `tool_result` with `is_error=True` and error string
  3. Include `tool_use_id` matching the tool call
- Model sees its tool_use followed by the failure, corrects on next attempt
- Cap retries (typically 3) to prevent infinite loops
- Return last payload even if invalid (with errors)

**Retry loop pattern:**
```python
messages = [{"role": "user", "content": user_prompt}]
for attempt in range(1, max_attempts + 1):
    resp = client.messages.create(
        model=MODEL,
        tools=[EVALUATE_TOOL],
        tool_choice={"type": "tool", "name": "record_evaluation"},
        messages=messages,
        max_tokens=300
    )
    
    tool_use = next(b for b in resp.content if b.type == "tool_use")
    ok, errors = validate(tool_use.input)
    
    if ok:
        return tool_use.input, []
    
    # Feed error back
    messages.append({"role": "assistant", "content": resp.content})
    messages.append({"role": "user", "content": [{
        "type": "tool_result",
        "tool_use_id": tool_use.id,
        "is_error": True,
        "content": f"Validation failed: {'; '.join(errors)}. Call record_evaluation again with corrected values."
    }]})

return last_payload, errors  # cap reached
```

## Key Takeaways

1. **Tool schema is the contract** — Asking for JSON in prose is unreliable. Define the target as a tool's `input_schema` and force `tool_choice`, then read `block.input` directly.

2. **Schema enforces shape; code enforces meaning** — JSON Schema handles types/enums/ranges. Your validator handles cross-field policy the schema cannot express.

3. **Return (ok, errors), don't raise** — Tuples make retry loops simple. Exceptions make them awkward.

4. **Feed errors back as tool_result** — On validation failure, append the assistant turn + a user turn with `tool_result(is_error=True)` carrying the specific error. The model sees its mistake and corrects it.

5. **Cap retries** — `max_attempts` guarantees termination even if the model never gets it right. Return the last payload + errors so callers can escalate.

6. **Three layers of reliability:**
   - **Tool schema** fixes the shape (every response is a typed object)
   - **Validator** fixes the meaning (cross-field rules checked in code)
   - **Retry loop** fixes the failure mode (self-correcting with bounded budget)

## Reflection Questions

### Exercise 1
- Why is a tool's `input_schema` + `tool_choice` more reliable for structured output than asking the model to "reply in JSON"?
- The enum `["strong_hire", "hire", "no_hire"]` lives in the schema, while `strong_hire ⇒ score ≥ 8` does not. What kinds of rules belong in JSON Schema vs. code?
- If you removed `"required": ["name", "recommendation", "score", "reason"]`, how would downstream code break?

### Exercise 2
- Why is `strong_hire ⇒ score ≥ 8` enforced in `validate()` instead of in the JSON Schema?
- The validator returns `(ok, errors)` instead of raising. Why is a tuple a better contract than an exception?
- Why test `not isinstance(score, bool)` even though we already test `isinstance(score, int)`?

### Exercise 3
- Why is the validation error returned as a `tool_result` with `is_error=True` rather than as a normal user message?
- Why append the assistant's previous `resp.content` to `messages` before adding the `tool_result`?
- Why cap the retries instead of looping until output is valid? What's the failure mode of an uncapped loop?

## Files

```
Lab 4.2/
├── README.md                          # This file
├── requirements.txt                   # anthropic>=0.40.0, python-dotenv
├── .env.example                       # API key template
├── .gitignore                         # Python ignores
├── exercise_1_tool_schema.py         # Tool schema + forced tool_choice
├── exercise_2_validation.py          # Schema + semantic validation (--check mode)
└── exercise_3_retry_loop.py          # Retry-and-feedback loop (--demo mode)
```

## Common Mistakes to Avoid

| Mistake | Why it matters and what to do instead |
|---------|--------------------------------------|
| Asking for JSON in prose | Markdown fences, preambles, and missing fields creep in. Define the shape as a tool's `input_schema` and force `tool_choice` — the tool arguments ARE the structured object. |
| Putting cross-field policy in the schema | Basic JSON Schema can't express `strong_hire ⇒ score ≥ 8`. Keep types/enum/range in the schema and policy rules in `validate()`. |
| Raising from the validator | Exceptions make the retry loop awkward. Return `(ok, errors)` so the caller can feed the message back to the model and keep going. |
| Forgetting that bool is an int | `isinstance(True, int)` is `True`. If you don't filter bool out, `score=True` passes silently as 1. Test `isinstance(score, int) and not isinstance(score, bool)`. |
| Sending the error as a plain user message | The model loses the link to its previous tool call. Use a `tool_result` with the matching `tool_use_id` and `is_error=True` so the failure is attached to the right turn. |
| Uncapped retry loop | A truly stuck case can spend tokens forever. Cap with `max_attempts` and return the last payload + errors so callers can decide whether to escalate. |

## Further Reading

- [Anthropic Tool Use Documentation](https://docs.claude.com/en/docs/build-with-claude/tool-use)
- [How to Implement Tool Use](https://docs.claude.com/en/docs/build-with-claude/tool-use/implement-tool-use)
- [Skilljar — Building with the Claude API](https://skilljar.anthropic.com/)

## Success Criteria

After completing this lab, you should be able to:

✓ Force structured output through tool_use and JSON Schema  
✓ Add schema + semantic validation to catch bad data  
✓ Build retry-and-feedback loops that self-correct  
✓ Distinguish syntax rules (schema) from semantic rules (code)  
✓ Feed validation errors back as tool_result with is_error=True  
✓ Cap retries to guarantee termination
