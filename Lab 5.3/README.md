# Lab 5.3: Trust & Traceability - Human Review, Confidence & Provenance

**Module**: M5 - Context Management & Reliability  
**Duration**: ~45 minutes  
**Sections**: S5 (Human Review & Confidence Calibration), S6 (Information Provenance & Uncertainty Handling)

## Overview

This lab builds an AI compliance reviewer for quarterly financial reports that demonstrates three critical trust mechanisms:

1. **Confidence Calibration** - Each finding includes a 0-1 confidence score to route high-confidence findings to auto-clear and low-confidence findings to human review
2. **Tamper-Proof Provenance** - Exact line citations attached locally from real data (never copied by the model) so citations cannot be hallucinated
3. **Confirmed vs. Contested** - Two independent review passes with findings confirmed by both passes or contested when they disagree

## Scenario

You're building an AI reviewer for quarterly financial reports. It scans for compliance issues (missing disclosures, risky language, inconsistent numbers) and produces findings for human compliance officers.

In regulated contexts, outputs cannot be black boxes:
- Wrong auto-approval = missed compliance issue
- Unverifiable flag = wasted reviewer time or blind trust

The solution: Make findings **calibrated**, **traceable**, and **corroborated**.

## File Inventory

| File | Role | Purpose |
|------|------|---------|
| `main.py` | entry | Runs two passes and prints the three buckets with provenance |
| `confidence.py` | Demo 1/3 (S5) | Buckets findings into auto_clear / human_review / contested |
| `reviewer.py` | Demo 2 (S6) | Claude review pass; parses JSON and attaches quote locally |
| `sample_report.py` | data | Mock report (one line each); `get_numbered_report()` & `get_quote()` |
| `.env.example` | setup | API key template |
| `requirements.txt` | setup | Dependencies: anthropic + python-dotenv |

## The Finding & Three Buckets

### Finding Shape
```python
{
    "line": 4,
    "quote": "<exact source line>",
    "flag": "unusual_change_without_disclosure",
    "confidence": 0.92
}
```

Note: The `quote` is attached **locally** from real data, never copied by the model.

### Three Buckets

1. **auto_clear** - In BOTH passes AND avg confidence >= 0.75
2. **human_review** - In both passes BUT below confidence threshold
3. **contested** - Flagged by only ONE of the two passes

## Setup

### Prerequisites

- Python 3.10+
- Anthropic API key

### Installation

1. **Install dependencies:**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **Configure API key:**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Run the reviewer:**
```bash
python main.py
```

## Demos

### Demo 1: Confidence Calibration & Routing (~15 min)

**Concepts**: S5 - Human Review & Confidence Calibration

**What it does**: Routes findings based on confidence threshold (default 0.75)

**Key file**: `confidence.py`

**Try this**:
1. Run `python main.py` and note which findings land in AUTO-CLEAR vs HUMAN REVIEW
2. Edit `CONFIDENCE_THRESHOLD` in `confidence.py`:
   - Lower to 0.5 → more findings auto-clear
   - Raise to 0.9 → more route to human review
3. Observe the trade-off between throughput and risk

**Reflection Questions**:
- Why route low-confidence findings to a human instead of auto-clearing everything?
- What happens to throughput and risk as you adjust the threshold?
- Why calibrate confidence per finding rather than one aggregate accuracy?

### Demo 2: Provenance - Cite the Source Line (~15 min)

**Concepts**: S6 - Information Provenance & Uncertainty Handling

**What it does**: Attaches exact source line from real data, not from model output

**Key file**: `reviewer.py`

