# Lab 1.2: Controlling Execution - Hooks, Decomposition & Session State

## AI SOC Copilot for NorthGate Capital

This lab implements three critical production-grade agentic patterns for a Security Operations Center copilot:

1. **PostToolUse Hooks** - Guardrails between decision and execution
2. **Fixed vs Adaptive Decomposition** - Right structure for the right task
3. **Session State Management** - Long-running investigations that survive shift changes

---

## 🏗️ Project Structure

```
lab_1_2/
├── tool_hooks.py           # Ex 1: Hook engine (log/validate/block)
├── agent_with_hooks.py     # Ex 1: Live agentic loop with guardrails
├── decompose.py            # Ex 2: Fixed & adaptive task decomposition
├── session_manager.py      # Ex 3: Save/resume/fork/summarize
└── sessions/               # Created at runtime - session JSON files
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Verify Python 3 and Anthropic SDK
python3 --version
pip install "anthropic>=0.40.0"

# Verify API key is set
echo $ANTHROPIC_API_KEY
```

### Run All Exercises

```bash
# Exercise 1: Hook Chain (standalone, no API key needed)
python3 tool_hooks.py

# Exercise 1: Live Agent with Hooks (requires API key)
python3 agent_with_hooks.py

# Exercise 2: Fixed vs Adaptive Decomposition
python3 decompose.py

# Exercise 3: Session State Management
python3 session_manager.py
```

---

## 📋 Exercise Details

### Exercise 1: PostToolUse Hooks (~20 min)

**Objective:** Build deterministic guardrails that sit between the model's decision and actual side-effects.

**Files:**
- `tool_hooks.py` - Pure Python hook engine with three hooks:
  - `logging_hook`: Audit trail (never blocks)
  - `arg_validation_hook`: Catches malformed inputs
  - `protected_asset_hook`: Enforces business policy

- `agent_with_hooks.py` - Live SOC agent with tools:
  - `quarantine_host` - Isolate systems via EDR
  - `block_ip` - Add IPs to firewall deny-list
  - `disable_user` - Disable AD accounts
  - `query_siem` - Search security logs

**The Trap:**
The test alert instructs the agent to quarantine `trading-prod-01` (a protected trading server). The hook chain MUST block this action while allowing legitimate responses.

**Key Verification:**
- ✅ Hook blocks trading-prod-01 quarantine
- ✅ Agent receives BLOCKED-by-policy result
- ✅ Agent does NOT retry the blocked action
- ✅ Audit log records all attempts (allowed + blocked)

**Protected Assets:**
```python
PROTECTED_HOSTS = [
    "trading-prod-01", "trading-prod-02", "trading-prod-03",
    "market-data-relay-01", "ceo-laptop", "cfo-laptop", "ciso-laptop"
]

PROTECTED_IPS = [
    "198.51.100.10",  # Reuters
    "198.51.100.11",  # Bloomberg
    "192.0.2.55",     # Prime-broker API
    "192.0.2.56"      # Clearing-house webhook
]
```

---

### Exercise 2: Fixed vs Adaptive Decomposition (~15 min)

**Objective:** Choose the right decomposition pattern based on task certainty.

**Patterns:**

**FIXED (task is certain):**
```
fetch IoCs → enrich → publish
(same path every time)
```
Use when: Steps are known in advance (morning threat-intel digest)

**ADAPTIVE (task is uncertain):**
```
classify alert → branch by type
├─ phishing → playbook A
├─ malware → playbook B
├─ data_exfiltration → playbook C
└─ false_positive → close-out
```
Use when: Input determines the path (alert triage)

**Demo 1: Fixed Pipeline**
Three hard-coded steps that run the same way every morning:
1. Extract IoCs from overnight threat intel
2. Enrich against NorthGate asset inventory
3. Generate executive brief for SOC manager standup

**Demo 2: Adaptive Pipeline**
Six specialist playbooks (phishing, malware, lateral_movement, data_exfiltration, brute_force, false_positive). The classifier picks which one runs at runtime.

**Key Insight:**
- Fixed saves tokens and latency when steps are predictable
- Adaptive handles branching logic when path depends on input
- Don't use adaptive when you already know the steps

---

### Exercise 3: Session State Management (~15 min)

**Objective:** Long-running investigations that survive shift changes, support parallel hypotheses, and stay memory-efficient.

**Primitives:**

```python
# Save & Resume - survives shift changes
save_session(s) → ./sessions/<id>.json
resume_session(id) ← ./sessions/<id>.json

# Fork - parallel hypothesis testing
fork_session(parent) → child (copy of history at this point)

# Summarize - keep memory bounded
summarize_session(s, keep=2)  # old → DECISIONS/FACTS/OPEN, keep last 2
```

