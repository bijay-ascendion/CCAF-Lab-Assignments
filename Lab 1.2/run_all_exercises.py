"""
Lab 1.2: Run All Exercises
Convenient script to run all three exercises in sequence
"""

import sys
import subprocess
import os

def run_exercise(name, script_path, description):
    """Run a single exercise script and report results."""
    print("\n" + "="*80)
    print(f"[RUN] {name}")
    print(f"   {description}")
    print("="*80 + "\n")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            text=True,
            timeout=300  # 5 minute timeout per exercise
        )

        if result.returncode == 0:
            print(f"\n[PASS] {name} completed successfully\n")
            return True
        else:
            print(f"\n[FAIL] {name} failed with return code {result.returncode}\n")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n[WARN]  {name} timed out after 5 minutes\n")
        return False
    except Exception as e:
        print(f"\n[FAIL] {name} failed with exception: {e}\n")
        return False


def main():
    print("""
================================================================================
                    Lab 1.2: Controlling Execution
                 Hooks, Decomposition & Session State

                AI SOC Copilot for NorthGate Capital
================================================================================
""")

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[WARN]  WARNING: ANTHROPIC_API_KEY not set")
        print("   Exercise 1 (tool_hooks.py) will run without API")
        print("   Exercises 2-3 require API key and will fail\n")

    exercises = [
        ("Exercise 1a: Hook Chain (Standalone)",
         "tool_hooks.py",
         "Test log/validate/block hooks without API calls"),

        ("Exercise 1b: Agent with Hooks (Live)",
         "agent_with_hooks.py",
         "SOC agent with guardrails - will attempt to quarantine trading server"),

        ("Exercise 2: Fixed vs Adaptive Decomposition",
         "decompose.py",
         "Threat intel digest + alert triage router"),

        ("Exercise 3: Session State Management",
         "session_manager.py",
         "Save/resume/fork/summarize for long-running investigations"),
    ]

    results = []

    for name, script, description in exercises:
        success = run_exercise(name, script, description)
        results.append((name, success))

        # Pause between exercises
        if name != exercises[-1][0]:  # Not the last one
            print("\n" + "-"*80)
            input("Press Enter to continue to next exercise...")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80 + "\n")

    for name, success in results:
        status = "[PASS] PASS" if success else "[FAIL] FAIL"
        print(f"{status}  {name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\n[RESULTS] Results: {passed}/{total} exercises passed")

    if passed == total:
        print("\n[SUCCESS] All exercises completed successfully!")
        print("\n[PASS] Completion checklist:")
        print("   - Hooks blocked dangerous actions")
        print("   - Fixed pipeline generated executive brief")
        print("   - Adaptive pipeline routed alerts correctly")
        print("   - Sessions saved to ./sessions/ directory")
        print("   - Fork created independent branches")
        print("   - Summarizer preserved concrete values")
    else:
        print("\n[WARN]  Some exercises failed - review output above")

    # Check sessions directory
    sessions_dir = os.path.join(os.path.dirname(__file__), "sessions")
    if os.path.exists(sessions_dir):
        files = os.listdir(sessions_dir)
        print(f"\n[FILES] Session files: {len(files)} saved to ./sessions/")
        for f in files:
            print(f"   - {f}")
    else:
        print("\n[WARN]  No sessions/ directory found - Exercise 3 may have failed")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
