"""
behavioral_sim.py — VOLAURA Full Behavioral Simulation Driver

Simulates N real users through the complete Volaura journey:
  auth → profile → assessment (per archetype) → aura

5 archetypes (user_index % 5):
  0 = fast         : response_time_ms=800   (triggers timing penalty)
  1 = slow         : response_time_ms=45000
  2 = dropoff      : submits 2 answers then stops (never completes)
  3 = rapid_restart: abandons session, immediately restarts same competency (expect 429)
  4 = grinder      : completes 3 competencies back-to-back

Usage:
  python scripts/behavioral_sim.py --users 100 --batch-size 10
  python scripts/behavioral_sim.py --users 50 --dry-run
  python scripts/behavioral_sim.py --cleanup
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
from supabase import create_client, Client

# ── Constants ─────────────────────────────────────────────────────────────────
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://dwdgzfusjsobnixgyzjk.supabase.co")
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]  # required — never hardcode
SUPABASE_ANON_KEY = os.environ.get(
    "SUPABASE_ANON_KEY",
    (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZGd6ZnVzanNvYm5peGd5emprIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4OTU0MDQsImV4cCI6MjA5MDQ3MTQwNH0"
        ".rbyIBLRONffOKCmfiLJQU_RVEgDmQ5MjUMPj8I8GxOw"
    ),
)

SIM_EMAIL_DOMAIN = "@volaura-sim.test"
SIM_PASSWORD = "SimTest123!"
SIM_PREFIX = "sim_user_"

COMPETENCIES = [
    "communication",
    "reliability",
    "english_proficiency",
    "leadership",
    "event_performance",
    "tech_literacy",
    "adaptability",
    "empathy_safeguarding",
]

ARCHETYPES = {
    0: "fast",
    1: "slow",
    2: "dropoff",
    3: "rapid_restart",
    4: "grinder",
}

# Archetype response times (ms) — used for answer payloads
ARCHETYPE_TIMING = {
    "fast": 800,
    "slow": 45_000,
    "dropoff": 3_000,
    "rapid_restart": 3_000,
    "grinder": 5_000,
}

MAX_ANSWERS_PER_SESSION = 12


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class UserMetrics:
    archetype: str
    user_index: int
    user_id: str = ""
    jwt: str = ""

    # step-level tracking
    step_failures: dict[str, int] = field(default_factory=dict)   # step → http status
    latencies_ms: dict[str, list[int]] = field(default_factory=dict)  # step → [ms, ...]

    # assessment outcomes
    theta_final: float | None = None
    theta_se_final: float | None = None
    questions_answered: int = 0
    stop_reason: str | None = None

    # aura
    aura_score: float | None = None
    badge_tier: str | None = None

    # error tracking
    error_codes: list[str] = field(default_factory=list)
    gaming_flags_triggered: bool = False

    # journey
    completed_full_journey: bool = False
    sessions_completed: int = 0


# ── Supabase admin client (sync — only used for user CRUD) ───────────────────

def get_admin_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def create_sim_user(admin: Client, i: int) -> tuple[str, str] | None:
    """Create a real Supabase auth user. Returns (user_id, jwt) or None on failure."""
    email = f"{SIM_PREFIX}{i}{SIM_EMAIL_DOMAIN}"
    try:
        resp = admin.auth.admin.create_user({
            "email": email,
            "password": SIM_PASSWORD,
            "email_confirm": True,
        })
        user_id = resp.user.id if resp.user else None
        if not user_id:
            return None

        # Sign in via anon client to get a real JWT
        sign_in = admin.auth.sign_in_with_password({
            "email": email,
            "password": SIM_PASSWORD,
        })
        jwt = sign_in.session.access_token if sign_in.session else None
        if not jwt:
            return None

        return user_id, jwt
    except Exception as exc:
        print(f"  [WARN] create_user {i} failed: {exc}", file=sys.stderr)
        return None


def delete_sim_users(admin: Client) -> int:
    """Delete all accounts with SIM_EMAIL_DOMAIN. Returns count deleted."""
    # List all users (paginate if needed — Supabase default page is 50)
    deleted = 0
    page = 1
    while True:
        resp = admin.auth.admin.list_users(page=page, per_page=1000)
        users = resp if isinstance(resp, list) else getattr(resp, "users", [])
        if not users:
            break
        for u in users:
            if hasattr(u, "email") and u.email and SIM_EMAIL_DOMAIN in u.email:
                try:
                    admin.auth.admin.delete_user(u.id)
                    deleted += 1
                except Exception as exc:
                    print(f"  [WARN] delete_user {u.id} failed: {exc}", file=sys.stderr)
        if len(users) < 1000:
            break
        page += 1
    return deleted


# ── Async HTTP helpers ────────────────────────────────────────────────────────

def _auth_headers(jwt: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON_KEY,
    }


async def _post(
    client: httpx.AsyncClient,
    url: str,
    jwt: str,
    payload: dict,
    metrics: UserMetrics,
    step: str,
) -> dict | None:
    t0 = time.monotonic()
    try:
        resp = await client.post(url, json=payload, headers=_auth_headers(jwt))
        latency = int((time.monotonic() - t0) * 1000)
        metrics.latencies_ms.setdefault(step, []).append(latency)
        if resp.status_code >= 400:
            metrics.step_failures[step] = resp.status_code
            try:
                detail = resp.json().get("detail", {})
                code = detail.get("code", str(resp.status_code)) if isinstance(detail, dict) else str(resp.status_code)
            except Exception:
                code = str(resp.status_code)
            metrics.error_codes.append(f"{step}:{code}")
            return None
        return resp.json()
    except Exception as exc:
        metrics.step_failures[step] = 0
        metrics.error_codes.append(f"{step}:CONNECTION_ERROR:{exc!s:.60}")
        return None


async def _get(
    client: httpx.AsyncClient,
    url: str,
    jwt: str,
    metrics: UserMetrics,
    step: str,
) -> dict | None:
    t0 = time.monotonic()
    try:
        resp = await client.get(url, headers=_auth_headers(jwt))
        latency = int((time.monotonic() - t0) * 1000)
        metrics.latencies_ms.setdefault(step, []).append(latency)
        if resp.status_code >= 400:
            metrics.step_failures[step] = resp.status_code
            try:
                detail = resp.json().get("detail", {})
                code = detail.get("code", str(resp.status_code)) if isinstance(detail, dict) else str(resp.status_code)
            except Exception:
                code = str(resp.status_code)
            metrics.error_codes.append(f"{step}:{code}")
            return None
        return resp.json()
    except Exception as exc:
        metrics.step_failures[step] = 0
        metrics.error_codes.append(f"{step}:CONNECTION_ERROR:{exc!s:.60}")
        return None


# ── Assessment journey helpers ────────────────────────────────────────────────

def _pick_answer(question: dict) -> str:
    """Pick a valid answer for a question — first MCQ option or a short open-ended text."""
    q_type = question.get("question_type", "open_ended")
    if q_type == "mcq" or q_type == "sjt":
        options = question.get("options") or []
        if options and isinstance(options[0], dict):
            # Options have a 'key' field per schema (key/text_en/text_az)
            return str(options[0].get("key", "A"))
        return "A"
    # open_ended — provide a genuine-looking answer (no injection patterns)
    return "I focus on clear communication and active listening to ensure mutual understanding."


async def run_assessment_session(
    client: httpx.AsyncClient,
    api_url: str,
    metrics: UserMetrics,
    competency_slug: str,
    max_answers: int = MAX_ANSWERS_PER_SESSION,
) -> bool:
    """Run one full assessment session. Returns True if completed successfully."""
    jwt = metrics.jwt
    archetype = metrics.archetype
    response_time = ARCHETYPE_TIMING.get(archetype, 3_000)

    # Start session
    start_resp = await _post(
        client,
        f"{api_url}/api/assessment/start",
        jwt,
        {
            "competency_slug": competency_slug,
            "language": "en",
            "role_level": "volunteer",
        },
        metrics,
        "assessment_start",
    )
    if not start_resp:
        return False

    session_id = start_resp.get("session_id")
    if not session_id:
        metrics.step_failures["assessment_start"] = 422
        metrics.error_codes.append("assessment_start:MISSING_SESSION_ID")
        return False

    answers_submitted = 0

    while True:
        next_q = start_resp.get("next_question") if answers_submitted == 0 else None

        # After first iteration, next_question comes from answer response
        # (the loop below updates start_resp with each answer response)
        current_session = start_resp

        if current_session.get("is_complete") or current_session.get("next_question") is None:
            break

        question = current_session.get("next_question")
        if question is None:
            break

        # Archetype: dropoff — stop after 2 answers
        if archetype == "dropoff" and answers_submitted >= 2:
            metrics.stop_reason = "dropoff"
            return False

        # Max guard
        if answers_submitted >= max_answers:
            metrics.stop_reason = "max_answers_guard"
            break

        answer_text = _pick_answer(question)

        answer_resp = await _post(
            client,
            f"{api_url}/api/assessment/answer",
            jwt,
            {
                "session_id": session_id,
                "question_id": question["id"],
                "answer": answer_text,
                "response_time_ms": response_time,
            },
            metrics,
            "assessment_answer",
        )

        if answer_resp is None:
            # Could be rate limit or server error — stop this session
            return False

        answers_submitted += 1
        metrics.questions_answered += 1

        # Check for gaming flags via timing_warning in AnswerFeedback
        if answer_resp.get("timing_warning"):
            metrics.gaming_flags_triggered = True

        # The answer response contains a nested 'session' object (AnswerFeedback schema)
        inner_session = answer_resp.get("session") or {}
        start_resp = inner_session  # update loop variable

        if inner_session.get("is_complete"):
            break

        if inner_session.get("next_question") is None:
            break

    # Complete session
    complete_resp = await _post(
        client,
        f"{api_url}/api/assessment/complete/{session_id}",
        jwt,
        {},
        metrics,
        "assessment_complete",
    )

    if complete_resp:
        metrics.stop_reason = complete_resp.get("stop_reason")
        metrics.sessions_completed += 1
        return True
    return False


# ── Archetype runners ─────────────────────────────────────────────────────────

async def run_fast(client: httpx.AsyncClient, api_url: str, metrics: UserMetrics) -> None:
    """Archetype 0: single session with 800ms responses — triggers timing penalty."""
    slug = COMPETENCIES[metrics.user_index % len(COMPETENCIES)]
    await run_assessment_session(client, api_url, metrics, slug)
    # Fetch aura
    aura = await _get(client, f"{api_url}/api/aura/me", metrics.jwt, metrics, "aura_get")
    if aura:
        metrics.aura_score = aura.get("total_score")
        metrics.badge_tier = aura.get("badge_tier")
        metrics.completed_full_journey = True


async def run_slow(client: httpx.AsyncClient, api_url: str, metrics: UserMetrics) -> None:
    """Archetype 1: single session with 45s response time."""
    slug = COMPETENCIES[metrics.user_index % len(COMPETENCIES)]
    await run_assessment_session(client, api_url, metrics, slug)
    aura = await _get(client, f"{api_url}/api/aura/me", metrics.jwt, metrics, "aura_get")
    if aura:
        metrics.aura_score = aura.get("total_score")
        metrics.badge_tier = aura.get("badge_tier")
        metrics.completed_full_journey = True


async def run_dropoff(client: httpx.AsyncClient, api_url: str, metrics: UserMetrics) -> None:
    """Archetype 2: starts but abandons after 2 answers — never completes."""
    slug = COMPETENCIES[metrics.user_index % len(COMPETENCIES)]
    await run_assessment_session(client, api_url, metrics, slug)
    # No complete call, no aura fetch — intentional drop-off


async def run_rapid_restart(client: httpx.AsyncClient, api_url: str, metrics: UserMetrics) -> None:
    """Archetype 3: abandons immediately, tries to restart same competency → expect 429."""
    slug = COMPETENCIES[metrics.user_index % len(COMPETENCIES)]

    # First: start a session
    start_resp = await _post(
        client,
        f"{api_url}/api/assessment/start",
        metrics.jwt,
        {"competency_slug": slug, "language": "en", "role_level": "volunteer"},
        metrics,
        "assessment_start",
    )

    if not start_resp:
        return

    # Don't complete — immediately try to restart the same competency
    restart_resp = await _post(
        client,
        f"{api_url}/api/assessment/start",
        metrics.jwt,
        {"competency_slug": slug, "language": "en", "role_level": "volunteer"},
        metrics,
        "rapid_restart_attempt",
    )

    # Expect 409 (SESSION_IN_PROGRESS) or 429 (RAPID_RESTART_COOLDOWN)
    if restart_resp is None:
        # This is the expected path — 409/429 means the gate is working
        status = metrics.step_failures.get("rapid_restart_attempt", 0)
        if status in (409, 429):
            # Gate correctly triggered — mark as expected behavior
            metrics.error_codes = [c for c in metrics.error_codes if "rapid_restart_attempt" not in c]
            metrics.error_codes.append("rapid_restart_attempt:GATE_OK")


async def run_grinder(client: httpx.AsyncClient, api_url: str, metrics: UserMetrics) -> None:
    """Archetype 4: completes 3 competencies back-to-back."""
    slugs = [
        COMPETENCIES[metrics.user_index % len(COMPETENCIES)],
        COMPETENCIES[(metrics.user_index + 1) % len(COMPETENCIES)],
        COMPETENCIES[(metrics.user_index + 2) % len(COMPETENCIES)],
    ]

    all_ok = True
    for slug in slugs:
        ok = await run_assessment_session(client, api_url, metrics, slug)
        if not ok:
            all_ok = False
            break  # Stop on first failure (could be rate limit)

    aura = await _get(client, f"{api_url}/api/aura/me", metrics.jwt, metrics, "aura_get")
    if aura:
        metrics.aura_score = aura.get("total_score")
        metrics.badge_tier = aura.get("badge_tier")
        if all_ok:
            metrics.completed_full_journey = True


ARCHETYPE_RUNNERS = {
    "fast": run_fast,
    "slow": run_slow,
    "dropoff": run_dropoff,
    "rapid_restart": run_rapid_restart,
    "grinder": run_grinder,
}


# ── Per-user full journey ─────────────────────────────────────────────────────

async def run_user_journey(
    i: int,
    user_id: str,
    jwt: str,
    api_url: str,
    dry_run: bool,
) -> UserMetrics:
    archetype = ARCHETYPES[i % 5]
    metrics = UserMetrics(archetype=archetype, user_index=i, user_id=user_id, jwt=jwt)

    # Increase timeouts for slow archetype
    timeout = httpx.Timeout(120.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        # Profile creation
        profile_resp = await _post(
            client,
            f"{api_url}/api/profiles/me",
            jwt,
            {
                "username": f"{SIM_PREFIX}{i}",
                "display_name": f"Sim User {i}",
                "account_type": "volunteer",
                "visible_to_orgs": False,
                "is_public": True,
                "languages": [],
                "social_links": {},
            },
            metrics,
            "profile_create",
        )

        if profile_resp is None:
            # Profile may already exist (idempotency) — check if it's a 409
            status = metrics.step_failures.get("profile_create", 0)
            if status not in (409, 200):
                return metrics
            # Clear the failure — existing profile is fine
            if status == 409:
                del metrics.step_failures["profile_create"]
                metrics.error_codes = [c for c in metrics.error_codes if "profile_create" not in c]

        if dry_run:
            return metrics

        # Run archetype-specific journey
        runner = ARCHETYPE_RUNNERS[archetype]
        await runner(client, api_url, metrics)

    return metrics


# ── Concurrency orchestration ─────────────────────────────────────────────────

async def run_batch(
    batch: list[tuple[int, str, str]],
    api_url: str,
    dry_run: bool,
) -> list[UserMetrics]:
    """Run a batch of users concurrently. Each tuple: (i, user_id, jwt)."""
    tasks = [
        run_user_journey(i, user_id, jwt, api_url, dry_run)
        for i, user_id, jwt in batch
    ]
    return list(await asyncio.gather(*tasks, return_exceptions=False))


async def orchestrate(
    users_data: list[tuple[int, str, str]],
    api_url: str,
    batch_size: int,
    dry_run: bool,
) -> list[UserMetrics]:
    all_metrics: list[UserMetrics] = []
    total = len(users_data)

    for start in range(0, total, batch_size):
        batch = users_data[start : start + batch_size]
        batch_num = start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} users)...")
        results = await run_batch(batch, api_url, dry_run)
        all_metrics.extend(results)

    return all_metrics


# ── Report ────────────────────────────────────────────────────────────────────

def build_report(all_metrics: list[UserMetrics]) -> dict[str, Any]:
    n = len(all_metrics)
    if n == 0:
        return {"error": "no metrics collected"}

    completed = [m for m in all_metrics if m.completed_full_journey]
    dropped = [m for m in all_metrics if m.archetype == "dropoff"]
    fast_users = [m for m in all_metrics if m.archetype == "fast"]
    gaming_flagged = [m for m in fast_users if m.gaming_flags_triggered]

    # Error rate by endpoint
    endpoint_errors: dict[str, list[int]] = {}
    endpoint_calls: dict[str, int] = {}
    for m in all_metrics:
        for step, latencies in m.latencies_ms.items():
            endpoint_calls[step] = endpoint_calls.get(step, 0) + len(latencies)
        for step, code in m.step_failures.items():
            endpoint_errors.setdefault(step, []).append(code)

    error_rate_by_endpoint = {}
    for step, codes in endpoint_errors.items():
        total_calls = endpoint_calls.get(step, len(codes))
        rate = len(codes) / total_calls * 100 if total_calls > 0 else 0
        error_rate_by_endpoint[step] = f"{rate:.1f}%"

    # Mean AURA
    aura_scores = [m.aura_score for m in all_metrics if m.aura_score is not None]
    mean_aura = statistics.mean(aura_scores) if aura_scores else None
    stddev_aura = statistics.stdev(aura_scores) if len(aura_scores) > 1 else None

    # Badge distribution
    badge_dist: dict[str, int] = {}
    for m in all_metrics:
        if m.badge_tier:
            badge_dist[m.badge_tier] = badge_dist.get(m.badge_tier, 0) + 1

    # Mean questions
    all_questions = [m.questions_answered for m in all_metrics if m.questions_answered > 0]
    mean_questions = statistics.mean(all_questions) if all_questions else 0

    # P95 latency by endpoint
    p95_latency: dict[str, str] = {}
    for step in endpoint_calls:
        all_lats: list[int] = []
        for m in all_metrics:
            all_lats.extend(m.latencies_ms.get(step, []))
        if all_lats:
            all_lats.sort()
            p95_idx = int(len(all_lats) * 0.95)
            p95_latency[step] = f"{all_lats[min(p95_idx, len(all_lats)-1)]}ms"

    # 5xx errors
    five_xx = []
    for m in all_metrics:
        for step, code in m.step_failures.items():
            if isinstance(code, int) and code >= 500:
                five_xx.append(f"{step}:{code}")

    # Unexpected errors (not 409/429/402/422)
    expected_codes = {409, 429, 402, 422}
    unexpected: list[str] = []
    for m in all_metrics:
        for step, code in m.step_failures.items():
            if isinstance(code, int) and code not in expected_codes and code >= 400:
                if "GATE_OK" not in step:
                    unexpected.append(f"user_{m.user_index}[{m.archetype}] {step}:{code}")

    # Drop-off rate by archetype
    dropoff_by_archetype: dict[str, str] = {}
    for arch in ARCHETYPES.values():
        arch_users = [m for m in all_metrics if m.archetype == arch]
        if arch_users:
            dropped_count = sum(1 for m in arch_users if not m.completed_full_journey)
            rate = dropped_count / len(arch_users) * 100
            dropoff_by_archetype[arch] = f"{rate:.0f}%"

    return {
        "users_simulated": n,
        "completion_rate": f"{len(completed)/n*100:.1f}%",
        "drop_off_rate_by_archetype": dropoff_by_archetype,
        "error_rate_by_endpoint": error_rate_by_endpoint,
        "mean_aura_score": round(mean_aura, 2) if mean_aura is not None else None,
        "aura_stddev": round(stddev_aura, 2) if stddev_aura is not None else None,
        "badge_distribution": badge_dist,
        "mean_questions_to_convergence": round(mean_questions, 2),
        "p95_latency_by_endpoint": p95_latency,
        "gaming_flags_triggered": f"{len(gaming_flagged)} ({len(gaming_flagged)/max(len(fast_users),1)*100:.0f}% of fast-archetype users)",
        "five_xx_errors": len(five_xx),
        "unexpected_errors_top5": unexpected[:5],
    }


def print_report(report: dict[str, Any]) -> None:
    print("\n" + "=" * 55)
    print("  VOLAURA BEHAVIORAL SIMULATION REPORT")
    print("=" * 55)
    print(f"  Users simulated:              {report['users_simulated']}")
    print(f"  Completion rate:              {report['completion_rate']}")
    print(f"  Mean AURA score:              {report['mean_aura_score']} (stddev: {report['aura_stddev']})")
    print(f"  Mean questions to convergence:{report['mean_questions_to_convergence']}")
    print(f"  Gaming flags triggered:       {report['gaming_flags_triggered']}")
    print(f"  5xx errors:                   {report['five_xx_errors']}")
    print()
    print("  Drop-off rate by archetype:")
    for arch, rate in report["drop_off_rate_by_archetype"].items():
        print(f"    {arch:<18} {rate}")
    print()
    print("  Error rate by endpoint:")
    for ep, rate in report["error_rate_by_endpoint"].items():
        print(f"    {ep:<28} {rate}")
    print()
    print("  Badge distribution:")
    for tier, count in sorted(report["badge_distribution"].items()):
        print(f"    {tier:<12} {count}")
    print()
    print("  P95 latency by endpoint:")
    for ep, lat in report["p95_latency_by_endpoint"].items():
        print(f"    {ep:<28} {lat}")
    print()
    if report["unexpected_errors_top5"]:
        print("  Unexpected errors (top 5):")
        for err in report["unexpected_errors_top5"]:
            print(f"    {err}")
    else:
        print("  Unexpected errors: none")
    print("=" * 55)


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="VOLAURA Behavioral Simulation Driver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--users", type=int, default=100, help="Number of users to simulate (max 10000)")
    parser.add_argument("--batch-size", type=int, default=10, help="Concurrent users per batch")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Output JSON path (default: scripts/sim_results_<timestamp>.json)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Create users + profiles only, no assessments")
    parser.add_argument("--cleanup", action="store_true", help="Delete all sim_user_* accounts and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Validation
    if args.users > 10_000:
        print("ERROR: --users cannot exceed 10000", file=sys.stderr)
        sys.exit(1)

    if args.batch_size < 1:
        print("ERROR: --batch-size must be at least 1", file=sys.stderr)
        sys.exit(1)

    admin = get_admin_client()

    # Cleanup mode
    if args.cleanup:
        confirm = input(f"Delete all accounts matching *{SIM_EMAIL_DOMAIN}? [yes/no]: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return
        print("Deleting sim users...")
        deleted = delete_sim_users(admin)
        print(f"Deleted {deleted} sim users.")
        return

    # Safety gate for large runs
    if args.users > 1_000:
        confirm = input(
            f"About to create {args.users} test users in Supabase. Continue? [yes/no]: "
        ).strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = args.output_json or f"scripts/sim_results_{timestamp}.json"

    print(f"\nVOLAURA Behavioral Simulation")
    print(f"  Users: {args.users} | Batch: {args.batch_size} | API: {args.api_url}")
    print(f"  Dry run: {args.dry_run} | Output: {output_path}")
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Create users
    print(f"Creating {args.users} sim users in Supabase auth...")
    users_data: list[tuple[int, str, str]] = []
    failed_create = 0

    for i in range(args.users):
        result = create_sim_user(admin, i)
        if result:
            user_id, jwt = result
            users_data.append((i, user_id, jwt))
        else:
            failed_create += 1

        if (i + 1) % 10 == 0 or i == args.users - 1:
            print(f"  Created {i+1}/{args.users} (failures: {failed_create})")

    print(f"\nUser creation complete: {len(users_data)} ok, {failed_create} failed")

    if not users_data:
        print("No users created — aborting.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("Dry run mode — skipping assessments.")
        print(f"Users created: {len(users_data)}")
        print(f"Run without --dry-run to execute full journey.")
        return

    # Run journeys
    t_start = time.monotonic()
    print(f"\nRunning behavioral journeys ({len(users_data)} users, batch_size={args.batch_size})...")

    all_metrics = asyncio.run(
        orchestrate(users_data, args.api_url, args.batch_size, dry_run=False)
    )

    elapsed = time.monotonic() - t_start
    print(f"\nJourneys complete: {elapsed:.1f}s total")

    # Build and print report
    report = build_report(all_metrics)
    print_report(report)

    # Serialize metrics to JSON
    output = {
        "metadata": {
            "users_requested": args.users,
            "users_created": len(users_data),
            "batch_size": args.batch_size,
            "api_url": args.api_url,
            "dry_run": args.dry_run,
            "timestamp": timestamp,
            "elapsed_seconds": round(elapsed, 2),
        },
        "report": report,
        "per_user": [
            {
                "user_index": m.user_index,
                "user_id": m.user_id,
                "archetype": m.archetype,
                "completed_full_journey": m.completed_full_journey,
                "sessions_completed": m.sessions_completed,
                "questions_answered": m.questions_answered,
                "aura_score": m.aura_score,
                "badge_tier": m.badge_tier,
                "gaming_flags_triggered": m.gaming_flags_triggered,
                "stop_reason": m.stop_reason,
                "step_failures": m.step_failures,
                "error_codes": m.error_codes,
                "latencies_ms": {
                    step: {
                        "p50": sorted(lats)[len(lats) // 2] if lats else None,
                        "p95": sorted(lats)[int(len(lats) * 0.95)] if lats else None,
                        "count": len(lats),
                    }
                    for step, lats in m.latencies_ms.items()
                },
            }
            for m in all_metrics
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved: {output_path}")


if __name__ == "__main__":
    main()