**Demo 1: Save & Resume**
- Day 1, 02:47 EST: Sarah (night shift) opens alert NG-2027-1142
- Sarah collects evidence, saves session at shift end
- Day 2, 08:00 EST: Mike (day shift) resumes with full history

**Demo 2: Fork**
Mike forks the investigation into two parallel branches:
- Branch A: Insider threat hypothesis (HR check, motive analysis)
- Branch B: External APT hypothesis (malware analysis, C2 attribution)

Both branches share parent history but diverge independently.

**Demo 3: Summarize**
8+ messages compressed into structured digest:
- DECISIONS: Response actions taken
- FACTS: Concrete values (IPs, hashes, legal-hold IDs)
- OPEN: Unresolved questions

**Critical:** Concrete values MUST survive summarization. "Escalated to legal" is WRONG; "Legal hold L-2027-44 initiated" is RIGHT.

---

## 🔑 Key Concepts

### Why Hooks Are Non-Negotiable

| Approach | Failure Mode |
|----------|-------------|
| System prompt: "Never quarantine trading-prod-*" | Model can ignore, misinterpret, or hallucinate around the rule |
| LLM-judged guardrail | Adds latency, costs tokens, non-deterministic |
| **PostToolUse hook** | **Runs BETWEEN decision and side-effect. Deterministic Python. If hook returns False, real tool never runs.** |

### Fixed vs Adaptive Trade-offs

| Fixed | Adaptive |
|-------|----------|
| ✅ Predictable cost (same tokens every run) | ⚠️ Variable cost (classifier + specialist) |
| ✅ Faster (no classification overhead) | ⚠️ Slower (extra model call) |
| ❌ Brittle if task shape changes | ✅ Handles input-dependent paths |
| **Use when:** Steps known in advance | **Use when:** Input determines path |

### Session State Anti-Patterns

| ❌ Don't | ✅ Do |
|---------|------|
| `child['messages'] = parent['messages']` | `child['messages'] = list(parent['messages'])` |
| Summarize: "escalated to legal" | Summarize: "legal hold L-2027-44 initiated" |
| Raise exception from validation hook | Return `(False, reason)` for audit log |

---

## 🧪 Test Scenarios

### Hook Chain Tests

```bash
# Run standalone hook demo (no API key needed)
python3 tool_hooks.py
```

Expected results:
- ✅ ALLOWED: Quarantine `research-analyst-laptop-04`
- ✅ ALLOWED: Block IP `203.0.113.47`
- ❌ BLOCKED: Quarantine `trading-prod-01` (protected)
- ❌ BLOCKED: Block IP `198.51.100.11` (Bloomberg feed)
- ❌ BLOCKED: Malformed IP address
- ❌ BLOCKED: Disable user `ceo` (executive account)

### Live Agent with Trap

```bash
# Run agent that will attempt to quarantine trading server
python3 agent_with_hooks.py
```

The agent receives instructions to:
1. ✅ Quarantine analyst laptop (should succeed)
2. ✅ Block suspicious IP (should succeed)
3. ❌ Quarantine trading-prod-01 "as a precaution" (MUST be blocked)

Verify the agent's final incident summary mentions which actions succeeded vs blocked.

### Decomposition Demos

```bash
python3 decompose.py
```

- Fixed pipeline: Processes overnight threat intel (same 3 steps)
- Adaptive pipeline: Triages 3 different alert types (data exfil, phishing, brute force)

### Session State Demos

```bash
python3 session_manager.py
```

Check the `./sessions/` directory afterward:
```bash
ls sessions/
# Should show multiple .json files (original + forks)
```

---

## 🎯 Learning Objectives

By completing this lab, you will be able to:

✅ **Implement PostToolUse hooks** that intercept every tool call between decision and execution

✅ **Choose between fixed and adaptive decomposition** based on task certainty

✅ **Manage long-running session state** via save/resume/fork/summarize

✅ **Build production-grade guardrails** for agents with dangerous tools

✅ **Design task decomposition** that matches structure to certainty

✅ **Persist investigation state** across shift changes and context resets

---

## 📊 Reflection Questions

### Exercise 1: Hooks

1. **Why is hook-level enforcement strictly safer than a system-prompt rule?**
   - System prompts can be ignored, misinterpreted, or jailbroken
   - Hooks run deterministic Python BEFORE the side-effect
   - If hook returns False, real tool never executes (period)

