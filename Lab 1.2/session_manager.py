"""
Exercise 3: Session State Management
Resume / Fork / Summarize - long-running SOC investigations that survive
shift changes, support parallel hypotheses, and keep memory bounded.
"""

import os
import json
import uuid
from typing import Dict, List
import anthropic

# Absolute path to sessions directory - works regardless of where you run from
SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")

# Initialize Anthropic client for summarization
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# ═══════════════════════════════════════════════════════════════════════════
# Session Primitives
# ═══════════════════════════════════════════════════════════════════════════

def new_session() -> Dict:
    """
    Create a fresh session with a unique ID.
    Session shape: {id, parent_id, messages, summary}
    """
    return {
        "id": uuid.uuid4().hex[:6],  # Short unique identifier
        "parent_id": None,
        "messages": [],
        "summary": ""
    }


def add_user(session: Dict, text: str):
    """Add a user message to the session history."""
    session["messages"].append({"role": "user", "content": text})


def add_assistant(session: Dict, text: str):
    """Add an assistant message to the session history."""
    session["messages"].append({"role": "assistant", "content": text})


def save_session(session: Dict) -> str:
    """
    Persist session to disk as JSON.
    Returns the file path.
    """
    # Create sessions directory if it doesn't exist
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    # Write to file
    file_path = os.path.join(SESSIONS_DIR, f"{session['id']}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)

    msg_count = len(session["messages"])
    print(f"[SAVE] Saved session {session['id']} to {file_path} ({msg_count} messages)")

    return file_path


def resume_session(session_id: str) -> Dict:
    """
    Load a session from disk.
    Raises FileNotFoundError if the session doesn't exist.
    """
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Session '{session_id}' not found.\n"
            f"Expected file: {file_path}\n"
            f"Available sessions: {os.listdir(SESSIONS_DIR) if os.path.exists(SESSIONS_DIR) else '(none)'}"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        session = json.load(f)

    msg_count = len(session["messages"])
    print(f"[LOAD] Resumed session {session_id} from {file_path} ({msg_count} messages)")

    return session


def fork_session(parent: Dict) -> Dict:
    """
    Create a child session that starts with a COPY of the parent's history.
    Both branches can diverge independently from this point.

    CRITICAL: Must copy the messages list, not share a reference.
    """
    child = {
        "id": uuid.uuid4().hex[:6],
        "parent_id": parent["id"],  # Track lineage
        "messages": list(parent["messages"]),  # COPY, not alias
        "summary": parent["summary"]
    }

    print(f"[FORK] Forked session {parent['id']} -> {child['id']} (copied {len(child['messages'])} messages)")

    return child


def summarize_session(session: Dict, keep_recent: int = 2):
    """
    Compress older messages into a structured digest to keep the session small.
    Replaces old messages with a summary; keeps only the last N messages.

    The summarizer is instructed to NEVER drop concrete values:
    IPs, hostnames, usernames, hashes, alert IDs, legal-hold IDs, etc.
    """
    if len(session["messages"]) <= keep_recent:
        print(f"[WARN]  Session has only {len(session['messages'])} messages - skipping summarization")
        return

    # Split into older block (to summarize) and recent slice (to keep)
    older_messages = session["messages"][:-keep_recent]
    recent_messages = session["messages"][-keep_recent:]

    # Build transcript from older messages
    transcript_lines = []
    for msg in older_messages:
        role = msg["role"].upper()
        content = msg["content"]
        if isinstance(content, list):
            # Handle tool results
            content = str(content)
        transcript_lines.append(f"{role}: {content[:500]}")  # Truncate for summarizer

    transcript = "\n\n".join(transcript_lines)

    # Call Claude to summarize
    print(f"[COMPRESS]  Summarizing {len(older_messages)} older messages (keeping {keep_recent} recent)...")

    summarizer_system = """You are summarizing a SOC investigation for shift handoff.
Output EXACTLY three sections:

DECISIONS:
- List every response action taken (quarantined hosts, blocked IPs, disabled accounts)

FACTS:
- List every concrete value: IPs, hostnames, usernames, hashes, alert IDs, legal-hold IDs, timestamps
- NEVER generalize concrete values - "escalated to legal" is WRONG, "legal hold L-2027-44 initiated" is RIGHT

OPEN:
- List every question or task that is still unresolved

CRITICAL: Concrete values must survive intact. A digest that loses an IP or legal-hold ID is worse than no digest."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=summarizer_system,
            messages=[{"role": "user", "content": f"Summarize this investigation transcript:\n\n{transcript}"}]
        )

        summary_text = response.content[0].text.strip()

        # Update session - replace old messages with summary, keep recent
        session["summary"] = summary_text
        session["messages"] = recent_messages

        print(f"[OK] Summarized into {len(summary_text)} chars, kept {len(recent_messages)} recent messages")

    except Exception as e:
        print(f"[FAIL] Summarization failed: {e}")
        print("   Keeping full message history")


# ═══════════════════════════════════════════════════════════════════════════
# DEMO - Save / Resume / Fork / Summarize
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*70)
    print("Exercise 3: Session State Management")
    print("="*70)

    # ─────────────────────────────────────────────────────────────────────
    # Demo 1: Save & Resume - Shift Change
    # ─────────────────────────────────────────────────────────────────────

    print("\n" + "─"*70)
    print("Demo 1: Save & Resume (Shift Change)")
    print("─"*70 + "\n")

    # Day 1, 02:47 EST - Sarah Chen (Tier-1, night shift) opens the alert
    print("[NIGHT] Day 1, 02:47 EST - Sarah Chen (Tier-1, Night Shift)")
    session = new_session()

    add_user(session, """Alert NG-2027-1142 received:
research-analyst-laptop-04 transferred 8.3 GB to 203.0.113.47 (Singapore) at 02:47 EST.
Owner (Maya Iyer) left office at 18:22 EST. No VPN session.""")

    add_assistant(session, """Initial triage complete:
1. Quarantined research-analyst-laptop-04 via EDR
2. Blocked destination IP 203.0.113.47 at firewall
3. SIEM query shows first connection at 02:14 EST
4. Leading hypothesis: compromised laptop, possible data exfiltration

Next steps: memory image, HR check on owner.""")

    add_user(session, "Memory image captured. Hash: a3f5e2d8c9b1f4e7a6d3c8b5e9f2a1d4")

    add_assistant(session, """Memory analysis findings:
- Process: firefox.exe spawned suspicious child processes
- Persistence: scheduled task created at 02:10 EST
- Network: TLS connection to 203.0.113.47:443 (encrypted channel)

Recommendation: Escalate to Tier-2 for malware analysis. Possible APT.""")

    # Save session - shift ending
    print("\n[SAVE] Sarah's shift ending - saving session...")
    session_path = save_session(session)
    session_id = session["id"]

    # Simulate shift change - delete the session object
    print("[SHIFT] Shift change - session object deleted from memory...")
    del session

    # Day 2, 08:00 EST - Mike Torres (Tier-2, day shift) resumes
    print("\n[DAY]  Day 2, 08:00 EST - Mike Torres (Tier-2, Day Shift)")
    print(f"[LOAD] Mike resumes session {session_id}...\n")

    resumed_session = resume_session(session_id)

    print(f"[OK] Full history available: {len(resumed_session['messages'])} messages")
    print("[OK] Mike can continue from where Sarah left off\n")

    # ─────────────────────────────────────────────────────────────────────
    # Demo 2: Fork - Parallel Hypothesis Testing
    # ─────────────────────────────────────────────────────────────────────

    print("\n" + "─"*70)
    print("Demo 2: Fork (Parallel Hypothesis Testing)")
    print("─"*70 + "\n")

    print("[FORK] Mike decides to test two hypotheses in parallel:\n")

    # Branch A - Insider threat hypothesis
    branch_a = fork_session(resumed_session)
    print("   Branch A: Insider Threat Hypothesis")

    add_user(branch_a, "Check: Did Maya Iyer have any recent HR issues? Departures planned?")
    add_assistant(branch_a, """HR records checked:
- No disciplinary actions
- No resignation on file
- Recent performance review: exceeds expectations
- BUT: Noticed she applied for a competitor role (found via LinkedIn activity)

Hypothesis strength: WEAK. No clear insider motive.""")

    save_session(branch_a)

    # Branch B - External APT hypothesis
    branch_b = fork_session(resumed_session)
    print("   Branch B: External APT Hypothesis")

    add_user(branch_b, "Analyze memory image for APT TTPs. Check for known malware families.")
    add_assistant(branch_b, """Malware analysis complete:
- Memory image hash matches known Cobalt Strike beacon variant
- C2 server 203.0.113.47 appears in CISA APT29 intel feed
- Persistence mechanism: scheduled task + registry run key
- Exfiltration: 8.3 GB sent via HTTPS POST to C2

Hypothesis strength: STRONG. High-confidence APT compromise.""")

    save_session(branch_b)

    print(f"\n[OK] Both branches share parent {resumed_session['id']}")
    print(f"[OK] Branch A: {branch_a['id']} (insider hypothesis)")
    print(f"[OK] Branch B: {branch_b['id']} (APT hypothesis)")
    print(f"[OK] Each can diverge independently\n")

    # ─────────────────────────────────────────────────────────────────────
    # Demo 3: Summarize - Keep Memory Bounded
    # ─────────────────────────────────────────────────────────────────────

    print("\n" + "─"*70)
    print("Demo 3: Summarize (Keep Memory Bounded)")
    print("─"*70 + "\n")

    print("[INFO] Building a long investigation history (8+ messages)...\n")

    long_session = new_session()

    # Pile up evidence-collection turns
    add_user(long_session, "Alert NG-2027-1142: 8.3 GB exfil to 203.0.113.47")
    add_assistant(long_session, "Quarantined laptop, blocked IP. Collecting evidence.")

    add_user(long_session, "Memory image captured. Hash: a3f5e2d8c9b1f4e7a6d3c8b5e9f2a1d4")
    add_assistant(long_session, "Hash matches Cobalt Strike. Initiating malware analysis.")

    add_user(long_session, "SIEM query: first beacon at 02:14 EST, exfil at 02:47 EST")
    add_assistant(long_session, "33-minute dwell time. Fast exfil after initial compromise.")

    add_user(long_session, "Legal hold initiated: L-2027-44. Preserving all evidence.")
    add_assistant(long_session, "Legal hold L-2027-44 confirmed. All logs frozen.")

    add_user(long_session, "IR team escalation: APT29 attribution confirmed via C2 IOCs")
    add_assistant(long_session, "APT29 confirmed. Escalating to executive briefing.")

    add_user(long_session, "What files were accessed before exfiltration?")
    add_assistant(long_session, "File access logs show: research_models/, client_data/. PII exposed.")

    print(f"Before summarization: {len(long_session['messages'])} messages\n")

    # Summarize - keep last 2 messages
    summarize_session(long_session, keep_recent=2)

    print(f"\nAfter summarization: {len(long_session['messages'])} messages")
    print(f"Summary length: {len(long_session['summary'])} characters\n")

    print("[SUMMARY] Summary Content:")
    print("─"*70)
    print(long_session["summary"])
    print("─"*70 + "\n")

    # Verify concrete values survived
    summary_lower = long_session["summary"].lower()
    critical_values = [
        ("203.0.113.47", "Exfil destination IP"),
        ("a3f5e2d8c9b1", "Memory image hash (partial)"),
        ("l-2027-44", "Legal hold ID"),
        ("02:14", "Initial beacon time"),
        ("apt29", "Threat actor")
    ]

    print("[CHECK] Verification: Did concrete values survive summarization?")
    for value, description in critical_values:
        if value in summary_lower:
            print(f"   [PASS] {description}: {value}")
        else:
            print(f"   [FAIL] {description}: {value} - MISSING!")

    # ─────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
[OK] Save/Resume: Sessions survive shift changes (saved to ./sessions/)
[OK] Fork: Parallel hypothesis testing - both branches share parent history
[OK] Summarize: Long investigations stay bounded; concrete values preserved

[SUMMARY] Key Insight:
   Session state must outlive the conversation.
   Concrete values (IPs, hashes, IDs) must survive every summarization.
   Fork must COPY messages, not alias them (or branches merge silently).
""")

    print(f"\n[FILES] Session files written to: {SESSIONS_DIR}")
    if os.path.exists(SESSIONS_DIR):
        files = os.listdir(SESSIONS_DIR)
        print(f"   {len(files)} session(s): {', '.join(files)}")
