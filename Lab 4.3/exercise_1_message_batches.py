"""
Exercise 1: Classify a Workload with the Message Batches API
Demonstrates async batch processing for large offline workloads
"""

import os
import sys
import time
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

PROMPT = "Classify the sentiment of this Helix Robotics news headline as positive, negative, or neutral. Answer with one word only.\n\nHeadline: {h}"

# Sample headlines about Helix Robotics
HEADLINES = [
    "Helix Robotics announces breakthrough in autonomous warehouse navigation",
    "Helix Robotics faces regulatory probe over safety protocols",
    "Helix stock rises 12% on strong quarterly earnings report",
    "Workers union raises concerns about Helix automation plans",
    "Helix Robotics partners with major retailer for pilot program",
    "Helix Robotics recalls 500 units due to software bug",
    "Industry analysts praise Helix's innovation in logistics automation",
    "Helix Robotics expands to European market with new facility",
]


def build_requests(headlines):
    """
    Build batch requests - one per headline with custom_id.
    Each request has {custom_id, params} structure.
    """
    return [
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


def main():
    # Handle --fetch flag for retrieving existing batch
    if "--fetch" in sys.argv and len(sys.argv) > 2:
        batch_id = sys.argv[2]
        print(f"\nFetching results for batch: {batch_id}\n")
        batch = client.messages.batches.retrieve(batch_id)
        print(f"Status: {batch.processing_status}")
        print(f"Counts: {batch.request_counts}\n")

        if batch.processing_status != "ended":
            print("Batch not yet complete. Try again later.")
            return

        print("Results:")
        print("=" * 70)
        for entry in client.messages.batches.results(batch_id):
            if entry.result.type == "succeeded":
                text = "".join(
                    b.text for b in entry.result.message.content if b.type == "text"
                ).strip()
                print(f"{entry.custom_id}: {text}")
            else:
                print(f"{entry.custom_id}: ERROR ({entry.result.type})")
        return

    print("\n" + "=" * 70)
    print("Exercise 1: Message Batches API")
    print("=" * 70)
    print(f"\nClassifying {len(HEADLINES)} Helix Robotics headlines...")
    print("This demonstrates async batch processing for offline workloads.\n")

    # Build batch requests
    requests = build_requests(HEADLINES)

    # Submit batch
    print("Submitting batch...")
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch submitted: {batch.id}\n")

    # Poll until completed (with deadline)
    print("Polling for completion...")
    deadline = time.time() + 600  # 10 minutes

    while True:
        batch = client.messages.batches.retrieve(batch.id)
        counts = batch.request_counts
        print(
            f"Status: {batch.processing_status} | "
            f"Processing: {counts.processing}, "
            f"Succeeded: {counts.succeeded}, "
            f"Errored: {counts.errored}"
        )

        if batch.processing_status == "ended":
            break

        if time.time() > deadline:
            print(f"\nStill processing after 10 minutes.")
            print(f"Fetch results later with: python {sys.argv[0]} --fetch {batch.id}")
            return

        time.sleep(10)

    # Collect results by custom_id
    print(f"\n{'=' * 70}")
    print("RESULTS")
    print("=" * 70)

    for entry in client.messages.batches.results(batch.id):
        if entry.result.type == "succeeded":
            text = "".join(
                b.text for b in entry.result.message.content if b.type == "text"
            ).strip()
            print(f"{entry.custom_id}: {text}")
        else:
            print(f"{entry.custom_id}: ERROR ({entry.result.type})")

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)
    print("Batch processing trades latency for cost and scale.")
    print("Every result matched back via custom_id, not submission order.")
    print("Use batches for overnight/bulk jobs, not real-time work.\n")


if __name__ == "__main__":
    main()
