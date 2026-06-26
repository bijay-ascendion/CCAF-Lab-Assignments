# Support Ticket Classification Pipeline - Agentic AI Lab

A hands-on lab project demonstrating how to build multi-agent AI pipelines using the Anthropic Python SDK. This project walks through progressively complex patterns for orchestrating AI agents, from single-agent tool use to multi-stage pipelines with programmatic safety gates.

## What You'll Build

This lab implements an automated support ticket processing system with four specialized AI agents:

1. **Classifier Agent** - Analyzes incoming tickets and extracts structured metadata
2. **CRM Enricher Agent** - Looks up customer account details and SLA information  
3. **Response Drafter Agent** - Generates personalized, context-aware email responses
4. **Quality Validator Agent** - Reviews drafts for accuracy, tone, and completeness

## Project Files

### Core Components

| File | Description |
|------|-------------|
| `tools.py` | Mock classification tool that returns simulated values (demonstrates tool use pattern) |
| `context.py` | `TicketContext` dataclass for managing shared pipeline state |
| `gates.py` | Programmatic gate functions that enforce stage dependencies |
| `subagents.py` | Four specialized agent implementations using Claude Haiku |

### Exercise Implementations

| File | Exercise | Pattern Demonstrated |
|------|----------|---------------------|
| `loop.py` | Exercise 1 | Manual agentic loop with tool use - single agent repeatedly calls tools until task complete |
| `coordinator.py` | Exercise 2 | Basic multi-agent orchestration - sequential execution without shared state |
| `coordinator_v2.py` | Exercise 3 | Pipeline with shared context object - all state flows through `TicketContext` |
| `coordinator_v3.py` | Exercise 4 | Gated pipeline - programmatic validation between each stage |
| `coordinator_v3_sabotage.py` | Exercise 4 Demo | Intentional gate failure to demonstrate safety mechanism |

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Installation

1. **Clone or download this repository**

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install anthropic python-dotenv
   ```

4. **Configure your API key**
   
   Create a `.env` file in the project root:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

## Running the Exercises

Each exercise demonstrates a different architectural pattern. Run them in order to understand how complexity builds:

### Exercise 1: Agentic Loop with Tool Use
```bash
python loop.py
```
**What it demonstrates:** A single Claude Opus agent uses a tool repeatedly in a `while True` loop until it gathers all required classification fields. Shows the fundamental agentic loop pattern where the model decides when to call tools and when to return a final answer.

**Key concepts:** `tool_use` stop reason, `tool_result` messages, loop continuation logic

---

### Exercise 2: Multi-Agent Sequential Pipeline
```bash
python coordinator.py
```
**What it demonstrates:** Four specialized Haiku agents execute sequentially, each performing a focused task. No shared state object - results are passed as function arguments.

**Key concepts:** Agent specialization, sequential orchestration, output chaining

---

### Exercise 3: Pipeline with Shared Context
```bash
python coordinator_v2.py
```
**What it demonstrates:** Same four-agent pipeline, but all state flows through a single `TicketContext` dataclass. Each agent populates its fields, and downstream agents read from it.

**Key concepts:** Centralized state management, dataclass validation, context evolution through stages

---

### Exercise 4: Gated Pipeline (Production Pattern)
```bash
# Clean run - all gates pass
python coordinator_v3.py

# Sabotage run - Gate 1 fails deliberately
python coordinator_v3_sabotage.py
```
**What it demonstrates:** Adds programmatic gates between stages. Gates validate that required data is present before allowing the next stage to execute. If a gate fails, the pipeline stops immediately with a clear error.

**Key concepts:** Fail-fast validation, defensive programming, explicit dependencies

## Architecture Deep Dive

### Pipeline Flow

```
Input: Raw ticket + customer email
    ↓
┌─────────────────────────────────────────────┐
│ Stage 1: Classification                     │
│ Extract: product_area, severity, intent     │
└─────────────────────────────────────────────┘
    ↓
[ Gate 1: Verify all classification fields present ]
    ↓
┌─────────────────────────────────────────────┐
│ Stage 2: CRM Enrichment                     │
│ Lookup: account_tier, sla_tier, manager     │
└─────────────────────────────────────────────┘
    ↓
[ Gate 2: Verify account data loaded ]
    ↓
┌─────────────────────────────────────────────┐
│ Stage 3: Response Drafting                  │
│ Generate: Personalized email draft          │
└─────────────────────────────────────────────┘
    ↓
[ Gate 3: Verify draft was created ]
    ↓
┌─────────────────────────────────────────────┐
│ Stage 4: Quality Validation                 │
│ Review: Accuracy, tone, SLA compliance       │
└─────────────────────────────────────────────┘
    ↓
Output: Validated response ready to send
```

### The Gate Pattern

Gates are Python functions that enforce hard dependencies:

```python
def gate_classification(ctx: TicketContext) -> None:
    """Blocks pipeline if classification incomplete"""
    if not ctx.classification_complete():
        raise PipelineGateError(f"Missing fields: {missing}")
```

**Why gates matter:**
- **Fail fast** - Catch missing data immediately rather than in downstream stages
- **Clear errors** - Tell you exactly what's missing and where
- **Type safety** - Enforce invariants that the type system can't
- **Production reliability** - Prevent partial/corrupted state from propagating

### Model Selection Strategy

| Role | Model | Reasoning |
|------|-------|-----------|
| Agentic loop | Claude Opus 4.8 | Main orchestration requires strongest reasoning and tool use capabilities |
| All subagents | Claude Haiku 4.5 | Fast and cost-effective for focused, single-task execution |

In production, you'd profile each agent's accuracy vs. cost tradeoff and potentially use different models per agent based on task complexity.

## Key Learning Outcomes

1. **Manual agentic loops** - How to implement `while True` loops with `stop_reason` branching
2. **Tool use protocol** - Registering tools, handling `tool_use` blocks, appending `tool_result` messages
3. **Multi-agent orchestration** - Breaking complex tasks into specialized subagents
4. **Context management** - Using dataclasses to track state through multi-stage pipelines
5. **Defensive programming** - Adding gates to enforce dependencies and catch errors early

## Extending This Project

Ideas for taking this further:

- **Add real MCP tools** - Replace the mock CRM enricher with actual database lookups
- **Parallel execution** - Run independent stages (like validation checks) concurrently
- **Streaming responses** - Show draft generation progress in real-time
- **Human-in-the-loop** - Add approval gates where humans review before sending
- **Observability** - Add structured logging to trace decisions and timings
- **Error recovery** - Implement retry logic and fallback strategies

## Troubleshooting

**`ModuleNotFoundError: No module named 'anthropic'`**
- Make sure you activated your virtual environment and ran `pip install anthropic python-dotenv`

**`AuthenticationError` or `PermissionDeniedError`**
- Verify your `.env` file exists and contains a valid `ANTHROPIC_API_KEY`

**`OverloadedError: 529` errors**
- The code includes exponential backoff retry logic for Opus. If it persists after 5 retries, wait a few minutes and try again.

**Tool returns nonsensical values**
- `tools.py` intentionally returns random values to simulate non-deterministic tool behavior. This is expected and demonstrates how the agentic loop handles inconsistent results.

## Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Tool Use Guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Agentic Patterns](https://docs.anthropic.com/en/docs/build-with-claude/develop/agentic-workflows)

## License

MIT - Feel free to use this code for learning and experimentation.
