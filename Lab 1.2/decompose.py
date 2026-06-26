"""
Exercise 2: Fixed vs Adaptive Decomposition
Two patterns for multi-step SOC tasks:
- FIXED: Same steps every time (morning threat-intel digest)
- ADAPTIVE: Branch based on input (alert triage router)
"""

import os
import json
import anthropic

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def ask_claude(system: str, user: str, max_tokens: int = 1024, model: str = "claude-haiku-4-5-20251001") -> str:
    """
    Shared helper - one-shot Claude call that returns text response.
    Used by both fixed and adaptive pipelines.
    """
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return response.content[0].text.strip()


# ═══════════════════════════════════════════════════════════════════════════
# FIXED DECOMPOSITION - Morning Threat Intel Digest
# ═══════════════════════════════════════════════════════════════════════════

def run_fixed_intel_digest(overnight_feed: str, asset_inventory: str) -> dict:
    """
    Fixed three-step pipeline that runs the same way every morning:
    1. Extract IoCs from overnight threat intel
    2. Enrich - match IoCs against NorthGate's asset inventory
    3. Executive brief - three-bullet summary for SOC manager standup

    The steps are HARD-CODED because they never change.
    """
    print("\n" + "="*70)
    print("FIXED DECOMPOSITION: Morning Threat Intel Digest")
    print("="*70 + "\n")

    # Step 1 - Extract IoCs
    print("Step 1/3: Extracting Indicators of Compromise...")
    ioc_system = """Extract every indicator of compromise as a JSON list of objects.
Each object must have: type (ip/hash/domain/cve), value (the indicator), context (brief threat description).
Return ONLY the JSON array, no other text."""

    iocs_json = ask_claude(ioc_system, overnight_feed, max_tokens=2048)
    print(f"[OK] Extracted IoCs:\n{iocs_json[:200]}...\n")

    # Step 2 - Enrich against asset inventory
    print("Step 2/3: Enriching against NorthGate asset inventory...")
    enrich_system = """You are a threat analyst at NorthGate Capital.
Given a list of IoCs and our asset inventory, identify every IoC that matches something we own or use.
Return one bullet point per match: [IoC] matches [asset] - [risk description]"""

    enrich_user = f"""IoCs from overnight feed:
{iocs_json}

NorthGate Asset Inventory:
{asset_inventory}

List every IoC that matches our environment:"""

    matches = ask_claude(enrich_system, enrich_user, max_tokens=1536)
    print(f"[OK] Matches:\n{matches[:300]}...\n")

    # Step 3 - Executive brief
    print("Step 3/3: Generating executive brief for 08:00 standup...")
    brief_system = """You are preparing a morning brief for the SOC manager.
Write exactly three bullet points summarizing the threats that affect NorthGate.
Each bullet must: name the asset, describe the threat, recommend a specific next action.
Be concise - the manager has 2 minutes."""

    brief_user = f"""Overnight IoCs:
{iocs_json}

Matches against our assets:
{matches}

Write the three-bullet executive brief:"""

    exec_brief = ask_claude(brief_system, brief_user, max_tokens=1024)
    print(f"[OK] Executive Brief:\n{exec_brief}\n")

    return {
        "iocs": iocs_json,
        "matches": matches,
        "exec_brief": exec_brief
    }


# ═══════════════════════════════════════════════════════════════════════════
# ADAPTIVE DECOMPOSITION - Alert Triage Router
# ═══════════════════════════════════════════════════════════════════════════

# Six specialist playbooks - each is a system prompt for that incident type
TRIAGE_BRANCHES = {
    "phishing": """You are a phishing specialist at NorthGate Capital SOC.
Playbook: (1) Identify the sender and all recipients, (2) Check if any links were clicked or attachments opened,
(3) Quarantine the email from all mailboxes, (4) Disable compromised accounts, (5) Escalate to Tier-2 if credentials entered.
Analyze the alert and execute the playbook.""",

    "malware": """You are a malware analyst at NorthGate Capital SOC.
Playbook: (1) Quarantine the infected host immediately, (2) Collect memory image and process tree,
(3) Extract IoCs (hashes, C2 domains), (4) Check for lateral movement, (5) Escalate to IR team if ransomware detected.
Analyze the alert and execute the playbook.""",

    "lateral_movement": """You are a lateral movement specialist at NorthGate Capital SOC.
Playbook: (1) Identify source and destination hosts, (2) Check for credential theft (Mimikatz, pass-the-hash),
(3) Quarantine both systems, (4) Force password reset for compromised accounts, (5) Hunt for additional compromised hosts.
Analyze the alert and execute the playbook.""",

    "data_exfiltration": """You are a data exfiltration specialist at NorthGate Capital SOC.
Playbook: (1) Block the destination IP at the firewall, (2) Quarantine the source host, (3) Identify what data was accessed,
(4) Initiate legal hold if PII/PCI/material non-public info involved, (5) Notify legal and compliance teams immediately.
Analyze the alert and execute the playbook.""",

    "brute_force": """You are a brute-force attack specialist at NorthGate Capital SOC.
Playbook: (1) Block the source IP, (2) Check if any accounts were compromised, (3) Force MFA enrollment for targeted accounts,
(4) Review authentication logs for successful logins from suspicious IPs, (5) Escalate if privileged accounts targeted.
Analyze the alert and execute the playbook.""",

    "false_positive": """You are a SOC analyst reviewing a potential false positive.
Playbook: (1) Document why this is likely benign, (2) Check if it matches known false-positive patterns,
(3) Recommend tuning the detection rule to reduce noise, (4) Close the alert with detailed justification.
Analyze the alert and provide your assessment."""
}


