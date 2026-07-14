# Lab 4.3: Scaling Output - Batch Processing & Multi-Pass Review

**Module:** M4 — Prompt Engineering & Structured Output  
**Duration:** ~45 minutes  
**Focus:** Message Batches API, Parallel Processing & Multi-Pass Review

## Overview

This lab demonstrates three patterns for scaling Claude workloads:
1. **Message Batches API (Ex 1):** Async batch processing for large offline workloads
2. **Parallel Processing (Ex 2):** ThreadPoolExecutor for time-critical bursts
3. **Multi-Pass Review (Ex 3):** Draft → Critique → Refine for higher quality

Each pattern fits a different point on the cost-vs-latency-vs-quality spectrum.

## Scenario

You're building a **media-monitoring pipeline** for Helix Robotics coverage. The pipeline has three distinct jobs:

- **Overnight bulk** → thousands of mentions need sentiment classification (cost and accuracy matter, latency doesn't)
- **Breaking news** → sudden burst needs fast classification (latency is everything)
- **Morning briefing** → daily summary needs high quality (one pass rarely enough)

**The challenge:** Wire each job to the right Claude pattern.

## Setup

### Prerequisites

- Python 3.9+
- Anthropic SDK: `pip install "anthropic>=0.40.0"`
- API Key: Set `ANTHROPIC_API_KEY` environment variable

### Installation

1. Navigate to the lab directory:
```bash
cd "Lab 4.3"
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

### Exercise 1: Message Batches API (~15 min)

**Goal:** Use async batch processing for large offline workloads.

**What it demonstrates:**
- Submit many `{custom_id, params}` requests at once
- Poll until `processing_status == "ended"`
- Match results back by `custom_id`, not submission order
- Trade latency for cost and scale

**Run:**
```bash
python exercise_1_message_batches.py
```

**If batch takes longer than 10 minutes:**
```bash
# Script will print a re-fetch command:
python exercise_1_message_batches.py --fetch <batch_id>
```

**What to observe:**
- Batch submitted with unique ID
- Status updates as requests process
- Results collected by `custom_id`
- Clean exit with re-fetch hint if needed

**Key concepts:**
- Each request needs `custom_id` for matching results
- Poll with deadline (10 min) to avoid hanging
- Batch results arrive in completion order, not submission order
- Use for overnight/bulk jobs, not real-time work

**Pattern:**
```python
# Build requests with custom_id
requests = [
    {
        "custom_id": f"headline-{i}",
        "params": {
            "model": MODEL,
            "max_tokens": 20,
            "messages": [{"role": "user", "content": PROMPT.format(h=h)}],
        },
    }
    for i, h in enumerate(headlines)
]

# Submit batch
batch = client.messages.batches.create(requests=requests)

# Poll until ended
while True:
    batch = client.messages.batches.retrieve(batch.id)
    if batch.processing_status == "ended":
        break
    time.sleep(10)

# Collect by custom_id
for entry in client.messages.batches.results(batch.id):
    if entry.result.type == "succeeded":
        print(f"{entry.custom_id}: {result}")
```

### Exercise 2: Parallel Processing for Throughput (~15 min)

**Goal:** Use ThreadPoolExecutor to overlap I/O waits and reduce wall-clock time.

**What it demonstrates:**
- Threads (not processes) for I/O-bound work
- `.map()` preserves input order
- Speedup limited by rate limits
- Typical 3-5x improvement with 5 workers

**Run:**
```bash
python exercise_2_parallel.py
```

**What to observe:**
- Sequential: waits for each request in turn
- Parallel: overlaps API waits, ~3-5x faster
- Results match item-for-item (`.map()` preserves order)
- Speedup printed at end

**Key concepts:**
- I/O-bound work: GIL doesn't matter, use threads
- `ThreadPoolExecutor.map()` preserves order automatically
- Workers default to 5 - tune cautiously (too many → 429 errors)
- Use for bursts, not overnight bulk

**Pattern:**
```python
from concurrent.futures import ThreadPoolExecutor

def run_parallel(client, headlines, workers=5):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        # .map preserves input order - results line up with headlines
        results = list(pool.map(lambda h: classify(client, h), headlines))
    return results

# Tune `workers` to your rate limit
```

### Exercise 3: Multi-Pass Review for Higher Quality (~15 min)

**Goal:** Separate generate from judge using draft → critique → refine pattern.

**What it demonstrates:**
- Draft: first pass generates briefing
- Critique: lists problems against standards (doesn't rewrite)
- Refine: addresses every critique point
- Catches issues single-shot misses

**Run:**
```bash
python exercise_3_multipass.py
```

**What to observe:**
- DRAFT: initial briefing (often too long, unbalanced)
- CRITIQUE: bullet list of specific issues (not a rewrite)
- REFINED: tighter, balanced, ≤120 words, addresses all points

**Key concepts:**
- Explicit standards: lead with most important, balance pos/neg, be specific, neutral tone, <120 words
- Critique doesn't rewrite - "Do NOT rewrite — only list issues"
- Refine addresses every bullet with concrete fixes
- Use for high-stakes output where quality matters

**Pattern:**
```python
# Standards
STANDARDS = "lead with most important; balance pos/neg; specific; neutral; <120 words"

# Draft
draft = ask(client, f"Write briefing from headlines: {headlines}")

# Critique (list issues, don't rewrite)
critique = ask(client,
    f"{STANDARDS}\nHeadlines: {headlines}\nDraft: {draft}\n"
    "List specific problems. Do NOT rewrite — only list issues.")

# Refine (address every point)
refined = ask(client,
    f"{STANDARDS}\nHeadlines: {headlines}\nDraft: {draft}\n"
    f"Critique: {critique}\n"
    "Rewrite to fix every point. Output only final briefing.")
```

## Key Takeaways

### Three Patterns, Three Trade-offs

| Pattern | When to use | Trade-off |
|---------|-------------|-----------|
| **Batches** | Overnight bulk, backfill | Latency for cost/scale |
| **Parallel** | Breaking news, real-time burst | Workers capped by rate limits |
| **Multi-pass** | Morning briefing, high-stakes | Quality for extra calls |

### Critical Distinctions

1. **Batches vs Real-time** — Batches make you wait (minutes to hours). Don't use for user-facing work.

2. **custom_id is essential** — Batch results arrive in completion order, not submission order. Tag every request.

3. **Threads, not processes** — I/O-bound work: GIL doesn't matter, threads have lower overhead.

4. **Critique must NOT rewrite** — If critique rewrites, you lose the separation. Keep it focused on judging.

5. **Multi-pass costs tokens** — Draft + critique + refine = 3 calls. Use where quality justifies cost.

## Reflection Questions

### Exercise 1
- When is the Message Batches API the right tool, and when is it wrong?
- Why does every request need a `custom_id`? What breaks if you match by order?
- Why poll with a deadline instead of waiting forever?

### Exercise 2
- Why threads (not processes or asyncio) for parallel Claude calls?
- What stops speedup from growing linearly with workers?
- How would you size the pool for production?

### Exercise 3
- Why split generate/critique/refine instead of one prompt that does all three?
- What breaks if you drop "Do NOT rewrite" from critique?
- When would you want a different model to run the critique?

## Files

```
Lab 4.3/
├── README.md                          # This file
├── requirements.txt                   # anthropic>=0.40.0, python-dotenv
├── .env.example                       # API key template
├── .gitignore                         # Python ignores
├── exercise_1_message_batches.py     # Batch processing (supports --fetch)
├── exercise_2_parallel.py            # ThreadPoolExecutor parallel processing
└── exercise_3_multipass.py           # Multi-pass draft→critique→refine
```

## Common Mistakes to Avoid

| Mistake | Why it matters and what to do instead |
|---------|--------------------------------------|
| Using batches for real-time work | Batches take minutes-hours. Use real-time calls or thread pool for anything synchronous. |
| Matching results by order, not custom_id | Batch results arrive in completion order. Tag with custom_id and join through it. |
| Polling forever with no deadline | Stuck batch hangs your script. Cap with deadline and print --fetch hint. |
| Cranking workers past rate limit | Beyond per-minute limit, workers just generate 429s. Start at 5, raise cautiously. |
| Asking critique to rewrite | Collapse generate+judge into one, lose separation value. Tell it "list issues, do NOT rewrite". |
| Self-review for high-stakes | Model that wrote draft is biased. For high-stakes, use fresh instance or different model. |

## Further Reading

- [Message Batches API Documentation](https://docs.anthropic.com/en/docs/build-with-claude/batch-processing)
- [Rate Limits](https://docs.anthropic.com/en/api/rate-limits)
- [Skilljar — Building with the Claude API](https://skilljar.anthropic.com/)

## Success Criteria

After completing this lab, you should be able to:

✓ Use Message Batches API for large offline workloads  
✓ Submit batch requests with custom_id and poll until ended  
✓ Implement parallel processing with ThreadPoolExecutor  
✓ Apply multi-pass review (draft → critique → refine)  
✓ Choose the right pattern for each job (batch/parallel/multi-pass)  
✓ Understand cost-vs-latency-vs-quality trade-offs
