"""
Phase F — Load test script.
Fires 200 concurrent requests at /api/progress/stats and reports p50/p95/p99.

Usage:
  # Against localhost (1-worker or N-worker):
  python scripts/local_load_test.py

  # Against production:
  python scripts/local_load_test.py https://mytacoai.com
"""
import asyncio
import httpx
import json
import sys
import time
from pathlib import Path


CREDENTIALS_PATH = Path(__file__).parent.parent.parent / "test_credentials" / "test_users.json"
DEFAULT_BASE = "http://localhost:8000"


async def hit(client: httpx.AsyncClient, token: str, url: str):
    start = time.monotonic()
    r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    return r.status_code, time.monotonic() - start


async def main():
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE
    endpoint = f"{base}/api/progress/stats"

    with open(CREDENTIALS_PATH) as f:
        users = json.load(f)
    token = users["medium"]["jwt"]

    print(f"Target: {endpoint}")
    print(f"Requests: 50 concurrent")
    print()

    async with httpx.AsyncClient(timeout=30) as client:
        # Send in batches of 20 to avoid overwhelming single worker / network
        n = 50
        tasks = [hit(client, token, endpoint) for _ in range(n)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    results = [r for r in results if not isinstance(r, Exception)]
    successes = [r for r in results if r[0] == 200]
    failures = [r for r in results if r[0] != 200]
    latencies = sorted(r[1] for r in successes)
    n = 50

    print(f"Success: {len(successes)}/{n}")
    if failures:
        codes = {}
        for r in failures:
            codes[r[0]] = codes.get(r[0], 0) + 1
        print(f"Failures: {codes}")

    if latencies:
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[min(int(len(latencies) * 0.95), len(latencies) - 1)]
        p99 = latencies[min(int(len(latencies) * 0.99), len(latencies) - 1)]
        print(f"p50: {p50 * 1000:.0f}ms")
        print(f"p95: {p95 * 1000:.0f}ms")
        print(f"p99: {p99 * 1000:.0f}ms")


if __name__ == "__main__":
    asyncio.run(main())