**How it works**:
- Model returns only **line number** and flag
- `get_quote(line)` attaches the real text from `sample_report.py`
- Out-of-range lines are dropped (unverifiable)
- Parse failures degrade to zero findings (don't crash)

**Try this**:
1. Run `python main.py` and verify every finding shows line number and exact quote
2. Edit a line in `sample_report.py` and re-run
3. Observe the quote in output changes because it's read from source

**Reflection Questions**:
- Why not let the model return the quote text too?
- Why treat JSON parse failure as zero findings instead of crashing?
- Why validate line numbers against the real report?

### Demo 3: Confirmed vs. Contested (~15 min)

**Concepts**: S5 + S6 - Dual Review for Corroboration

**What it does**: Runs two independent review passes; confirms on agreement, contests on disagreement

**Key files**: `main.py`, `confidence.py`, `reviewer.py`

**How it works**:
- Two different prompts: `PROMPT_STRICT` and `PROMPT_GENERAL`
- Findings on same line number = "same finding"
- Both flag → confirmed (then routed by confidence)
- Only one flags → contested (surfaced for human adjudication)

**Try this**:
1. Run `python main.py` and examine the CONTESTED bucket
2. Note each contested entry shows what both passes said
3. Observe that confirmed findings still pass through confidence threshold

**Reflection Questions**:
- Why use two different prompts instead of the same prompt twice?
- Why surface disagreement to humans instead of resolving automatically?
- Why combine agreement AND confidence before auto-clearing?

## Key Concepts

### Why These Three Together?

They answer the three questions a reviewer asks of any AI finding:

1. **How sure?** → Confidence score + threshold routing
2. **Says who / from where?** → Provenance (exact line citation)
3. **Does anything corroborate it?** → Two passes (confirmed vs. contested)

**Confidence without provenance** = unverifiable guess  
**Provenance without corroboration** = single fallible opinion  
**Together** = calibrated, traceable, and corroborated findings

### Confidence Routing

```python
CONFIDENCE_THRESHOLD = 0.75

if avg_confidence >= CONFIDENCE_THRESHOLD:
    auto_clear.append(finding)
else:
    human_review.append(finding)
```

- **Raise threshold** → safer, more human review
- **Lower threshold** → faster, more auto-clear
- No universally right value - trades throughput against risk

### Provenance (Never Trust the Model's Copy)

```python
quote = get_quote(line_num)  # From OUR data, by line number
if not quote:
    continue  # Out of range → drop (unverifiable)
```

The model returns only a line number; the quote is attached locally from source data so it cannot be hallucinated.

### Confirmed vs. Contested

```python
if finding_in_both_passes:
    # Confirmed → route by confidence
    confirmed = True
else:
    # Contested → send to human
    contested.append(both_passes_flags)
```

Agreement earns trust; disagreement goes to a human.

## Common Mistakes

| Mistake | Why it matters |
|---------|----------------|
| Auto-clearing everything | A wrong auto-clear = missed compliance issue. Score confidence and route deliberately. |
| Letting model return quote text | Model-copied quotes can be altered/invented. Attach locally from source. |
| Crashing on malformed reply | One bad response shouldn't crash the run. Parse tolerantly, degrade gracefully. |
| Trusting single review pass | One opinion isn't corroboration. Run two passes with different prompts. |
| Auto-clearing on agreement alone | Two passes can agree and both be unsure. Require agreement AND confidence. |

## Results Interpretation

When you run `python main.py`, you'll see three buckets:

### ✅ AUTO-CLEAR
- Confirmed by both passes
- High confidence (>= 0.75)
- Safe to process automatically

### ⚠️ HUMAN REVIEW
- Confirmed by both passes
- Lower confidence (< 0.75)
- Needs human verification

### 🔀 CONTESTED
- Flagged by only one pass
- Needs human adjudication
- Shows both passes' perspectives

## Further Reading

- [Anthropic API Overview](https://docs.claude.com/en/api/overview)
- [Structured Outputs / Tool Use](https://docs.claude.com/en/docs/build-with-claude/tool-use)
- [Evaluation, Confidence & Provenance Patterns](https://docs.claude.com/en/docs/build-with-claude)

## Summary

This lab demonstrates production-grade trust mechanisms for regulated AI workflows:

1. **Confidence calibration** routes findings to appropriate review levels
2. **Provenance attachment** prevents hallucinated citations
3. **Dual-pass review** provides corroboration and surfaces disagreement

These patterns apply beyond financial compliance to any regulated AI workflow: loan underwriting, medical coding, insurance claims, contract review, etc.

The bar for regulated workflows is high: findings must be **calibrated**, **traceable**, and **corroborated**.
