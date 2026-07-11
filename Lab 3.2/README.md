# Lab 3.2 — Targeted Behavior (NorthPeak Services Monorepo)

Starter project for **Lab 3.2: Path-Specific Rules & Plan Mode Workflows**.
Everything you need is already here — your job in the lab is to make Claude
Code's caution scale with the risk of each module.

## What's in here

    CLAUDE.md                       general rules + how path-specific rules work
    src/auth/CLAUDE.md              SECURITY-CRITICAL rules for auth/
    src/orders/CLAUDE.md            order conventions for orders/
    src/payments/CLAUDE.md          MONEY-CRITICAL rules for payments/
    .claude/agents/explorer.md      read-only explorer subagent (Read, Grep, Glob)
    src/auth/tokens.py              verify_token (strict) + deprecated verify_token_v1
    src/orders/service.py           place_order (still calls verify_token_v1)
    src/payments/charges.py         charge (still calls verify_token_v1)
    src/tests/test_smoke.py         pytest suite (4 tests, all green)

The suite starts at 4 tests and grows as you work: Exercise 1 adds one
(-> 5), the Exercise 2 migration adds none (still 5), and Exercise 3 adds
one (-> 6).

## Setup (do this before the session)

1. Get this bundle onto your Blue Labs VM and enter it.
2. Create a virtual environment and install the test dependency:

       python -m venv .venv && source .venv/bin/activate
       # Windows: .venv\Scripts\activate
       pip install -r requirements.txt

3. Confirm the suite is green:

       pytest -q          # expect: 4 passed

4. Start Claude Code **from this folder** so it finds the root CLAUDE.md and the
   per-module ones under src/:

       claude

   The first time, Claude Code will ask you to sign in — follow the prompt.

This project is already a git repository with a committed baseline, so you can
review your changes with `git diff` or undo an experiment with `git restore`.

## Exercise Summaries

### Exercise 1: Path-Specific Rules (Completed)

Demonstrated how `CLAUDE.md` rules scope to specific paths:

- **Added `count_items()` helper** to `src/orders/service.py` - clean change under 
  low-stakes path with standard rules
- **Refused to weaken auth check** in `src/auth/tokens.py` - security-weakening 
  request was challenged due to SECURITY-CRITICAL rules in `src/auth/CLAUDE.md`
- **Key insight**: Same type of request handled differently based on path-specific 
  rule strictness

**Result**: 5 tests passing (added `test_count_items`)

### Exercise 2: Plan Mode for Multi-File Migration (Completed)

Migrated all callers from deprecated `verify_token_v1` to stricter `verify_token`:

- **Updated `src/orders/service.py`** - changed import and function call
- **Updated `src/payments/charges.py`** - changed import and function call  
- **Removed deprecated function** from `src/auth/tokens.py` - cleaned up dead code
- **Key insight**: Plan-first approach ensures systematic migration across multiple 
  files without missing call sites

**Result**: 5 tests still passing (migration adds no new tests, existing token passes 
stricter check)

### Exercise 3: Explorer Subagent (Completed)

Used read-only explorer to survey payments module before making changes:

- **Explored `src/payments/`** - subagent reported files, API, dependencies, and 
  MONEY-CRITICAL risks without making any edits
- **Added $10,000 limit validation** to `charge()` with proper error handling
- **Added `test_charge_exceeds_limit()`** - tests both success and rejection cases 
  per MONEY-CRITICAL rules
- **Key insight**: Exploring unfamiliar code first provides context about 
  dependencies, risks, and rules

**Result**: 6 tests passing (added `test_charge_exceeds_limit`)

### Final Status

✅ All exercises complete  
✅ 6 tests passing  
✅ 4 files modified (auth, orders, payments, tests)  
✅ Demonstrated: path-specific rules, plan mode, and explorer subagent