def classify_alert(alert_text: str) -> str:
    """
    Classifier step - determine which specialist playbook to route to.
    Returns one of six labels: phishing, malware, lateral_movement,
    data_exfiltration, brute_force, false_positive.
    """
    classifier_system = f"""You are a SOC alert classifier.
Read the alert and return ONLY ONE of these labels (lowercase, no other text):
phishing
malware
lateral_movement
data_exfiltration
brute_force
false_positive

Reply with ONLY the label."""

    label = ask_claude(classifier_system, alert_text, max_tokens=50).strip().lower()

    # Validation - fallback to safe default if label is unknown
    if label not in TRIAGE_BRANCHES:
        print(f"[WARN]  Unknown label '{label}' - falling back to false_positive")
        label = "false_positive"

    return label


def run_adaptive_triage(alert_text: str) -> dict:
    """
    Adaptive pipeline - classify first, then route to the specialist playbook.
    The branch is picked at RUNTIME based on the alert content.
    """
    print("\n" + "="*70)
    print("ADAPTIVE DECOMPOSITION: Alert Triage Router")
    print("="*70 + "\n")

    # Step 1 - Classify
    print("Step 1: Classifying alert type...")
    branch = classify_alert(alert_text)
    print(f"[OK] Classification: {branch.upper()}\n")

    # Step 2 - Route to specialist
    print(f"Step 2: Routing to {branch} playbook...")
    specialist_prompt = TRIAGE_BRANCHES[branch]
    answer = ask_claude(specialist_prompt, alert_text, max_tokens=2048)
    print(f"[OK] Specialist Response:\n{answer[:500]}...\n")

    return {
        "branch": branch,
        "answer": answer
    }


# ═══════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*70)
    print("Exercise 2: Fixed vs Adaptive Decomposition")
    print("="*70)

    # ─────────────────────────────────────────────────────────────────────
    # Demo 1: Fixed Pipeline - Morning Threat Intel Digest
    # ─────────────────────────────────────────────────────────────────────

    overnight_feed = """
CISA Alert AA24-123A: APT29 Targeting Financial Services
IoCs identified:
- IP: 198.51.100.99 (C2 server, Russia-based ASN)
- Hash: a3f5e2d8c9b1f4e7a6d3c8b5e9f2a1d4 (Cobalt Strike beacon)
- Domain: secure-banking-update[.]com (phishing domain)
- CVE-2024-1234: Zero-day in Citrix Gateway (actively exploited)

Threat: APT29 spear-phishing campaigns targeting finance sector employees.
Delivers malware via weaponized Excel attachments. Post-compromise: credential theft, lateral movement.
"""

    asset_inventory = """
NorthGate Capital Asset Inventory (relevant excerpt):
- Citrix Gateway: citrix.northgate.com (version 14.2 - VULNERABLE to CVE-2024-1234)
- 45 Bloomberg terminals (connect to 198.51.100.11)
- Trading servers: trading-prod-01, trading-prod-02, trading-prod-03
- VPN concentrator: 203.0.113.10
- Email: Microsoft 365 with ATP
"""

    digest_result = run_fixed_intel_digest(overnight_feed, asset_inventory)

    # ─────────────────────────────────────────────────────────────────────
    # Demo 2: Adaptive Pipeline - Alert Triage on 3 Different Alert Types
    # ─────────────────────────────────────────────────────────────────────

    # Alert 1: Data exfiltration (the live test alert from the lab)
    alert_1 = """
Alert ID: NG-2027-1142
Severity: HIGH
Source: EDR (CrowdStrike Falcon)
Time: 02:47 EST
Asset: research-analyst-laptop-04
Owner: Maya Iyer, Sr. Equity Research
Event: Outbound transfer of 8.3 GB to external IP 203.0.113.47 (Singapore, AS65000)
Context: Transfer outside business hours; no active VPN; owner left office at 18:22 EST.
"""

    result_1 = run_adaptive_triage(alert_1)

    # Alert 2: Phishing
    alert_2 = """
Alert ID: NG-2027-1155
Severity: MEDIUM
Source: Microsoft 365 Defender
Time: 09:14 EST
Asset: Email system
Event: Suspected phishing email delivered to 23 users
Subject: "Urgent: Update your benefits enrollment by EOD"
Sender: hr-benefits@northgate-capital.secure-update.com (spoofed domain)
Attachment: benefits_form_2027.xlsx (macro-enabled)
Context: 3 users opened the attachment. Macros were enabled on 1 device.
"""

    result_2 = run_adaptive_triage(alert_2)

    # Alert 3: Brute force
    alert_3 = """
Alert ID: NG-2027-1167
Severity: MEDIUM
Source: SIEM (Splunk)
Time: 14:22 EST
Event: 847 failed login attempts to VPN from IP 198.51.100.88
Target accounts: multiple (password spray pattern detected)
Context: Attack ongoing for 45 minutes. No successful logins yet.
Source IP geolocation: Eastern Europe, known VPN exit node.
"""

    result_3 = run_adaptive_triage(alert_3)

    # ─────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n[OK] Fixed Pipeline: Always runs 3 steps (extract -> enrich -> brief)")
    print(f"[OK] Adaptive Pipeline: Classified 3 alerts")
    print(f"  - Alert 1: {result_1['branch']}")
    print(f"  - Alert 2: {result_2['branch']}")
    print(f"  - Alert 3: {result_3['branch']}")
    print("\n[SUMMARY] Key Insight:")
    print("  Fixed = predictable work, hard-code the steps")
    print("  Adaptive = input-dependent work, let the model classify and route")
