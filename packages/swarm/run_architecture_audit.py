"""
Swarm evaluation: Volaura Architecture Audit
Agents attack the current architecture. Find what breaks at 10x scale.
Run: python -m packages.swarm.run_architecture_audit
"""
import asyncio
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

env_path = Path(__file__).parent.parent.parent / "apps" / "api" / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            import os
            os.environ.setdefault(key.strip(), val.strip())

from packages.swarm import SwarmEngine, SwarmConfig, StakesLevel
from packages.swarm.types import DomainTag, PathDefinition

ARCHITECTURE_SUMMARY = """
VOLAURA ARCHITECTURE (current state, 2026-03-24):

BACKEND (FastAPI, 3,774 lines, 39 Python files):
- 9 API routers: assessment (IRT/CAT), profiles, auth, aura, badges, events, organizations, verification, activity
- Pure-Python IRT/CAT assessment engine (3PL model, EAP ability estimation, no numpy/scipy)
- BARS scoring for open-ended answers (LLM-evaluated via Gemini 2.5 Flash)
- Anti-gaming heuristics (rapid answers, copy-paste detection, timing anomalies)
- Per-request Supabase async client via Depends() (critical for RLS isolation)
- Rate limiting: slowapi IN-MEMORY (leaky bucket, per-IP + per-user)
- Security: HSTS, CSP, X-Frame-Options headers. JWT validated server-side.
- LLM: Gemini 2.5 Flash primary, OpenAI fallback (gated by env)
- Embeddings: Gemini text-embedding-004 (768-dim), vector search via Supabase RPC
- No ORM. No Celery. No Redis. No background jobs.
- HOSTING: Railway (~$8/mo), single instance

FRONTEND (Next.js 14, 8,294 lines, ~90 TypeScript files):
- App Router only, locale-first routing: /[locale]/path
- Route groups: (auth), (public), (dashboard) — layout composition
- ~45 components: assessment (9), aura (4), dashboard (3), landing (8), events (2), profile (5), layout (4), ui (3)
- State: TanStack Query 5 (server), Zustand 5 (client), React Hook Form + Zod (forms)
- i18n: react-i18next, AZ primary / EN secondary
- Styling: Tailwind CSS 4, Framer Motion, shadcn/ui base
- PWA: @ducanh2912/next-pwa
- API client: INTERIM manual fetch wrapper (TODO: replace with @hey-api/openapi-ts generated)
- HOSTING: Vercel free tier

DATABASE (Supabase PostgreSQL + pgvector):
- 13 migrations, 626 lines SQL
- Tables: profiles, competencies, questions, assessment_sessions, aura_scores, badges, organizations, events, behavior_signals, volunteer_embeddings, expert_verifications
- RLS enabled on all user-facing tables
- pgvector(768) for Gemini embeddings
- All vector ops via RPC functions (never PostgREST)
- 230 lines of RPC helpers: calculate_aura_score(), match_volunteers(), verify_skill()

TESTING:
- Backend: 9 test files, 1,250 lines (pytest + async)
- Frontend: ZERO test files. Not a single component test.
- E2E: ZERO. No Playwright/Cypress.
- CI/CD: NONE. Tests exist as files, never run automatically.

KNOWN GAPS:
- Rate limiter in-memory (won't survive multi-instance)
- No background job queue (LLM calls per-request)
- Matching engine is a stub
- Interim API client (manual types, not generated)
- No monitoring/observability beyond loguru
- Assessment CAT state in JSONB (resume-safe but not replicated)
"""


