"""Load test for the Owlin API. Run it only against your own deployment.

    OWLIN_TOKEN=<access token> uv run python scripts/load_test.py --target orders --total 100000

Targets:
  me      GET  /api/me            reads the profile (one SQL query)
  orders  POST /api/orders        multipart order with a screenshot; once the account has 4 orders
                                  under review the API answers 409 without touching storage
  mix     both, 1 order per 10 reads

The first requests of the `orders` target create real orders (up to the open-order limit),
reject or delete them in the admin panel afterwards.
"""

import argparse
import asyncio
import os
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

DEFAULT_IMAGE = Path(r"C:\Users\Roman\Downloads\repository-open-graph-template.png")


async def worker(client, queue, build_request, statuses, latencies, errors):
    while True:
        index = await queue.get()
        if index is None:
            return
        method, path, kwargs = build_request(index)
        started = time.perf_counter()
        try:
            response = await client.request(method, path, **kwargs)
            statuses[response.status_code] += 1
        except httpx.HTTPError as error:
            errors[type(error).__name__] += 1
        finally:
            latencies.append((time.perf_counter() - started) * 1000)


def percentile(values: list[float], share: float) -> float:
    return values[min(len(values) - 1, int(len(values) * share))]


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://api.owlin.software")
    parser.add_argument("--target", choices=["me", "orders", "mix"], default="me")
    parser.add_argument("--total", type=int, default=100_000)
    parser.add_argument("--concurrency", type=int, default=100)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()

    token = os.environ.get("OWLIN_TOKEN")
    if not token:
        sys.exit("Set OWLIN_TOKEN to a valid access token first.")
    image = args.image.read_bytes() if args.target != "me" else b""

    def build_request(index: int):
        if args.target == "me" or (args.target == "mix" and index % 10):
            return "GET", "/api/me", {}
        form = {"product": "spoofer", "period": "1m", "method": "paypal", "proof_text": "load test"}
        files = {"screenshots": ("proof.png", image, "image/png")}
        return "POST", "/api/orders", {"data": form, "files": files}

    limits = httpx.Limits(max_connections=args.concurrency, max_keepalive_connections=args.concurrency)
    headers = {"Authorization": f"Bearer {token}"}
    statuses: Counter = Counter()
    errors: Counter = Counter()
    latencies: list[float] = []
    queue: asyncio.Queue = asyncio.Queue(maxsize=args.concurrency * 2)

    started = time.perf_counter()
    async with httpx.AsyncClient(base_url=args.url, headers=headers, limits=limits, timeout=args.timeout) as client:
        tasks = [
            asyncio.create_task(worker(client, queue, build_request, statuses, latencies, errors))
            for _ in range(args.concurrency)
        ]
        reporter = asyncio.create_task(report_progress(statuses, errors, args.total, started))
        for index in range(args.total):
            await queue.put(index)
        for _ in tasks:
            await queue.put(None)
        await asyncio.gather(*tasks)
        reporter.cancel()
    elapsed = time.perf_counter() - started

    latencies.sort()
    print(f"\n{args.total} requests in {elapsed:.1f}s = {args.total / elapsed:.0f} req/s")
    print("statuses:", dict(sorted(statuses.items())))
    if errors:
        print("network errors:", dict(errors))
    if latencies:
        print(
            f"latency ms: median {statistics.median(latencies):.0f}, "
            f"p95 {percentile(latencies, 0.95):.0f}, p99 {percentile(latencies, 0.99):.0f}, max {latencies[-1]:.0f}"
        )


async def report_progress(statuses, errors, total, started) -> None:
    while True:
        await asyncio.sleep(5)
        finished = sum(statuses.values()) + sum(errors.values())
        elapsed = time.perf_counter() - started
        print(f"{finished}/{total}  {finished / elapsed:.0f} req/s  {dict(sorted(statuses.items()))}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
