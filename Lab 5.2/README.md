# Lab 5.2: Resilient Systems - Error Propagation & Large Codebase Exploration

## Overview

This lab implements a healthcare claims processing pipeline demonstrating three key resilience patterns:

1. **Error Propagation (S3)**: StageResult envelope ensures failures are structured data, not exceptions
2. **Disk-backed Scratchpad (S4)**: Every finding logged to disk for audit and checkpoint
3. **Crash Recovery (S4)**: Resume from interruption without redoing finished work

## Scenario

A healthcare claims pipeline with three stages:
- **Intake**: Extract structured data from raw claim narrative (calls Claude API)
- **Validation**: Check policy rules (member active, procedure covered)
- **Adjudication**: Decide approve/hold/deny based on amount

## File Inventory

| File | Purpose |
|------|---------|
| `main.py` | Coordinator that walks claims through stages and handles crash recovery |
| `agents.py` | StageResult dataclass and three subagents (Demo 1 - S3) |
| `scratchpad.py` | Scratchpad class with per-mutation flush (Demo 2/3 - S4) |
| `sample_claims.py` | Three mock claims (CLM-002 deliberately fails validation) |
| `.env.example` | API key template |
| `requirements.txt` | Dependencies |

## Setup

1. **Create Python environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure API key**:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Running the Lab

### First Run - Process All Claims
```bash
python main.py
```

Expected output:
- CLM-001: intake...ok → validation...ok → adjudication...ok
- CLM-002: intake...ok → validation...FAIL (member_not_active)
- CLM-003: intake...ok → validation...ok → adjudication...ok

Summary: `done: 2  failed: 1  skipped: 0`

### Second Run - Crash Recovery Demonstration
```bash
python main.py
```

Expected output:
- All three claims show "(already done/failed, skipping)"
- Summary: `done: 0  failed: 0  skipped: 3`

### Manual Reset
To start fresh:
```bash
rm scratchpad.json
python main.py
```

## Key Concepts

### Demo 1: StageResult Envelope (S3)

Every subagent returns a structured result instead of raising exceptions:

```python
@dataclass
class StageResult:
    stage: str
    ok: bool
    data: Any = None
    error: str | None = None
```

**Why**: Failures become inspectable, structured data. The coordinator can decide how to react (log, retry, escalate) instead of catching generic exceptions.

### Demo 2: Disk-backed Scratchpad (S4)

Every mutation immediately flushes to disk:

```python
def log(self, claim_id, stage, payload):
    entry["findings"].append({"stage": stage, "payload": payload})
    self._flush()  # Immediate write
```

**Why**: Provides both audit trail and checkpoint state. A crash doesn't lose progress.

### Demo 3: Crash Recovery (S4)

Coordinator checks status before processing:

```python
if pad.status(claim_id) in ("done", "failed"):
    skipped_count += 1
    continue
```

**Why**: Re-runs process only unfinished work. No duplicate billing or re-processing.

## Three Pieces, One Contract

All three patterns are required together:

- **Without StageResult**: Scratchpad has missing entries from unhandled exceptions
- **Without Scratchpad**: Crashes lose all progress, no audit trail
- **Without Skip Rule**: Re-runs duplicate work and re-bill claims

## Testing Crash Recovery

Simulate a mid-run crash:

```bash
python main.py
# Press Ctrl+C after first claim processes
python main.py
# First claim skipped, remaining claims process
```

## Inspection

View the audit trail:
```bash
cat scratchpad.json
```

Structure per claim:
```json
{
  "CLM-001": {
    "status": "done",
    "findings": [
      {"stage": "intake", "payload": {...}},
      {"stage": "validation", "payload": {...}},
      {"stage": "adjudication", "payload": {...}}
    ]
  },
  "CLM-002": {
    "status": "failed",
    "failure_reason": "validation: member_not_active",
    "findings": [...]
  }
}
```

## Common Mistakes

1. **Letting subagents raise**: Wrap everything in try/except and return StageResult
2. **Memory-only state**: Always write findings to disk immediately
3. **Batching writes**: Per-mutation flush is the contract that enables crash recovery
4. **Auto-deleting scratchpad**: Keep reset manual to preserve audit trail
5. **Retrying failed claims automatically**: Let humans decide which failures to retry

## Reflection Questions

1. Why force every subagent to return StageResult rather than letting exceptions bubble up?
2. Why does `_flush()` run after EVERY mutation instead of batching?
3. Why skip both "done" AND "failed" claims on restart?
4. How would you extend this to support retry-then-escalate policies?
5. What changes are needed to support concurrent coordinators?

## Cost & Safety

- **Model**: Claude Sonnet 4.5 (only intake stage calls API)
- **Cost**: ~1 JSON extraction per claim (minimal)
- **Data**: Fictional claims with synthetic IDs (no PHI)
- **Reset**: Manual deletion of `scratchpad.json` (never auto-deleted)

## Lab Duration

~45 minutes hands-on
