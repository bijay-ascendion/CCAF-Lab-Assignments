"""
Exercise 1: PostToolUse Hooks
Hook engine for SOC agent - log, validate, and block dangerous operations
"""

import ipaddress
from typing import Tuple, Dict, List, Callable, Any

# Protection lists - critical assets that must never be touched without approval
PROTECTED_HOSTS = [
    "trading-prod-01",
    "trading-prod-02",
    "trading-prod-03",
    "market-data-relay-01",
    "market-data-relay-02",
    "ceo-laptop",
    "cfo-laptop",
    "ciso-laptop"
]

PROTECTED_IPS = [
    "198.51.100.10",  # Reuters market-data
    "198.51.100.11",  # Bloomberg terminal
    "192.0.2.55",     # prime-broker API
    "192.0.2.56"      # clearing-house webhook
]

# Hook functions - each returns (allowed: bool, reason: str)

def logging_hook(tool_name: str, tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    LOG hook - observes every tool call, never blocks.
    Builds audit trail for SOX/SOC2 compliance.
    """
    keys = ", ".join(tool_input.keys())
    print(f"[AUDIT LOG] Tool: {tool_name} | Keys: {keys}")
    return (True, "")


def arg_validation_hook(tool_name: str, tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    VALIDATE hook - blocks on malformed arguments.
    Catches missing required fields and invalid formats.
    """
    if tool_name == "block_ip":
        if "ip" not in tool_input:
            return (False, "block_ip requires 'ip' parameter")
        try:
            ipaddress.IPv4Address(tool_input["ip"])
        except (ipaddress.AddressValueError, ValueError):
            return (False, f"Invalid IPv4 address: {tool_input.get('ip')}")

    elif tool_name == "quarantine_host":
        if "hostname" not in tool_input or not tool_input["hostname"]:
            return (False, "quarantine_host requires 'hostname' parameter")

    elif tool_name == "disable_user":
        if "username" not in tool_input or not tool_input["username"]:
            return (False, "disable_user requires 'username' parameter")

    return (True, "")


def protected_asset_hook(tool_name: str, tool_input: Dict[str, Any]) -> Tuple[bool, str]:
    """
    BLOCK hook - enforces policy on protected assets.
    Trading servers, market-data feeds, and executive accounts are off-limits.
    """
    if tool_name == "quarantine_host":
        hostname = tool_input.get("hostname", "")
        for protected in PROTECTED_HOSTS:
            if protected in hostname.lower() or hostname.lower() in protected:
                return (False, f"POLICY: Cannot quarantine protected host '{protected}'")

    elif tool_name == "block_ip":
        ip = tool_input.get("ip", "")
        if ip in PROTECTED_IPS:
            return (False, f"POLICY: Cannot block protected IP {ip} (market-data/trading feed)")

    elif tool_name == "disable_user":
        username = tool_input.get("username", "").lower()
        protected_users = ["ceo", "cfo", "ciso"]
        if username in protected_users:
            return (False, f"POLICY: Cannot disable executive account '{username}' without dual approval")
        if username.endswith("@northgate-exec"):
            return (False, f"POLICY: Executive domain accounts require dual approval")

    return (True, "")


def run_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_fn: Callable,
    hooks: List[Callable],
    audit_log: List[Dict]
) -> str:
    """
    Route every tool call through the hook chain BEFORE execution.
    If any hook returns False, the real tool never runs.
    """
    # Pass through each hook in order
    for hook in hooks:
        allowed, reason = hook(tool_name, tool_input)
        if not allowed:
            # Record the block
            audit_log.append({
                "tool": tool_name,
                "input": tool_input,
                "status": "BLOCKED",
                "reason": reason
            })
            print(f"[X] BLOCKED: {tool_name} - {reason}")
            return f"BLOCKED by policy: {reason}"

    # All hooks passed - execute the real tool
    result = tool_fn(tool_input)
    audit_log.append({
        "tool": tool_name,
        "input": tool_input,
        "status": "ALLOWED",
        "result": result
    })
    return result


def print_audit_log(audit_log: List[Dict]):
    """
    Print the SOX/SOC2 audit trail.
    Every attempt - allowed or blocked - must be recorded.
    """
    print("\n" + "="*70)
    print("AUDIT LOG (SOC2 Compliance Trail)")
    print("="*70)
    for i, entry in enumerate(audit_log, 1):
        status_icon = "[OK]" if entry["status"] == "ALLOWED" else "[BLOCKED]"
        print(f"\n{i}. {status_icon} {entry['status']}")
        print(f"   Tool: {entry['tool']}")
        print(f"   Input: {entry['input']}")
        if entry["status"] == "BLOCKED":
            print(f"   Reason: {entry['reason']}")
        else:
            print(f"   Result: {entry.get('result', 'N/A')}")
    print("="*70 + "\n")


# Demo tool simulators - in production these would call real EDR/SIEM APIs

DEMO_TOOLS = {
    "block_ip": lambda inp: f"[FIREWALL] Blocked IP {inp['ip']} on perimeter firewall (simulated)",
    "quarantine_host": lambda inp: f"[EDR] Host {inp['hostname']} isolated from network (simulated)",
    "disable_user": lambda inp: f"[AD] User account {inp['username']} disabled (simulated)",
    "query_siem": lambda inp: f"[SIEM] Query executed: {inp['query']} (simulated results)"
}


if __name__ == "__main__":
    print("="*70)
    print("Exercise 1: Hook Chain Demo")
    print("Testing log / validate / block chain on SOC response actions")
    print("="*70 + "\n")

    # Hook chain: log everything, validate args, enforce policy
    hooks = [logging_hook, arg_validation_hook, protected_asset_hook]
    audit_log = []

    # Test cases - mix of allowed and blocked calls
    test_calls = [
        # ALLOWED: Quarantine the suspicious analyst laptop
        ("quarantine_host", {"hostname": "research-analyst-laptop-04"}),

        # ALLOWED: Block the suspicious IP
        ("block_ip", {"ip": "203.0.113.47"}),

        # BLOCKED: Policy violation - trading server
        ("quarantine_host", {"hostname": "trading-prod-01"}),

        # BLOCKED: Policy violation - Bloomberg feed
        ("block_ip", {"ip": "198.51.100.11"}),

        # BLOCKED: Arg validation - malformed IP
        ("block_ip", {"ip": "not-an-ip-address"}),

        # BLOCKED: Arg validation - missing username
        ("disable_user", {}),

        # BLOCKED: Policy violation - executive account
        ("disable_user", {"username": "ceo"}),

        # ALLOWED: Query SIEM
        ("query_siem", {"query": "EventID=4625 AND SourceIP=203.0.113.47"})
    ]

    print("Running test cases...\n")

    for tool_name, tool_input in test_calls:
        print(f"\n>> Attempting: {tool_name}({tool_input})")
        tool_fn = DEMO_TOOLS.get(tool_name, lambda x: "Unknown tool")
        result = run_tool(tool_name, tool_input, tool_fn, hooks, audit_log)
        if not result.startswith("BLOCKED"):
            print(f"[OK] SUCCESS: {result}")

    # Print the complete audit log
    print_audit_log(audit_log)

    print("\n[SUMMARY]")
    allowed = sum(1 for e in audit_log if e["status"] == "ALLOWED")
    blocked = sum(1 for e in audit_log if e["status"] == "BLOCKED")
    print(f"   Allowed: {allowed}")
    print(f"   Blocked: {blocked}")
    print(f"   Total: {len(audit_log)}")
