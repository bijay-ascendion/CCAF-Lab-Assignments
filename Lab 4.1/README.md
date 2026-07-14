# Lab 4.1: Precision Prompting - Explicit Criteria & Few-Shot Consistency

**Module:** M4 — Prompt Engineering & Structured Output  
**Duration:** ~40 minutes  
**Focus:** Explicit Criteria, Few-Shot Examples & Generalization

## Overview

This lab builds precision into a content moderation classifier using prompting techniques alone:
1. **Explicit Criteria (Ex 1):** Define exactly what each label means to cut false positives
2. **Few-Shot Examples (Ex 2):** Show the exact output format to lock consistency
3. **Generalization (Ex 3):** Add principles so behavior extends to unseen edge cases

Each exercise demonstrates a specific prompting pattern that makes classification more accurate, parseable, and robust to context-heavy scenarios.

## Scenario

You're building the triage step for a community platform's **Trust & Safety queue**. Reported posts must be routed to one of three actions:

- **REMOVE** → unambiguous violation: doxxing, credible threat, clearly illegal content
- **REVIEW** → needs a human: likely spam, borderline harassment, ambiguous threats
- **ALLOW** → rude/blunt/off-topic but not a violation; strong disagreement, sarcasm

**The challenge:** A vague prompt over-fires REMOVE, producing wrongful takedowns. Your job is to make the classifier precise with prompting alone — no fine-tuning, no extra tooling.

## Setup

### Prerequisites

- Python 3.9+
- Anthropic SDK: `pip install "anthropic>=0.40.0"`
- API Key: Set `ANTHROPIC_API_KEY` environment variable

### Installation

1. Navigate to the lab directory:
```bash
cd "Lab 4.1"
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

### Exercise 1: Explicit Criteria to Cut False Positives (~15 min)

**Goal:** Replace vague labels with testable definitions to reduce wrongful "remove" calls.

**What it demonstrates:**
- VAGUE prompt: "remove, review, or allow" (undefined → over-fires)
- EXPLICIT prompt: Clear criteria + tie-break rule (ambiguous cases → review)

**Run:**
```bash
python exercise_1_explicit_criteria.py
```

**What to observe:**
- How many wrongful "remove" calls with vague vs. explicit prompts
- The explicit prompt should drive false positives toward zero
- Same model, same test cases — only the criteria changed

**Key concepts:**
- Define each label with concrete, testable boundaries
- Add a tie-break rule: "if unsure between remove and review, choose review"
- Measure the specific failure that matters (false positives), not just accuracy

### Exercise 2: Few-Shot Examples to Lock Consistent Output (~12 min)

**Goal:** Use examples to pin the exact output format (ACTION | rationale).

**What it demonstrates:**
- ZERO-SHOT: Describes the format → inconsistent output
- FEW-SHOT: Shows 3 labeled examples → strict format compliance

**Run:**
```bash
python exercise_2_few_shot.py
```

**What to observe:**
- Format compliance measured with strict regex: `^(REMOVE|REVIEW|ALLOW) \| .+`
- Zero-shot may decide correctly but in unparseable shapes
- Few-shot locks casing, separator, rationale length reliably

**Key concepts:**
- Show the format, don't just describe it
- One example per label (REMOVE, ALLOW, REVIEW)
- Measure format compliance independently from decision correctness

### Exercise 3: Generalizing Beyond the Examples Shown (~13 min)

**Goal:** Add principles so the model handles unseen, context-heavy edge cases correctly.

**What it demonstrates:**
- Examples teach FORMAT, not every possible situation
- Principles teach INTENT (private vs. public data, context interpretation)
- Tests on 4 edge cases that hinge on distinctions the examples never showed

**Run:**
```bash
python exercise_3_generalization.py
```

**What to observe:**
- Edge cases: public press number (allow), private address "as a joke" (remove), playful threat (review), boring essay (allow)
- Without principles: examples can't cover every context
- With principles: boundary generalizes to unseen cases

**Key concepts:**
- State the distinctions: private vs. public, intent rules, tie-break
- Principles block = short statement of intent above examples
- Robust parsing: extract action from ACTION | line (handles preamble)

## Key Takeaways

1. **Define the label before you apply it** — Vague labels like "remove" over-fire because the boundary is undefined. Explicit, testable criteria cut false positives.

2. **Show the output shape, don't just describe it** — Instructions give inconsistent formats. A few examples in the exact target shape lock casing, separator, and structure.

3. **State the intent so behavior generalizes** — Examples can't enumerate every case. A short principles block teaches the boundary for context-heavy scenarios.

4. **Measure what matters** — Track the specific failure (wrongful removes) separately from overall accuracy. Cost of errors is asymmetric.

5. **Three layers of precision:**
   - **Criteria** fix the decision (what each label means)
   - **Examples** fix the format (parseable output shape)
   - **Principles** fix the intent (generalization to unseen cases)

## Reflection Questions

### Exercise 1
- Why does a vague "remove / review / allow" prompt over-fire remove?
- The explicit prompt says "if unsure between remove and review, choose review." Why bake in that tie-breaker, and what cost asymmetry does it encode?
- Why measure the false-"remove" count separately from overall accuracy?

### Exercise 2
- The instruction already says "respond as ACTION | rationale." Why do few-shot examples lock the format better than instructions alone?
- How many examples should you use, and what should they cover?
- Why measure format compliance independently from decision correctness?

### Exercise 3
- What do the principles add over examples alone?
- The "public press number = allow" but "private address as a joke = remove" cases hinge on context. How do principles get them right?
- Why does robust parsing (regex on ACTION | line) matter more than split("|")[0]?

## Files

```
Lab 4.1/
├── README.md                          # This file
├── requirements.txt                   # anthropic>=0.40.0, python-dotenv
├── .env.example                       # API key template
├── .gitignore                         # Python ignores
├── exercise_1_explicit_criteria.py   # Vague vs explicit criteria
├── exercise_2_few_shot.py            # Zero-shot vs few-shot format
└── exercise_3_generalization.py      # Principles for edge cases
```

## Common Mistakes to Avoid

| Mistake | Why it matters and what to do instead |
|---------|--------------------------------------|
| Using a label without defining it | "Remove" means whatever the model guesses, so it over-fires. Give each action a testable definition and a tie-break rule. |
| Judging the prompt on accuracy alone | Accuracy can hide errors clustered in the costly direction. Track the specific failure (wrongful removes) you care about. |
| Describing the format instead of showing it | Instructions give inconsistent shapes. Demonstrate the exact ACTION \| rationale format with a few examples. |
| Over-fitting to the examples | Examples can't cover every case. Add a short principles block so the boundary generalizes to unseen, context-heavy reports. |
| Scoring with split("\|")[0] | A preamble before the line mis-scores a correct answer. Extract the action with a regex on the ACTION \| line. |

## Further Reading

- [Claude Prompt Engineering Overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [Being Clear and Direct](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct)
- [Providing Examples (Few-Shot)](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/provide-examples)
- [Skilljar — Building with the Claude API](https://skilljar.anthropic.com/)

## Success Criteria

After completing this lab, you should be able to:

✓ Write explicit classification criteria that reduce false positives  
✓ Use few-shot examples to lock consistent, parseable output formats  
✓ Add principles that help models generalize to unseen edge cases  
✓ Measure the right metrics (false positives, format compliance) not just accuracy  
✓ Build precise classifiers with prompting alone — no fine-tuning needed