2. **What would change if `arg_validation_hook` raised an exception instead of returning False?**
   - Audit log wouldn't record the attempt
   - Error handling becomes messy (catch at run_tool level)
   - Loses the "reason" string for the analyst

3. **What asset-naming mistake could let a hostname slip through the protected_asset_hook?**
   - Current logic: `if protected in hostname` (substring match)
   - Attack: Name a malicious host `my-trading-prod-01-backup`
   - Fix: Use exact match or regex with word boundaries

### Exercise 2: Decomposition

1. **If you replaced the fixed digest with adaptive routing, what's the cost?**
   - Cost: Extra API call per step to decide next action
   - Latency: 3× model calls instead of 1 (classify each step)
   - Worth it when: Steps genuinely depend on prior results

2. **What's the failure mode if classifier silently picks false_positive for real data exfiltration?**
   - Critical alert gets closed without investigation
   - Detection: Monitor false_positive rate, review closed alerts
   - Fix: Add confidence scores, human-in-loop for borderline cases

3. **Could the morning digest be partially adaptive?**
   - Yes: Same 3 steps, but step 2 branches based on what step 1 found
   - Example: If IoCs include ransomware → escalate immediately

### Exercise 3: Session State

1. **Why must the summarizer never drop concrete values?**
   - "Escalated to legal" without hold ID → analyst can't find the case
   - Lost IP/hostname → can't resume containment actions
   - A digest that loses concrete values is worse than no digest

2. **What bug appears if you skip the copy when forking?**
   - Both branches share the SAME list object
   - Adding message to branch A shows up in branch B
   - Silent data corruption - hard to debug

3. **What extra step needed if messages[] contained SDK objects (not strings)?**
   - SDK content objects aren't JSON-serializable
   - Must convert to dict before json.dump()
   - Or use `anthropic.lib.utils.serialize()` helper

---

## 🔗 Further Reading

- **Claude Code 101** (Skilljar): Hooks, Context Management, Workflow
- **Introduction to Subagents** (Skilljar): Designing Effective Subagents
- **Anthropic API Docs**: Tool Use & Agentic Loops (docs.anthropic.com/agents)

---

## 📝 Notes

### API Key Setup

Your API key should be in the environment:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Model Selection

- `tool_hooks.py`: No API calls (pure Python demo)
- `agent_with_hooks.py`: claude-opus-4-6 (multi-tool coordination)
- `decompose.py`: claude-haiku-4-5-20251001 (one-shot calls)
- `session_manager.py`: claude-haiku-4-5-20251001 (summarization)

### Cost Estimates

- Exercise 1 (agent_with_hooks): ~15K tokens (~$0.10)
- Exercise 2 (decompose): ~8K tokens (~$0.01)
- Exercise 3 (session_manager): ~5K tokens (~$0.01)

**Total lab cost:** ~$0.12 per run

---

## ✅ Completion Checklist

- [ ] All three Python files run without errors
- [ ] Exercise 1: Hook blocks trading-prod-01 quarantine
- [ ] Exercise 1: Audit log shows both allowed and blocked attempts
- [ ] Exercise 2: Fixed pipeline generates executive brief
- [ ] Exercise 2: Adaptive pipeline routes alerts to correct playbooks
- [ ] Exercise 3: Session survives save/resume cycle
- [ ] Exercise 3: Fork creates independent branches
- [ ] Exercise 3: Summarizer preserves concrete values
- [ ] `./sessions/` directory contains JSON files
- [ ] All reflection questions answered

---

## 🎓 Scenario Summary

**You are building Sentinel**, the AI copilot for NorthGate Capital's Security Operations Center.

**The Challenge:**
- SOC ingests alerts from CrowdStrike, Splunk, M365 Defender every minute
- Manual triage is slow and inconsistent
- Wrong actions during market hours have cost seven figures in the past

**Your Solution:**
1. **Hooks** - Prevent the copilot from damaging production (trading servers, market-data feeds)
2. **Decomposition** - Handle both routine work (daily digest) and exceptional work (alert triage)
3. **Session State** - Investigations span days, survive shift changes, support parallel hypotheses

**Live Test Alert:**
```
Alert ID: NG-2027-1142
Severity: HIGH
Asset: research-analyst-laptop-04 (Maya Iyer, Sr. Equity Research)
Event: 8.3 GB exfiltrated to 203.0.113.47 (Singapore) at 02:47 EST
Context: Outside business hours, no VPN, owner left office at 18:22 EST
```

This alert is the running example across all three exercises.

---

**Built for CCA-F Module 1 | AI Pioneers Lab 1.2**
