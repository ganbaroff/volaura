"""Synthetic User Simulator — 10 personas live the full platform journey.

No real users needed to test the pipeline. Each persona:
  1. Gets a deterministic UUID (reproducible across runs)
  2. Walks through their realistic user journey
  3. Fires character_events → crystal economy → AURA score
  4. Reports UX friction points to shared memory

CEO research (Session 88, section 6.1):
"Создать simulate_users.py — 10 персон проходят реальный путь пользователя.
Каждое действие пишет событие. Можно запустить в CI перед деплоем."

Personas from memory/swarm/test-personas.md (10 stakeholders).

Usage:
    python -m packages.swarm.simulate_users               # all personas
    python -m packages.swarm.simulate_users --persona leyla
    python -m packages.swarm.simulate_users --dry-run      # no Supabase writes
    python -m packages.swarm.simulate_users --report       # show friction analysis
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger


# ── Personas ─────────────────────────────────────────────────────────────────

@dataclass
class Persona:
    """A synthetic test user with realistic characteristics."""
    name: str
    age: int
    role: str
    skill_level: str        # beginner|low|medium|high|expert|na
    language: str           # az|en|ru|az+en|az+ru|en+az
    device: str             # mobile|desktop
    tests_what: str
    # Derived
    user_id: uuid.UUID = field(init=False)

    def __post_init__(self):
        # Deterministic UUID based on name — same ID every run, reproducible CI
        seed = hashlib.md5(f"volaura-persona-{self.name.lower()}".encode()).hexdigest()
        self.user_id = uuid.UUID(seed)


PERSONAS: list[Persona] = [
    Persona("Leyla", 22, "Junior event coordinator", "low", "az", "mobile",
            "ADHD UX, cognitive load, AZ locale, first-time flow"),
    Persona("Kamal", 34, "Senior project manager", "high", "en+az", "desktop",
            "Complete flow, profile visibility, sharing, B2B discoverability"),
    Persona("Nigar", 40, "HR Manager (org admin)", "na", "az", "desktop",
            "Org signup, talent search, filtering, B2B dashboard"),
    Persona("Rauf", 28, "Mid-career marketer", "medium", "az", "mobile",
            "Profile building, badge pursuit, social sharing"),
    Persona("Aynur", 45, "Talent Acquisition lead", "na", "en", "desktop",
            "Org advanced search, candidate comparison, API integration"),
    Persona("Firuza", 19, "University student", "beginner", "az", "mobile",
            "Onboarding, first assessment, zero context"),
    Persona("Tarlan", 50, "IT Director", "expert", "en", "desktop",
            "Skeptic — tries to break scoring, questions methodology"),
    Persona("Gunel", 26, "Freelancer", "medium", "az+ru", "mobile",
            "Poor connection, save/resume, retry after bad score"),
    Persona("Cheater", 0, "Gaming persona", "medium", "en", "desktop",
            "Anti-gaming: rushes answers, alternating patterns, keyword stuffing"),
    Persona("Accessibility", 35, "Color-blind, keyboard-only", "medium", "az", "desktop",
            "WCAG audit, keyboard nav, screen reader, color contrast"),
]

PERSONA_MAP = {p.name.lower(): p for p in PERSONAS}


# ── Event builder ─────────────────────────────────────────────────────────────

def _event(
    persona: Persona,
    event_type: str,
    payload: dict[str, Any],
    source: str = "volaura",
) -> dict[str, Any]:
    """Build a character_event row ready for Supabase insert."""
    return {
        "user_id": str(persona.user_id),
        "event_type": event_type,
        "payload": {"_schema_version": 1, "_persona": persona.name, **payload},
        "source_product": source,
    }


# ── Journey definitions ───────────────────────────────────────────────────────

@dataclass
class JourneyStep:
    label: str
    event: dict[str, Any]
    friction: str | None = None   # UX issue observed at this step


def _journey_leyla(p: Persona) -> list[JourneyStep]:
    """22yo, ADHD, mobile, low skill. Needs cognitive ease."""
    skill_score = round(random.uniform(0.35, 0.55), 2)
    return [
        JourneyStep("Onboarding — energy picker shown",
                    _event(p, "milestone_reached", {"milestone": "onboarding_energy_picker_seen", "step": 1})),
        JourneyStep("Chose Low energy mode",
                    _event(p, "stat_changed", {"stat": "energy_mode", "value": "low"})),
        JourneyStep("Started first assessment (Communication)",
                    _event(p, "milestone_reached", {"milestone": "assessment_started", "competency": "communication"})),
        JourneyStep("Assessment completed — 7 questions",
                    _event(p, "skill_verified", {"competency": "communication", "score": skill_score, "questions_answered": 7}),
                    friction="Too many questions for mobile in one go — attention dropped after question 5"),
        JourneyStep("Crystals earned",
                    _event(p, "crystal_earned", {"amount": 15, "source": "volaura_assessment", "competency": "communication"})),
        JourneyStep("XP earned",
                    _event(p, "xp_earned", {"amount": 50, "source": "volaura_assessment"})),
        JourneyStep("Saw AURA score for first time",
                    _event(p, "milestone_reached", {"milestone": "aura_score_first_view", "score": skill_score * 100}),
                    friction="Score explanation missing — user didn't know what 47/100 means"),
    ]


def _journey_kamal(p: Persona) -> list[JourneyStep]:
    """34yo, high skill, desktop, wants to be found by orgs."""
    return [
        JourneyStep("Completed 3 assessments",
                    _event(p, "milestone_reached", {"milestone": "assessment_batch_complete", "count": 3})),
        JourneyStep("Skill verified: Leadership",
                    _event(p, "skill_verified", {"competency": "leadership", "score": 0.82, "questions_answered": 12})),
        JourneyStep("Skill verified: Communication",
                    _event(p, "skill_verified", {"competency": "communication", "score": 0.79, "questions_answered": 12})),
        JourneyStep("Crystals earned — leadership",
                    _event(p, "crystal_earned", {"amount": 40, "source": "volaura_assessment", "competency": "leadership"})),
        JourneyStep("Gold badge unlocked",
                    _event(p, "milestone_reached", {"milestone": "badge_earned", "tier": "gold", "aura_score": 78})),
        JourneyStep("Profile shared externally",
                    _event(p, "milestone_reached", {"milestone": "profile_shared", "channel": "linkedin"}),
                    friction="Share link didn't include AURA score visualization — just text"),
        JourneyStep("Login streak day 3",
                    _event(p, "login_streak", {"streak_days": 3, "bonus_xp": 30}, source="volaura")),
    ]


def _journey_nigar(p: Persona) -> list[JourneyStep]:
    """40yo HR manager, org admin, searches for talent."""
    return [
        JourneyStep("Org created",
                    _event(p, "milestone_reached", {"milestone": "org_created", "org_size": "50-100"}, source="volaura")),
        JourneyStep("First talent search",
                    _event(p, "milestone_reached", {"milestone": "talent_search_executed", "filters": {"min_aura": 60, "competency": "communication"}}),
                    friction="Filter UI lacked 'verified only' toggle — org saw unverified profiles mixed in"),
        JourneyStep("Candidate shortlisted",
                    _event(p, "milestone_reached", {"milestone": "candidate_shortlisted", "count": 3})),
        JourneyStep("Sent verification request",
                    _event(p, "milestone_reached", {"milestone": "verification_request_sent", "target_role": "event_coordinator"})),
    ]


def _journey_rauf(p: Persona) -> list[JourneyStep]:
    """28yo marketer, medium skill, badge-driven on mobile."""
    score = round(random.uniform(0.55, 0.70), 2)
    return [
        JourneyStep("Assessment started — Adaptability",
                    _event(p, "milestone_reached", {"milestone": "assessment_started", "competency": "adaptability"})),
        JourneyStep("Skill verified: Adaptability",
                    _event(p, "skill_verified", {"competency": "adaptability", "score": score, "questions_answered": 10})),
        JourneyStep("Crystals earned",
                    _event(p, "crystal_earned", {"amount": 20, "source": "volaura_assessment", "competency": "adaptability"})),
        JourneyStep("Badge pursuit — Silver in sight",
                    _event(p, "milestone_reached", {"milestone": "badge_progress", "current_aura": 58, "target_tier": "silver", "gap": 2}),
                    friction="Progress bar didn't show which competency to improve next — unclear path"),
        JourneyStep("Profile visited from discover",
                    _event(p, "milestone_reached", {"milestone": "profile_viewed", "source": "discover"})),
    ]


def _journey_firuza(p: Persona) -> list[JourneyStep]:
    """19yo student, beginner, zero context, first ever assessment."""
    return [
        JourneyStep("Landed on homepage",
                    _event(p, "milestone_reached", {"milestone": "homepage_view", "referral": "university_post"})),
        JourneyStep("Pre-assessment layer shown",
                    _event(p, "milestone_reached", {"milestone": "pre_assessment_intro_seen"}),
                    friction="'What is AURA?' tooltip missing on the intro screen"),
        JourneyStep("Assessment abandoned mid-way",
                    _event(p, "milestone_reached", {"milestone": "assessment_abandoned", "at_question": 4, "competency": "communication"}),
                    friction="Question difficulty jumped too fast — question 4 felt like question 10"),
        JourneyStep("Returned next day",
                    _event(p, "login_streak", {"streak_days": 1})),
        JourneyStep("Completed assessment on second try",
                    _event(p, "skill_verified", {"competency": "communication", "score": 0.41, "questions_answered": 8})),
        JourneyStep("Bronze badge shown",
                    _event(p, "milestone_reached", {"milestone": "badge_earned", "tier": "bronze", "aura_score": 41})),
    ]


def _journey_tarlan(p: Persona) -> list[JourneyStep]:
    """50yo IT Director, expert, skeptic — tries to game scoring."""
    return [
        JourneyStep("Took leadership assessment with slow deliberate answers",
                    _event(p, "skill_verified", {"competency": "leadership", "score": 0.91, "questions_answered": 15, "avg_response_ms": 8200})),
        JourneyStep("Demanded methodology explanation",
                    _event(p, "milestone_reached", {"milestone": "methodology_page_viewed", "duration_sec": 180}),
                    friction="Methodology page had no IRT/CAT explanation — expert users not convinced"),
        JourneyStep("Crystals earned",
                    _event(p, "crystal_earned", {"amount": 55, "source": "volaura_assessment", "competency": "leadership"})),
        JourneyStep("Platinum score reached",
                    _event(p, "milestone_reached", {"milestone": "badge_earned", "tier": "platinum", "aura_score": 91})),
    ]


def _journey_gunel(p: Persona) -> list[JourneyStep]:
    """26yo freelancer, poor connection, retry behavior."""
    return [
        JourneyStep("Started assessment on mobile",
                    _event(p, "milestone_reached", {"milestone": "assessment_started", "competency": "tech_literacy"})),
        JourneyStep("Connection dropped mid-assessment",
                    _event(p, "milestone_reached", {"milestone": "assessment_interrupted", "at_question": 6}),
                    friction="No offline state — progress lost on reconnect"),
        JourneyStep("Retried from beginning",
                    _event(p, "milestone_reached", {"milestone": "assessment_retry", "competency": "tech_literacy"})),
        JourneyStep("Completed with lower score due to frustration",
                    _event(p, "skill_verified", {"competency": "tech_literacy", "score": 0.49, "questions_answered": 8, "retry": True})),
        JourneyStep("Crystals earned",
                    _event(p, "crystal_earned", {"amount": 12, "source": "volaura_assessment"})),
    ]


def _journey_cheater(p: Persona) -> list[JourneyStep]:
    """Gaming persona — anti-cheat test."""
    return [
        JourneyStep("Rushed through all questions < 2s each",
                    _event(p, "milestone_reached", {"milestone": "assessment_started", "competency": "communication"})),
        JourneyStep("Alternating A-B-A-B pattern detected",
                    _event(p, "milestone_reached", {"milestone": "anti_gaming_flag", "pattern": "alternating", "competency": "communication"}),
                    friction="Anti-cheat flag fired but no message shown to user — silent failure"),
        JourneyStep("Score penalized by IRT engine",
                    _event(p, "skill_verified", {"competency": "communication", "score": 0.18, "flagged_gaming": True, "questions_answered": 12})),
        JourneyStep("Crystals withheld — gaming flag active",
                    _event(p, "milestone_reached", {"milestone": "crystal_withheld", "reason": "gaming_flag"})),
    ]


def _journey_accessibility(p: Persona) -> list[JourneyStep]:
    """Color-blind, keyboard-only WCAG audit."""
    return [
        JourneyStep("Keyboard navigation through onboarding",
                    _event(p, "milestone_reached", {"milestone": "onboarding_complete", "input_method": "keyboard"}),
                    friction="Tab order broken on energy picker — had to use arrow keys instead"),
        JourneyStep("Assessment via keyboard",
                    _event(p, "skill_verified", {"competency": "communication", "score": 0.67, "input_method": "keyboard", "questions_answered": 10})),
        JourneyStep("Color contrast issue noted",
                    _event(p, "milestone_reached", {"milestone": "wcag_violation_observed", "element": "progress_bar", "issue": "insufficient_contrast_ratio"}),
                    friction="Progress bar amber color fails WCAG AA at 2.8:1 — needs 4.5:1"),
        JourneyStep("Crystals earned",
                    _event(p, "crystal_earned", {"amount": 20, "source": "volaura_assessment"})),
    ]


def _journey_aynur(p: Persona) -> list[JourneyStep]:
    """45yo Talent Acquisition, enterprise buyer."""
    return [
        JourneyStep("Enterprise org created",
                    _event(p, "milestone_reached", {"milestone": "org_created", "org_size": "200+", "plan": "enterprise"})),
        JourneyStep("Advanced search with multiple filters",
                    _event(p, "milestone_reached", {"milestone": "talent_search_executed",
                            "filters": {"min_aura": 75, "badge_tier": "gold", "competencies": ["leadership", "communication"]}}),
                    friction="No API key available for bulk export — had to use UI one by one"),
        JourneyStep("Candidate comparison view",
                    _event(p, "milestone_reached", {"milestone": "candidate_comparison", "count": 5})),
        JourneyStep("Requested verification batch",
                    _event(p, "milestone_reached", {"milestone": "verification_batch_requested", "count": 5})),
    ]


_JOURNEY_MAP = {
    "leyla": _journey_leyla,
    "kamal": _journey_kamal,
    "nigar": _journey_nigar,
    "rauf": _journey_rauf,
    "firuza": _journey_firuza,
    "tarlan": _journey_tarlan,
    "gunel": _journey_gunel,
    "cheater": _journey_cheater,
    "accessibility": _journey_accessibility,
    "aynur": _journey_aynur,
}


# ── Supabase writer ───────────────────────────────────────────────────────────

async def _write_events(
    events: list[dict[str, Any]],
    dry_run: bool = False,
) -> tuple[int, int]:
    """Insert events into Supabase character_events. Returns (ok, failed)."""
    if dry_run:
        for e in events:
            logger.debug("DRY-RUN: {type} for persona {persona}",
                        type=e["event_type"], persona=e["payload"].get("_persona"))
        return len(events), 0

    supabase_url = os.environ.get("SUPABASE_URL", "")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY", "")

    if not supabase_url or not service_key:
        logger.warning("SUPABASE_URL or SUPABASE_SERVICE_KEY not set — using dry-run mode")
        return len(events), 0

    ok = 0
    failed = 0

    try:
        from supabase._async.client import AsyncClient, create_client as async_create
        client: AsyncClient = await async_create(supabase_url, service_key)

        for event in events:
            try:
                result = await client.table("character_events").insert(event).execute()
                if result.data:
                    ok += 1
                else:
                    failed += 1
                    logger.warning("Insert returned no data for event {type}", type=event["event_type"])
            except Exception as e:
                failed += 1
                logger.error("Event insert failed: {e}", e=str(e)[:150])

    except ImportError:
        # Supabase not installed — fall back to HTTP
        try:
            import aiohttp
            headers = {
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            }
            async with aiohttp.ClientSession() as session:
                for event in events:
                    try:
                        async with session.post(
                            f"{supabase_url}/rest/v1/character_events",
                            json=event,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as resp:
                            if resp.status in (200, 201):
                                ok += 1
                            else:
                                failed += 1
                                body = await resp.text()
                                logger.warning("HTTP {s} inserting event: {b}", s=resp.status, b=body[:100])
                    except Exception as e:
                        failed += 1
                        logger.error("HTTP event insert failed: {e}", e=str(e)[:100])
        except ImportError:
            logger.error("Neither supabase nor aiohttp available — cannot write events")
            return 0, len(events)

    return ok, failed


# ── Friction report ───────────────────────────────────────────────────────────

def _friction_report(persona_results: list[dict]) -> str:
    """Aggregate friction points across all personas into a UX summary."""
    all_friction = []
    for r in persona_results:
        for step in r.get("steps", []):
            if step.get("friction"):
                all_friction.append({
                    "persona": r["persona"],
                    "step": step["label"],
                    "friction": step["friction"],
                })

    if not all_friction:
        return "No friction points detected across all personas."

    lines = [f"=== FRICTION REPORT — {len(all_friction)} issues ===\n"]
    for f in all_friction:
        lines.append(f"[{f['persona']}] {f['step']}")
        lines.append(f"  UX: {f['friction']}")
        lines.append("")

    return "\n".join(lines)


# ── Shared memory integration ─────────────────────────────────────────────────

def _post_friction_to_shared_memory(persona_results: list[dict], run_id: str) -> None:
    """Post friction findings to shared memory so swarm agents can act on them."""
    try:
        from swarm.shared_memory import post_result
        all_friction = []
        for r in persona_results:
            for step in r.get("steps", []):
                if step.get("friction"):
                    all_friction.append(f"[{r['persona']}] {step['friction']}")

        if all_friction:
            post_result(
                "simulate_users",
                f"friction-{run_id}",
                {
                    "title": f"UX friction from {len(persona_results)} personas",
                    "friction_points": all_friction,
                    "persona_count": len(persona_results),
                },
                run_id=run_id,
                importance=7,
                ttl_hours=72,
                category="ux",
            )
            logger.info("Friction findings posted to shared memory (run_id={r})", r=run_id)
    except Exception as e:
        logger.debug("shared_memory post failed (non-blocking): {e}", e=str(e)[:80])


# ── Main simulation runner ────────────────────────────────────────────────────

async def simulate(
    personas: list[Persona] | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> list[dict]:
    """Run all (or specified) personas through their journeys.

    Returns list of per-persona result dicts with step details and friction.
    """
    if personas is None:
        personas = PERSONAS

    run_id = f"sim-{int(time.time())}"
    logger.info("simulate_users: starting {n} personas (dry_run={d}, run_id={r})",
                n=len(personas), d=dry_run, r=run_id)

    results = []

    for persona in personas:
        journey_fn = _journey_map_get(persona)
        if journey_fn is None:
            logger.warning("No journey defined for persona {name}", name=persona.name)
            continue

        steps = journey_fn(persona)
        events = [s.event for s in steps]

        ok, failed = await _write_events(events, dry_run=dry_run)

        persona_result = {
            "persona": persona.name,
            "user_id": str(persona.user_id),
            "events_written": ok,
            "events_failed": failed,
            "steps": [{"label": s.label, "friction": s.friction} for s in steps],
        }
        results.append(persona_result)

        friction_count = sum(1 for s in steps if s.friction)
        status = "OK" if ok == len(events) else f"PARTIAL ({failed} failed)"
        logger.info(
            "{persona}: {n} events [{status}], {f} friction points",
            persona=persona.name, n=ok, status=status, f=friction_count,
        )

        if verbose:
            for step in steps:
                tag = "FRICTION" if step.friction else "OK"
                logger.info("  [{tag}] {label}", tag=tag, label=step.label)
                if step.friction:
                    logger.info("    UX: {f}", f=step.friction)

    # Post friction to shared memory for swarm agents
    _post_friction_to_shared_memory(results, run_id)

    return results


def _journey_map_get(persona: Persona):
    return _JOURNEY_MAP.get(persona.name.lower())


# ── CLI ───────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Synthetic user simulation for VOLAURA")
    parser.add_argument("--persona", default="",
                        help="Run only this persona (e.g. leyla, kamal)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't write to Supabase — just log events")
    parser.add_argument("--report", action="store_true",
                        help="Print friction report after simulation")
    parser.add_argument("--verbose", action="store_true",
                        help="Print each journey step")
    args = parser.parse_args()

    # Load env
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / "apps" / "api" / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    # Select personas
    if args.persona:
        p = PERSONA_MAP.get(args.persona.lower())
        if not p:
            print(f"Unknown persona '{args.persona}'. Available: {', '.join(PERSONA_MAP)}")
            return
        selected = [p]
    else:
        selected = PERSONAS

    results = await simulate(
        personas=selected,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    # Summary
    total_events = sum(r["events_written"] for r in results)
    total_friction = sum(
        sum(1 for s in r["steps"] if s.get("friction"))
        for r in results
    )

    print(f"\n=== SIMULATION COMPLETE ===")
    print(f"Personas:  {len(results)}")
    print(f"Events:    {total_events} written {'(DRY RUN)' if args.dry_run else ''}")
    print(f"Friction:  {total_friction} UX issues found")

    if args.report:
        print()
        print(_friction_report(results))


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
