"""
Full 3-phase audit by the 14-model swarm:
  Phase 1: Analyze the roadmap — find problems in our plan
  Phase 2: Audit what we built — compare plan vs reality
  Phase 3: Best path forward — solve all identified problems
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.swarm.meta_15models import load_all_providers

PHASE_1_PROMPT = """You are auditing a project roadmap. Find problems, gaps, risks.

## ROADMAP (what we PLANNED to build)

VOLAURA: Verified volunteer platform for Azerbaijan. $50/mo budget. 6-week timeline.

Session 1-4: Backend (FastAPI + Supabase + IRT assessment engine) — DONE
Session 5-10: Frontend (Next.js 14 + auth + assessment UI + AURA scores) — DONE
Session 11-12: Design system + Stitch integration — DONE
Session 13: Org dashboard + event wizard + org discovery — DONE
Session 14 (NEXT): E2E integration test + deploy to Vercel/Railway — NOT STARTED

SWARM ENGINE (built this session instead of Session 14):
- Universal multi-model decision engine (packages/swarm/)
- 14 working models from 8 families via 3 API keys (2 free + 1 cheap)
- Weighted voting + conditional debate + LLM synthesis
- Self-learning calibration + persistent memory
- Tournament architecture designed but not implemented

WHAT'S BLOCKING LAUNCH:
1. Database migrations not run (supabase/ALL_MIGRATIONS_COMBINED.sql)
2. No deployment (Vercel + Railway not configured)
3. No E2E test (registration -> assessment -> AURA -> badge)
4. GEMINI_API_KEY set but BARS evaluation not tested with real AZ text
5. Embedding pipeline not triggered
6. 0 real users have tested the platform

## YOUR TASK
Find problems in this roadmap. Specifically:
1. What's the biggest risk to launching in 6 weeks?
2. Did we make the right decision building the swarm engine before deploying Volaura?
3. What's missing from the roadmap that should be there?
4. What will break when we try to deploy?

Respond with JSON:
{
  "evaluator": "model_name",
  "biggest_risk": "one sentence",
  "was_swarm_right_decision": true/false,
  "swarm_reasoning": "why yes or no",
  "missing_from_roadmap": ["list of gaps"],
  "will_break_on_deploy": ["list of predicted failures"],
  "priority_order": ["what to do first, second, third"],
  "innovation": "ONE idea nobody considered yet, actionable in 1 session",
  "confidence": 0.0
}"""

PHASE_2_PROMPT = """You are auditing what was actually BUILT vs what was PLANNED.

## WHAT WE PLANNED (start of session)
- Session 13: Org Launch Bundle (event wizard, org dashboard, discovery page)
- Session 14: E2E test + deploy preview
- DSP v4.0: Upgrade from pseudo-debate to real parallel agents

## WHAT WE ACTUALLY BUILT (this session)
1. Session 13 deliverables: COMPLETED (event wizard, org dashboard, i18n, TanStack hooks)
2. Session 14: NOT STARTED (scope changed to swarm engine)
3. DSP v4.0 live test: COMPLETED with 5 Claude haiku agents
4. Swarm engine (packages/swarm/): BUILT from scratch
   - 2366 lines Python, 15 files
   - 5 providers -> expanded to 14 working models from 8 families
   - Weighted voting, conditional debate, LLM synthesis, self-scaling
   - 6 benchmark runs, 100% success rate achieved
   - 3 meta-evaluations (swarm evaluated itself)
5. API keys stored + allocated by swarm decision
6. Research: MoA, ACL 2025, NeurIPS 2025, RouteLLM, RouterBench — best practices applied
7. Tournament architecture: designed by 14 models, not implemented

## METRICS
- Code written: ~2500 lines (swarm engine) + ~500 lines (Session 13 UI)
- Benchmarks run: 6
- Models tested: 57 (15 working)
- Research papers analyzed: 5
- Bugs found by swarm: risk dimension ambiguity, k-ahead voting flaw, PM synthesis gap
- Real Volaura decisions made by engine: 0
- Code deployed to production: 0

## YOUR TASK
Honest comparison. Was this session productive or scope creep?
1. What was the ROI of building the swarm engine this session?
2. What's the opportunity cost (what DIDN'T we do)?
3. Is the swarm engine production-ready or still prototype?
4. What quality issues exist in the code?
5. Grade this session: A (excellent) to F (wasted)

