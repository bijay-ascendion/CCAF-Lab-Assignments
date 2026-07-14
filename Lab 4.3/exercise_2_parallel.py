"""
Exercise 2: Parallel Processing for Throughput
Demonstrates ThreadPoolExecutor for I/O-bound burst workloads
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

PROMPT = "Classify the sentiment of this Helix Robotics news headline as positive, negative, or neutral. Answer with one word only.\n\nHeadline: {h}"

# Breaking news headlines - need fast classification
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


def classify(client, headline):
    """Classify a single headline"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=20,
        messages=[{"role": "user", "content": PROMPT.format(h=headline)}],
    )
    return response.content[0].text.strip()


def run_sequential(client, headlines):
    """Run classifications sequentially"""
    t0 = time.time()
    results = []
    for h in headlines:
        results.append(classify(client, h))
    elapsed = time.time() - t0
    return results, elapsed


def run_parallel(client, headlines, workers=5):
    """
    Run classifications in parallel using ThreadPoolExecutor.
    .map() preserves input order - results line up with headlines.
    """
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        # .map preserves input order, so results line up with headlines.
        results = list(pool.map(lambda h: classify(client, h), headlines))
    elapsed = time.time() - t0
    return results, elapsed


def main():
    print("\n" + "=" * 70)
    print("Exercise 2: Parallel Processing for Throughput")
    print("=" * 70)
    print(f"\nClassifying {len(HEADLINES)} breaking news headlines.")
    print("Comparing sequential vs parallel execution.\n")

    # Sequential run
    print("Running SEQUENTIAL...")
    seq_results, seq_time = run_sequential(client, HEADLINES)
    print(f"Completed in {seq_time:.2f}s")

    # Parallel run
    print("\nRunning PARALLEL (5 workers)...")
    par_results, par_time = run_parallel(client, HEADLINES, workers=5)
    print(f"Completed in {par_time:.2f}s")

    # Verify results match
    print(f"\n{'=' * 70}")
    print("RESULTS COMPARISON")
    print("=" * 70)

    matches = sum(1 for s, p in zip(seq_results, par_results) if s == p)
    print(f"Results match: {matches}/{len(HEADLINES)}")

    print("\nSample results:")
    for i, (seq, par) in enumerate(zip(seq_results[:3], par_results[:3])):
        print(f"  {i}: seq={seq}, par={par}")

    # Speedup
    speedup = seq_time / par_time if par_time > 0 else 0
    print(f"\n{'=' * 70}")
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"Sequential:  {seq_time:.2f}s")
    print(f"Parallel:    {par_time:.2f}s")
    print(f"Speedup:     {speedup:.2f}x")

    print(f"\n{'=' * 70}")
    print("TAKEAWAYS")
    print("=" * 70)
    print("• I/O-bound waits overlap - threads are the right primitive")
    print("• .map() preserves order - no manual id-tagging needed")
    print("• Speedup limited by rate limits - tune workers cautiously")
    print("• Use ThreadPoolExecutor for bursts, batches for bulk\n")


if __name__ == "__main__":
    main()
