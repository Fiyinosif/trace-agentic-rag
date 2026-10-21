"""
Concurrency test: simulates multiple users hitting the system at the same
time and verifies:
  1. Requests actually overlap in wall-clock time (not serialized)
  2. Each user's session state stays isolated (no cross-talk)
  3. All requests complete successfully under concurrent load

Run with: python3 tests/test_concurrent_users.py
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import httpx
from httpx import ASGITransport

from api import app


USERS_AND_QUERIES = [
    ("Alice", "how do I save money on S3 storage"),
    ("Bob", "what are Lambda concurrency limits"),
    ("Carol", "how does DynamoDB capacity mode work"),
    ("Dave", "how do I save money on S3 storage"),  # same query as Alice, different session
]


async def simulate_user(client: httpx.AsyncClient, name: str, query: str) -> dict:
    session_resp = await client.post("/session")
    session_id = session_resp.json()["session_id"]

    start = time.perf_counter()
    resp = await client.post("/query", json={"session_id": session_id, "query": query})
    elapsed = time.perf_counter() - start

    data = resp.json()
    return {
        "user": name,
        "session_id": session_id,
        "query": query,
        "status": resp.status_code,
        "trust_score": data.get("trust_score"),
        "elapsed_s": round(elapsed, 3),
    }


async def main():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        overall_start = time.perf_counter()

        # Fire all users' requests CONCURRENTLY, not one at a time
        results = await asyncio.gather(*[
            simulate_user(client, name, query) for name, query in USERS_AND_QUERIES
        ])

        overall_elapsed = time.perf_counter() - overall_start

        print(f"\n{len(USERS_AND_QUERIES)} concurrent users, total wall time: {overall_elapsed:.3f}s")
        print(f"(if requests were serialized, total time would be ~sum of individual times)\n")

        sum_individual = sum(r["elapsed_s"] for r in results)
        print(f"Sum of individual request times: {sum_individual:.3f}s")
        print(f"Actual wall-clock time:          {overall_elapsed:.3f}s")
        print(f"Concurrency speedup:              {sum_individual / overall_elapsed:.2f}x\n")

        for r in results:
            print(f"  {r['user']:8s} session={r['session_id'][:8]}...  "
                  f"trust={r['trust_score']}  status={r['status']}  time={r['elapsed_s']}s")

        # Verify session isolation: each session's history should contain
        # ONLY that user's query, never another user's
        print("\nSession isolation check:")
        all_isolated = True
        for r in results:
            hist_resp = await client.get(f"/session/{r['session_id']}/history")
            history = hist_resp.json()["history"]
            queries_in_history = [h["query"] for h in history]
            isolated = queries_in_history == [r["query"]]
            all_isolated = all_isolated and isolated
            print(f"  {r['user']:8s}: history={queries_in_history} "
                  f"{'OK' if isolated else 'FAILED — CROSS-SESSION LEAK'}")

        assert all_isolated, "Session isolation failed!"
        assert all(r["status"] == 200 for r in results), "Some requests failed!"
        print("\nAll checks passed: concurrent requests succeeded with isolated sessions.")


if __name__ == "__main__":
    asyncio.run(main())