Respond with JSON:
{
  "evaluator": "model_name",
  "session_grade": "A/B/C/D/F",
  "grade_reasoning": "why",
  "roi_of_swarm": "was it worth building",
  "opportunity_cost": "what we lost by not doing Session 14",
  "production_ready": true/false,
  "quality_issues": ["list of code/architecture problems"],
  "what_worked": ["list of things that went well"],
  "what_failed": ["list of things that went wrong"],
  "innovation": "ONE idea for making next session 2x more productive",
  "confidence": 0.0
}"""

PHASE_3_PROMPT = """Based on the roadmap analysis and session audit, propose the BEST PATH FORWARD.

## CURRENT STATE
- Volaura backend + frontend: BUILT but NOT DEPLOYED
- Swarm engine: BUILT (14 models, 8 families, 100% success rate) but NOT USED for real decisions
- Database: migrations NOT RUN
- Users: ZERO
- Budget: $50/mo, ~$36 remaining for LLM
- Timeline: 6 weeks to launch (already used ~3 weeks building)
- Team: Yusif (founder, non-technical) + Claude (CTO AI)

## PROBLEMS IDENTIFIED
1. Scope creep: built swarm engine instead of deploying Volaura
2. 0 calibration data (swarm can't learn without real decisions)
3. No deployment pipeline (manual deploy only)
4. Database migrations untested
5. No E2E test of critical path
6. Tournament architecture designed but not coded
7. AZ text evaluation untested with real Gemini
8. 3 weeks remaining of 6-week timeline

## YOUR TASK
Propose the optimal path for the next 3 weeks (remaining timeline).
Be specific: what to do in each session, in what order, and why.

RULES:
- Each step must be completable in 1 session (~2-3 hours)
- Steps must be ordered by dependency (can't deploy before migrations)
- Swarm engine should be USED for decisions, not just built more
- Launch date must be met
- Be ruthlessly honest about what to CUT if timeline is tight

Respond with JSON:
{
  "evaluator": "model_name",
  "proposed_sessions": [
    {"session": 14, "goal": "what to accomplish", "deliverable": "concrete output", "uses_swarm": true/false, "hours": 2}
  ],
  "what_to_cut": ["features to defer past launch"],
  "critical_path": ["minimum steps to reach launch"],
  "swarm_integration_plan": "how to start using the engine for real decisions",
  "launch_date_feasible": true/false,
  "launch_risk": "biggest risk to launching on time",
  "innovation": "ONE idea to accelerate the timeline",
  "confidence": 0.0
}"""


async def run_phase(providers, prompt, phase_name):
    """Run one phase across all providers."""
    print(f"\n{'=' * 70}")
    print(f"PHASE: {phase_name}")
    print(f"{'=' * 70}")
    print(f"Launching {len(providers)} agents...")

    start = time.monotonic()
    tasks = [p.safe_evaluate(prompt, temperature=0.7) for p in providers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_ms = int((time.monotonic() - start) * 1000)

    successes = []
    for provider, result in zip(providers, results):
        model = provider.get_model_name()
        if isinstance(result, dict) and result.get("json_valid") and not result.get("error"):
            successes.append({"model": model, "result": result})
        else:
            err = ""
            if isinstance(result, Exception):
                err = str(result)[:60]
            elif isinstance(result, dict):
                err = result.get("error", "?")[:60]
            print(f"  [x] {model:40s} | {err}")

    print(f"  Success: {len(successes)}/{len(providers)} ({total_ms}ms)")
    return successes


def print_phase1(successes):
    print(f"\n--- ROADMAP AUDIT ---")
    risks = {}
    missing = {}
    deploy_breaks = {}

    for s in successes:
        m = s["model"][:25]
        r = s["result"]
        risk = r.get("biggest_risk", "?")[:100]
        swarm_right = r.get("was_swarm_right_decision", "?")
        grade_items = r.get("missing_from_roadmap", [])
        breaks = r.get("will_break_on_deploy", [])
        priority = r.get("priority_order", [])
        innovation = r.get("innovation", "")

        print(f"\n  [{m}] swarm_right={swarm_right}")
        print(f"    Risk: {risk}")
        print(f"    Missing: {', '.join(str(x)[:50] for x in grade_items[:3])}")
        print(f"    Breaks: {', '.join(str(x)[:50] for x in breaks[:3])}")
        print(f"    Priority: {' -> '.join(str(x)[:30] for x in priority[:4])}")
        if innovation:
            print(f"    Innovation: {innovation[:150]}")

        # Count votes
        swarm_key = "yes" if swarm_right else "no"
        risks[risk[:50]] = risks.get(risk[:50], 0) + 1
        for item in grade_items:
            k = str(item)[:50]
            missing[k] = missing.get(k, 0) + 1
        for item in breaks:
            k = str(item)[:50]
            deploy_breaks[k] = deploy_breaks.get(k, 0) + 1

    print(f"\n  CONSENSUS - was swarm right decision?")
    yes_count = sum(1 for s in successes if s["result"].get("was_swarm_right_decision"))
    no_count = len(successes) - yes_count
    print(f"    YES: {yes_count} | NO: {no_count}")

    if missing:
        print(f"\n  TOP MISSING (by votes):")
        for item, count in sorted(missing.items(), key=lambda x: -x[1])[:5]:
            print(f"    [{count}x] {item}")

    if deploy_breaks:
        print(f"\n  PREDICTED DEPLOY FAILURES:")
        for item, count in sorted(deploy_breaks.items(), key=lambda x: -x[1])[:5]:
            print(f"    [{count}x] {item}")


def print_phase2(successes):
    print(f"\n--- SESSION AUDIT ---")
    grades = {}
    for s in successes:
        m = s["model"][:25]
        r = s["result"]
        grade = r.get("session_grade", "?")
        grades[grade] = grades.get(grade, 0) + 1
        roi = r.get("roi_of_swarm", "?")[:100]
        cost = r.get("opportunity_cost", "?")[:100]
        prod = r.get("production_ready", "?")
        innovation = r.get("innovation", "")

        print(f"\n  [{m}] Grade: {grade} | Production: {prod}")
        print(f"    ROI: {roi}")
        print(f"    Opportunity cost: {cost}")
        if r.get("quality_issues"):
            print(f"    Issues: {', '.join(str(x)[:40] for x in r['quality_issues'][:3])}")
        if innovation:
            print(f"    Innovation: {innovation[:150]}")

    print(f"\n  GRADE DISTRIBUTION: {dict(sorted(grades.items()))}")


def print_phase3(successes):
    print(f"\n--- BEST PATH FORWARD ---")
    all_sessions = {}
    cuts = {}
    innovations = []

    for s in successes:
        m = s["model"][:25]
        r = s["result"]
        feasible = r.get("launch_date_feasible", "?")
        risk = r.get("launch_risk", "?")[:100]
        sessions = r.get("proposed_sessions", [])
        cut_items = r.get("what_to_cut", [])
        innovation = r.get("innovation", "")

        print(f"\n  [{m}] Launch feasible: {feasible}")
        print(f"    Risk: {risk}")
        for sess in sessions[:5]:
            sn = sess.get("session", "?")
            goal = sess.get("goal", "?")[:60]
            uses = "swarm" if sess.get("uses_swarm") else "manual"
            print(f"    S{sn}: {goal} [{uses}]")

        for item in cut_items:
            k = str(item)[:50]
            cuts[k] = cuts.get(k, 0) + 1

        if innovation:
            innovations.append({"model": m, "idea": innovation})

    if cuts:
        print(f"\n  CONSENSUS - WHAT TO CUT:")
        for item, count in sorted(cuts.items(), key=lambda x: -x[1])[:5]:
            print(f"    [{count}x] {item}")

    feasible_count = sum(1 for s in successes if s["result"].get("launch_date_feasible"))
    print(f"\n  LAUNCH FEASIBLE: {feasible_count}/{len(successes)} say YES")

    if innovations:
        print(f"\n  INNOVATIONS:")
        for inn in innovations[:5]:
            print(f"    [{inn['model']}] {inn['idea'][:150]}")


async def main():
    print("=" * 70)
    print("FULL 3-PHASE AUDIT BY 14-MODEL SWARM")
    print("=" * 70)

    providers = load_all_providers()
    print(f"Loaded {len(providers)} models")

    # Phase 1: Roadmap analysis
    p1 = await run_phase(providers, PHASE_1_PROMPT, "1 - ROADMAP PROBLEMS")
    print_phase1(p1)

    # Phase 2: Session audit
    p2 = await run_phase(providers, PHASE_2_PROMPT, "2 - SESSION AUDIT")
    print_phase2(p2)

    # Phase 3: Best path forward
    p3 = await run_phase(providers, PHASE_3_PROMPT, "3 - BEST PATH FORWARD")
    print_phase3(p3)

    # Save all results
    out = Path(__file__).parent / "full_audit_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "phase1_roadmap": [s["result"] for s in p1],
            "phase2_session": [s["result"] for s in p2],
            "phase3_path": [s["result"] for s in p3],
        }, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'=' * 70}")
    print(f"Full audit saved to {out}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
