#!/usr/bin/env python3
"""Production E2E smoke — real user journey through the bridge path.

Unlike `prod_smoke_test.py` (health + auth-gate only), this walks a full
user flow against the live Railway deployment:

    1. POST /api/auth/from_external  (X-Bridge-Secret) → shared JWT
    2. POST /api/assessment/start                      → session + first question
    3. POST /api/assessment/answer  (loop)             → drive to is_complete
    4. POST /api/assessment/complete/{session_id}      → competency_score, aura_updated
    5. GET  /api/aura/me                               → verify total_score exists

Shadow user is fresh per run (time-seeded standalone_user_id + email), so
the 7-day retest cooldown and 30-min abandoned-session lock never trigger.

Usage:
    VOLAURA_PROD_URL=https://volauraapi-production.up.railway.app \
    EXTERNAL_BRIDGE_SECRET=<same-as-railway> \
    python scripts/prod_smoke_e2e.py

Env vars:
    VOLAURA_PROD_URL         — required, e.g. https://volauraapi-production.up.railway.app
    EXTERNAL_BRIDGE_SECRET   — required, must match Railway
    VOLAURA_SMOKE_COMPETENCY — optional, default 'communication'
    VOLAURA_SMOKE_MAX_Q      — optional, default 10 (safety cap on answer loop)
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid
from typing import Any

import httpx

BASE_URL = os.getenv("VOLAURA_PROD_URL", "").rstrip("/")
BRIDGE_SECRET = os.getenv("EXTERNAL_BRIDGE_SECRET", "")
COMPETENCY = os.getenv("VOLAURA_SMOKE_COMPETENCY", "communication")
MAX_Q = int(os.getenv("VOLAURA_SMOKE_MAX_Q", "10"))
TIMEOUT = 60.0

# Generic answers — non-empty, no HTML, no injection patterns, <5000 chars.
GENERIC_OPEN_ANSWER = (
    "In my experience I focus on clear communication, listening actively, "
    "summarising decisions, and confirming next steps with the team so "
    "everyone is aligned on the shared goal and any blockers."
)


def _ts() -> str:
    return time.strftime("%H:%M:%S", time.gmtime())


def _ok(step: str) -> None:
    print(f"  [OK]   {step}")


def _fail(step: str, reason: str) -> None:
    print(f"  [FAIL] {step}: {reason}")


async def _bridge_signup(client: httpx.AsyncClient) -> tuple[str, str]:
    """Create a fresh shadow user via bridge. Returns (shared_user_id, jwt)."""
    standalone_id = f"smoke-e2e-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    email = f"smoke+{standalone_id}@volaura.app"
    r = await client.post(
        "/api/auth/from_external",
        headers={"X-Bridge-Secret": BRIDGE_SECRET},
        json={
            "standalone_user_id": standalone_id,
            "standalone_project_ref": "smoke_e2e_test",
            "email": email,
            "source_product": "smoke_test",
        },
    )
    if r.status_code != 200:
        raise RuntimeError(f"bridge {r.status_code}: {r.text[:300]}")
    body = r.json()
    return body["shared_user_id"], body["shared_jwt"]


async def _start_assessment(client: httpx.AsyncClient, jwt: str) -> dict[str, Any]:
    r = await client.post(
        "/api/assessment/start",
        headers={"Authorization": f"Bearer {jwt}"},
        json={
            "competency_slug": COMPETENCY,
            "language": "en",
            "role_level": "volunteer",
            "energy_level": "full",
        },
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"start {r.status_code}: {r.text[:500]}")
    return r.json()


def _pick_answer(question: dict[str, Any]) -> str:
    """Return a valid answer for the question type."""
    qtype = (question.get("question_type") or "").lower()
    if qtype == "mcq":
        options = question.get("options") or []
        if options and isinstance(options[0], dict):
            # Option keys are like "A", "B", "C" — use the first one.
            return str(options[0].get("key") or options[0].get("id") or "A")
        return "A"
    # open_ended / sjt / anything else
    return GENERIC_OPEN_ANSWER


async def _answer_loop(
    client: httpx.AsyncClient, jwt: str, session: dict[str, Any]
) -> tuple[int, str]:
    """Submit answers until is_complete or MAX_Q. Returns (answered, session_id)."""
    session_id = session["session_id"]
    next_q = session.get("next_question")
    answered = 0
    for i in range(MAX_Q):
        if not next_q:
            break
        answer = _pick_answer(next_q)
        r = await client.post(
            "/api/assessment/answer",
            headers={"Authorization": f"Bearer {jwt}"},
            json={
                "session_id": session_id,
                "question_id": next_q["id"],
                "answer": answer,
                "response_time_ms": 4500,
            },
        )
        if r.status_code != 200:
            raise RuntimeError(
                f"answer[{i+1}] {r.status_code}: {r.text[:400]}"
            )
        feedback = r.json()
        answered += 1
        sess = feedback.get("session", {})
        if sess.get("is_complete"):
            return answered, session_id
        next_q = sess.get("next_question")
    return answered, session_id


async def _complete(client: httpx.AsyncClient, jwt: str, session_id: str) -> dict[str, Any]:
    r = await client.post(
        f"/api/assessment/complete/{session_id}",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"complete {r.status_code}: {r.text[:400]}")
    return r.json()


async def _get_aura(client: httpx.AsyncClient, jwt: str) -> dict[str, Any] | None:
    r = await client.get(
        "/api/aura/me",
        headers={"Authorization": f"Bearer {jwt}"},
    )
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        raise RuntimeError(f"aura {r.status_code}: {r.text[:300]}")
    return r.json()


async def main() -> int:
    if not BASE_URL:
        print("VOLAURA_PROD_URL not set"); return 2
    if not BRIDGE_SECRET:
        print("EXTERNAL_BRIDGE_SECRET not set"); return 2

    print(f"\nVOLAURA Production E2E Smoke  [{_ts()} UTC]")
    print(f"  Target:     {BASE_URL}")
    print(f"  Competency: {COMPETENCY}\n")

    failures: list[tuple[str, str]] = []
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
        # 1. Bridge signup
        try:
            user_id, jwt = await _bridge_signup(client)
            _ok(f"bridge signup (user_id={user_id[:8]})")
        except Exception as e:
            _fail("bridge-signup", str(e)); failures.append(("bridge-signup", str(e)))
            print("\nFATAL: cannot obtain JWT. Stopping."); return 1

        # 2. Start
        try:
            session = await _start_assessment(client, jwt)
            _ok(f"assessment start (session={session['session_id'][:8]}, first_q={bool(session.get('next_question'))})")
        except Exception as e:
            _fail("assessment-start", str(e)); failures.append(("assessment-start", str(e)))
            return 1

        # 3. Answer loop
        try:
            answered, session_id = await _answer_loop(client, jwt, session)
            _ok(f"answer loop completed {answered} answer(s)")
        except Exception as e:
            _fail("answer-loop", str(e)); failures.append(("answer-loop", str(e)))
            return 1

        # 4. Complete
        try:
            result = await _complete(client, jwt, session_id)
            score = result.get("competency_score")
            aura_updated = result.get("aura_updated")
            _ok(f"complete: score={score}, aura_updated={aura_updated}, flags={result.get('gaming_flags') or '[]'}")
        except Exception as e:
            _fail("complete", str(e)); failures.append(("complete", str(e)))
            return 1

        # 5. AURA fetch
        try:
            aura = await _get_aura(client, jwt)
            if aura is None:
                _fail("aura/me", "404 — AURA not written for this user")
                failures.append(("aura/me", "404"))
            else:
                total = aura.get("total_score")
                tier = aura.get("badge_tier")
                _ok(f"aura/me: total={total}, tier={tier}")
        except Exception as e:
            _fail("aura/me", str(e)); failures.append(("aura/me", str(e)))

    print("\n" + "-" * 60)
    if failures:
        print(f"E2E RESULT: FAILED ({len(failures)} step(s))")
        for step, reason in failures:
            print(f"  - {step}: {reason[:120]}")
        return 1
    print("E2E RESULT: PASSED — full user journey works on prod.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
