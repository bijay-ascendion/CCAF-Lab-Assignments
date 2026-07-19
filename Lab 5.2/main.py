"""
Healthcare Claims Processing Pipeline Coordinator
Demonstrates: Error propagation + disk-backed scratchpad + crash recovery
"""

import os
from dotenv import load_dotenv
from agents import run_intake, run_validation, run_adjudication
from scratchpad import Scratchpad
from sample_claims import CLAIMS

# Load environment variables
load_dotenv()


def process_claim(claim: dict, pad: Scratchpad) -> str:
    """
    Walk one claim through all three stages.
    Log every finding; mark terminal status.
    Returns: 'done' or 'failed'
    """
    claim_id = claim["claim_id"]

    # Define the pipeline stages
    stages = [
        ("intake", run_intake),
        ("validation", run_validation),
        ("adjudication", run_adjudication),
    ]

    print(f"\n[CLAIM {claim_id}] Processing...")

    # Walk through each stage
    for stage_name, stage_fn in stages:
        result = stage_fn(claim)

        # Log the result to scratchpad
        pad.log(claim_id, stage_name, result.to_dict())

        # Print status
        if result.ok:
            print(f"  {stage_name}...ok")
        else:
            print(f"  {stage_name}...FAIL ({result.error})")
            # Mark as failed and stop processing this claim
            pad.mark_failed(claim_id, f"{stage_name}: {result.error}")
            return "failed"

    # All stages passed
    pad.mark_done(claim_id)
    return "done"


def main():
    """
    Coordinator loop: skip already-finished claims, process the rest.
    """
    print("=" * 60)
    print("Healthcare Claims Processing Pipeline")
    print("=" * 60)

    # Initialize scratchpad
    pad = Scratchpad("scratchpad.json")

    # Counters
    done_count = 0
    failed_count = 0
    skipped_count = 0

    # Process each claim
    for claim in CLAIMS:
        claim_id = claim["claim_id"]
        status = pad.status(claim_id)

        # Crash recovery: skip claims already finished
        if status in ("done", "failed"):
            print(f"\n[CLAIM {claim_id}] (already {status}, skipping)")
            skipped_count += 1
            continue

        # Process the claim
        final_status = process_claim(claim, pad)

        if final_status == "done":
            done_count += 1
        else:
            failed_count += 1

    # Print summary
    print("\n" + "=" * 60)
    print(f"Pipeline complete: done: {done_count}  failed: {failed_count}  skipped: {skipped_count}")
    print("=" * 60)
    print("\nAudit trail saved to: scratchpad.json")
    print("Run again to see crash-recovery skip in action.")


if __name__ == "__main__":
    main()