async def main():
    engine = SwarmEngine()

    config = SwarmConfig(
        question=f"""ARCHITECTURE AUDIT for Volaura.

You are a senior infrastructure/security/scaling engineer reviewing this architecture.
Find what breaks at 10x users (5,000 concurrent), what's a security risk, what's over-engineered, and what's missing.

{ARCHITECTURE_SUMMARY}

EVALUATE: Given the constraints (single founder, $50/mo budget, AI CTO, Azerbaijan market, 6-month runway), which approach to fixing these issues maximizes survivability?""",

        paths={
            "fix_testing_first": PathDefinition(
                name="Fix testing infrastructure first (CI/CD + frontend tests + E2E)",
                description="Add Vitest for frontend, Playwright for E2E, GitHub Actions CI pipeline. No feature work until green pipeline exists. Testing prevents regressions as codebase grows.",
                best_case="Every commit verified. Regressions caught before deploy. Confidence to refactor grows.",
                worst_case="2 weeks spent on infra, no features shipped, users don't notice 'better testing'.",
                effort="2 sprints (10-14 days), $0 extra cost (GitHub Actions free tier)",
            ),
            "fix_security_first": PathDefinition(
                name="Fix security gaps first (rate limiter, auth hardening, CSP, monitoring)",
                description="Move rate limiter to Redis (or Supabase Edge). Add request signing. Audit all RLS policies manually. Add Sentry for monitoring. Security before features.",
                best_case="System hardened before first B2B client (Pasha Bank). Security audit pass.",
                worst_case="Over-engineering for 0 users. Redis adds $5-10/mo cost. No revenue to justify spend.",
                effort="1 sprint, +$5-10/mo for Redis/Sentry",
            ),
            "fix_api_client_first": PathDefinition(
                name="Fix API type safety first (generate types from OpenAPI, replace interim client)",
                description="Run pnpm generate:api. Replace all manual types/hooks with generated code. Eliminate the #1 source of frontend-backend type mismatches. Quick win, high impact.",
                best_case="Zero type mismatch bugs. Frontend development 3x faster with autocomplete.",
                worst_case="OpenAPI schema has gaps → generated types are incomplete → need manual overrides anyway.",
                effort="1-2 days, $0 cost",
            ),
            "ship_first_fix_later": PathDefinition(
                name="Ship to production first, fix architecture in v2",
                description="Deploy what exists. Get real users. Real user feedback > hypothetical architecture improvements. Fix what actually breaks, not what might break.",
                best_case="First users this week. Real feedback drives priorities. Architecture debt is known and managed.",
                worst_case="Security incident with real user data. Regression breaks assessment flow. No tests = no confidence to fix anything.",
                effort="1-2 days to deploy, ongoing debt management",
            ),
        },

        stakes=StakesLevel.HIGH,
        domain=DomainTag.ARCHITECTURE,
        context="Pre-launch architecture review. Founder is non-technical. CTO is AI (Claude). First B2B client pitch (Pasha Bank) expected within 2 weeks. Budget: $50/mo. No employees. Azerbaijan market.",
        constraints="$50/mo budget. Single FastAPI instance. No DevOps person. Supabase free tier. Vercel free tier. Must not over-engineer for 0 users but must not ship insecure code to a bank client demo.",
        timeout=90,
    )

    print("\n" + "="*70)
    print("SWARM EVALUATION: Architecture Audit")
    print("="*70 + "\n")

    report = await engine.decide(config)

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\nRecommendation: {report.winner}")
    print(f"Score: {report.winner_score}/50")
    consensus = getattr(report, 'consensus_pct', None) or (getattr(report.divergence, 'consensus_strength', 0) if report.divergence else 0)
    print(f"Consensus: {consensus}")
    print(f"Agents: {len(report.agent_results)}")
    print(f"Cost: ${report.total_cost_estimate:.4f}")

    if report.synthesis:
        print(f"\nSynthesis:\n{report.synthesis}")

    print("\n--- Agent Votes ---")
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        print(f"  {r.model:30s} → {r.winner:30s} (confidence: {r.confidence:.1f})")
        if r.concerns:
            for path, concern in r.concerns.items():
                print(f"    [{path}]: {concern}")

    # Innovations
    print("\n--- Agent Innovations ---")
    for r in report.agent_results:
        if r.innovation:
            print(f"  [{r.model}]: {r.innovation}")
        else:
            try:
                raw = json.loads(r.raw_response) if r.raw_response else {}
                innov = raw.get("innovation", "")
                if innov and innov not in ("null", ""):
                    print(f"  [{r.model}]: {innov}")
            except (json.JSONDecodeError, TypeError):
                pass

    # Save
    output_path = Path(__file__).parent / "architecture_audit_result.json"
    innovations = {}
    for r in report.agent_results:
        innov = r.innovation
        if not innov:
            try:
                raw = json.loads(r.raw_response) if r.raw_response else {}
                innov = raw.get("innovation", "")
            except:
                pass
        if innov and innov not in ("null", ""):
            innovations[r.model] = innov

    output_data = {
        "recommendation": report.winner,
        "score": report.winner_score,
        "consensus": consensus,
        "agents": len(report.agent_results),
        "cost": report.total_cost_estimate,
        "votes": {r.model: r.winner for r in report.agent_results},
        "concerns": {r.model: r.concerns for r in report.agent_results if r.concerns},
        "innovations": innovations,
        "synthesis": str(report.synthesis) if report.synthesis else "",
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_path = Path(__file__).parent / "architecture_audit_summary.md"
    lines = [
        "# Swarm Evaluation: Volaura Architecture Audit",
        f"**Date:** 2026-03-24",
        f"**Agents:** {len(report.agent_results)}",
        f"**Cost:** ${report.total_cost_estimate:.4f}",
        "",
        f"## Recommendation: {report.winner} — {report.winner_score}/50",
        f"Consensus: {consensus}",
        "",
        "## Synthesis",
        str(report.synthesis) if report.synthesis else "N/A",
        "",
        "## Votes",
    ]
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        lines.append(f"- **{r.model}** → {r.winner} (confidence: {r.confidence:.1f})")

    if innovations:
        lines.append("\n## Innovations")
        for model, innov in innovations.items():
            lines.append(f"- **{model}**: {innov}")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nResults saved: {output_path}")
    print(f"Summary saved: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
