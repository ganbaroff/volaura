"""
concurrent_stress.py — VOLAURA Concurrent Stress Tester

Sends N requests to a single endpoint simultaneously using one JWT.
Tests: rate limiting, race conditions, DB connection pool exhaustion.

Usage:
  python scripts/concurrent_stress.py \\
    --url http://localhost:8000 \\
    --jwt eyJhbGc... \\
    --concurrency 500 \\
    --endpoint /api/assessment/start

  # Or with a body file:
  python scripts/concurrent_stress.py \\
    --url http://localhost:8000 \\
    --jwt eyJhbGc... \\
    --concurrency 200 \\
    --endpoint /api/aura/me \\
    --method GET
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass, field

import httpx

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class RequestResult:
    status_code: int | None
    latency_ms: int
    error: str | None = None


@dataclass
class StressReport:
    total: int
    status_distribution: dict[str, int] = field(default_factory=dict)
    p50_ms: int = 0
    p95_ms: int = 0
    p99_ms: int = 0
    mean_ms: float = 0.0
    min_ms: int = 0
    max_ms: int = 0
    connection_errors: int = 0
    error_samples: list[str] = field(default_factory=list)
    elapsed_wall_seconds: float = 0.0
    rps: float = 0.0


# ── Core ──────────────────────────────────────────────────────────────────────

DEFAULT_BODY_BY_ENDPOINT: dict[str, dict] = {
    "/api/assessment/start": {
        "competency_slug": "communication",
        "language": "en",
        "role_level": "volunteer",
    },
    "/api/assessment/answer": {
        "session_id": "00000000-0000-0000-0000-000000000000",
        "question_id": "00000000-0000-0000-0000-000000000000",
        "answer": "stress test answer",
        "response_time_ms": 3000,
    },
}


async def fire_single(
    semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,
    url: str,
    method: str,
    headers: dict[str, str],
    body: dict | None,
) -> RequestResult:
    async with semaphore:
        t0 = time.monotonic()
        try:
            if method.upper() == "GET":
                resp = await client.get(url, headers=headers)
            else:
                resp = await client.post(url, json=body, headers=headers)
            latency = int((time.monotonic() - t0) * 1000)
            return RequestResult(status_code=resp.status_code, latency_ms=latency)
        except httpx.ConnectError as e:
            latency = int((time.monotonic() - t0) * 1000)
            return RequestResult(status_code=None, latency_ms=latency, error=f"ConnectError: {e!s:.80}")
        except httpx.TimeoutException as e:
            latency = int((time.monotonic() - t0) * 1000)
            return RequestResult(status_code=None, latency_ms=latency, error=f"Timeout: {e!s:.80}")
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            return RequestResult(status_code=None, latency_ms=latency, error=f"{type(e).__name__}: {e!s:.80}")


async def run_stress(
    base_url: str,
    endpoint: str,
    jwt: str,
    concurrency: int,
    method: str,
    body: dict | None,
) -> StressReport:
    full_url = f"{base_url.rstrip('/')}{endpoint}"
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }

    # Use a semaphore to cap actual in-flight connections
    # (asyncio.gather doesn't limit concurrency by default)
    semaphore = asyncio.Semaphore(concurrency)

    # Set limits: pool size matches concurrency
    limits = httpx.Limits(
        max_connections=concurrency + 10,
        max_keepalive_connections=concurrency,
    )
    timeout = httpx.Timeout(30.0, connect=10.0)

    print(f"\n  Firing {concurrency} concurrent {method.upper()} {full_url}")
    print(f"  Pool size: {concurrency + 10} connections")

    t_wall_start = time.monotonic()

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        tasks = [
            fire_single(semaphore, client, full_url, method, headers, body)
            for _ in range(concurrency)
        ]
        results: list[RequestResult] = await asyncio.gather(*tasks)

    t_wall_end = time.monotonic()
    elapsed = t_wall_end - t_wall_start

    # Aggregate
    latencies = [r.latency_ms for r in results]
    statuses = [str(r.status_code) if r.status_code is not None else "error" for r in results]
    connection_errors = sum(1 for r in results if r.status_code is None)
    error_samples = list({r.error for r in results if r.error is not None})[:5]

    latencies_sorted = sorted(latencies)
    n = len(latencies_sorted)

    def percentile(data: list[int], pct: float) -> int:
        if not data:
            return 0
        idx = max(0, min(int(len(data) * pct / 100), len(data) - 1))
        return data[idx]

    report = StressReport(
        total=concurrency,
        status_distribution=dict(Counter(statuses)),
        p50_ms=percentile(latencies_sorted, 50),
        p95_ms=percentile(latencies_sorted, 95),
        p99_ms=percentile(latencies_sorted, 99),
        mean_ms=statistics.mean(latencies) if latencies else 0,
        min_ms=min(latencies) if latencies else 0,
        max_ms=max(latencies) if latencies else 0,
        connection_errors=connection_errors,
        error_samples=error_samples,
        elapsed_wall_seconds=round(elapsed, 2),
        rps=round(concurrency / elapsed, 1) if elapsed > 0 else 0,
    )
    return report


# ── Report ────────────────────────────────────────────────────────────────────

def print_report(report: StressReport, endpoint: str) -> None:
    print("\n" + "=" * 55)
    print("  VOLAURA CONCURRENT STRESS TEST REPORT")
    print("=" * 55)
    print(f"  Endpoint:          {endpoint}")
    print(f"  Total requests:    {report.total}")
    print(f"  Wall time:         {report.elapsed_wall_seconds}s")
    print(f"  Effective RPS:     {report.rps}")
    print()
    print("  Status distribution:")
    for code, count in sorted(report.status_distribution.items()):
        pct = count / report.total * 100
        bar_len = int(pct / 2)
        bar = "#" * bar_len
        label = _status_label(code)
        print(f"    {code:>5}  {count:>5}  ({pct:>5.1f}%)  {bar}  {label}")
    print()
    print("  Latency (all requests):")
    print(f"    min:  {report.min_ms}ms")
    print(f"    mean: {report.mean_ms:.0f}ms")
    print(f"    p50:  {report.p50_ms}ms")
    print(f"    p95:  {report.p95_ms}ms")
    print(f"    p99:  {report.p99_ms}ms")
    print(f"    max:  {report.max_ms}ms")
    print()
    print(f"  Connection errors: {report.connection_errors}")
    if report.error_samples:
        print("  Error samples:")
        for e in report.error_samples:
            print(f"    - {e}")

    # Interpretation
    print()
    print("  Interpretation:")
    total_4xx = sum(v for k, v in report.status_distribution.items() if k.startswith("4"))
    total_5xx = sum(v for k, v in report.status_distribution.items() if k.startswith("5"))
    total_429 = report.status_distribution.get("429", 0)
    total_200 = report.status_distribution.get("200", 0) + report.status_distribution.get("201", 0)

    if total_429 > 0:
        print(f"    Rate limiter active: {total_429} requests throttled ({total_429/report.total*100:.0f}%)")
    if total_5xx > 0:
        print(f"    Server errors: {total_5xx} ({total_5xx/report.total*100:.0f}%) — possible pool exhaustion or crash")
    if report.connection_errors > 0:
        print(f"    Connection failures: {report.connection_errors} — server may be saturated or not running")
    if total_200 == report.total:
        print("    All requests succeeded — no rate limiting or errors at this concurrency level")
    if report.p99_ms > 5000:
        print(f"    P99={report.p99_ms}ms is high — check DB connection pool and slow query log")

    print("=" * 55)


def _status_label(code: str) -> str:
    labels = {
        "200": "OK",
        "201": "Created",
        "400": "Bad Request",
        "401": "Unauthorized",
        "403": "Forbidden",
        "404": "Not Found",
        "409": "Conflict",
        "422": "Validation Error",
        "429": "Rate Limited",
        "500": "Internal Server Error",
        "502": "Bad Gateway",
        "503": "Service Unavailable",
        "error": "Connection/Timeout Error",
    }
    return labels.get(code, "")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="VOLAURA Concurrent Stress Tester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--jwt",
        type=str,
        required=True,
        help="JWT access token for authentication",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=500,
        help="Number of concurrent requests (default: 500)",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="/api/assessment/start",
        help="Endpoint path to stress test (default: /api/assessment/start)",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="POST",
        choices=["GET", "POST", "get", "post"],
        help="HTTP method (default: POST)",
    )
    parser.add_argument(
        "--body",
        type=str,
        default=None,
        help="JSON string for request body (optional — uses sensible defaults per endpoint)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Path to save JSON results (optional)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    method = args.method.upper()

    # Resolve body
    body: dict | None = None
    if method == "POST":
        if args.body:
            try:
                body = json.loads(args.body)
            except json.JSONDecodeError as e:
                print(f"ERROR: --body is not valid JSON: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            body = DEFAULT_BODY_BY_ENDPOINT.get(args.endpoint)
            if body is None:
                print(
                    f"WARNING: No default body for endpoint '{args.endpoint}'. "
                    "Pass --body or the request may fail with 422.",
                    file=sys.stderr,
                )
            else:
                print(f"  Using default body for {args.endpoint}:")
                print(f"    {json.dumps(body)}")

    print(f"\nVOLAURA Concurrent Stress Test")
    print(f"  URL:         {args.url}{args.endpoint}")
    print(f"  Method:      {method}")
    print(f"  Concurrency: {args.concurrency}")
    print(f"  JWT:         {args.jwt[:20]}...{args.jwt[-10:] if len(args.jwt) > 30 else ''}")

    report = asyncio.run(
        run_stress(
            base_url=args.url,
            endpoint=args.endpoint,
            jwt=args.jwt,
            concurrency=args.concurrency,
            method=method,
            body=body,
        )
    )

    print_report(report, args.endpoint)

    if args.output_json:
        output = {
            "endpoint": args.endpoint,
            "method": method,
            "concurrency": args.concurrency,
            "api_url": args.url,
            "report": {
                "total": report.total,
                "elapsed_wall_seconds": report.elapsed_wall_seconds,
                "rps": report.rps,
                "status_distribution": report.status_distribution,
                "latency": {
                    "min_ms": report.min_ms,
                    "mean_ms": round(report.mean_ms, 1),
                    "p50_ms": report.p50_ms,
                    "p95_ms": report.p95_ms,
                    "p99_ms": report.p99_ms,
                    "max_ms": report.max_ms,
                },
                "connection_errors": report.connection_errors,
                "error_samples": report.error_samples,
            },
        }
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved: {args.output_json}")


if __name__ == "__main__":
    main()
