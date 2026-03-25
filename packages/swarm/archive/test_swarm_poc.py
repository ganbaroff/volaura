"""
Hybrid Swarm Proof-of-Concept — Phase 0
========================================
Architecture: Gemini 2.5 Flash evaluators (5 parallel) + Claude synthesis
Decision: "What should Session 14 start with?"

Usage:
  1. Add GEMINI_API_KEY to apps/api/.env
  2. pip install google-genai python-dotenv
  3. python packages/swarm/test_swarm.py

Output: Full DSP v4.0 format — consensus, divergence, winner, confidence.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Load .env from apps/api/.env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / "apps" / "api" / ".env")
except ImportError:
    pass  # dotenv optional — set GEMINI_API_KEY manually

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"

# ─────────────────────────────────────────────
# DECISION SEED
# ─────────────────────────────────────────────
DECISION = {
    "question": "What should Session 14 start with?",
    "context": (
        "Volaura is a verified competency platform for Azerbaijan volunteers. "
        "Backend (FastAPI) + Frontend (Next.js 14) are built. DB migrations pending. "
        "Session 13 complete: Org dashboard, event wizard, org discovery, i18n, TanStack hooks. "
        "No deployment yet. No E2E test. Embedding pipeline not triggered. "
        "Budget: $50/mo. Timeline: 6-week launch target. Current date: 2026-03-23."
    ),
    "constraints": (
        "Railway + Vercel (free tiers). Supabase migrations must run before assessment works. "
        "GEMINI_API_KEY not yet set — BARS evaluation blocked until added. "
        "No CI/CD yet. Manual deploy. pgvector 768-dim embeddings needed for talent matching."
    ),
    "stakes": "High",
    "reversibility": "Moderate",
    "affected_files": [
        "supabase/ALL_MIGRATIONS_COMBINED.sql",
        "apps/api/app/routers/assessment.py",
        "apps/api/app/core/assessment/engine.py",
        "apps/web/src/app/[locale]/(dashboard)/",
        "vercel.json",
        "apps/api/Dockerfile",
    ],
}

PATHS = {
    "path_a": {
        "name": "E2E Integration Test First",
        "description": (
            "Run migrations + seed.sql. Then execute the full critical path: "
            "register → assessment → AURA score → badge. Fix all 422/500 errors before any deploy. "
            "Goal: know the backend is production-ready before anyone sees it."
        ),
        "best_case": "All endpoints pass, migration works cleanly, confidence to deploy is high.",
        "worst_case": "Multiple 422 errors found (Pydantic schema mismatches), takes full session to fix.",
        "side_effects": "Delays deploy by 1 session but ships zero regressions.",
        "effort": "M",
        "dependencies": ["supabase/ALL_MIGRATIONS_COMBINED.sql", "apps/api/.env with keys"],
    },
    "path_b": {
        "name": "Vercel Deploy Preview First",
        "description": (
            "Deploy frontend to Vercel and backend to Railway immediately. "
            "Get a live preview URL for stakeholder feedback. "
            "Test in production-like environment rather than local."
        ),
        "best_case": "Live URL in 2 hours. Real feedback before over-engineering anything.",
        "worst_case": "Deploy fails due to missing env vars or build errors. GEMINI_API_KEY missing blocks BARS.",
        "side_effects": "Exposes an untested backend publicly. First impressions matter.",
        "effort": "M",
        "dependencies": ["vercel.json", "apps/api/Dockerfile", "Railway account", "all env vars"],
    },
    "path_c": {
        "name": "Embedding Pipeline First",
        "description": (
            "Trigger Supabase Edge Function or pg_cron to generate Gemini embeddings for all profiles. "
            "This unblocks talent matching (the core differentiator). "
            "Run migrations first as prerequisite."
        ),
        "best_case": "Talent matching works from day 1. Org discovery page becomes functional.",
        "worst_case": "GEMINI_API_KEY still missing — embeddings can't generate. Wasted session.",
        "side_effects": "Requires migrations + GEMINI key. Neither is confirmed ready.",
        "effort": "L",
        "dependencies": [
            "supabase/functions/ (edge functions)",
            "GEMINI_API_KEY set in env",
            "migrations run",
            "apps/api/app/services/embeddings.py",
        ],
    },
    "path_d": {
        "name": "AURA Coach + Talent Matching UI Wiring",
        "description": (
            "Wire the frontend Talent Discovery UI to real API endpoints. "
            "Connect AURA Coach component to Gemini coaching endpoint. "
            "Parallel: Yusif runs migrations manually while Claude wires UI."
        ),
        "best_case": "Full volunteer journey visible end-to-end in UI. Demo-ready.",
        "worst_case": "API endpoints return 422 because migrations haven't run. UI shows error states.",
        "side_effects": "Creates good demo material but depends on backend being healthy.",
        "effort": "M",
        "dependencies": [
            "apps/web/src/lib/api/ generated types",
            "backend running locally",
            "migration state unknown",
        ],
    },
}

# ─────────────────────────────────────────────
# PERSONA DEFINITIONS
# ─────────────────────────────────────────────
PERSONAS = [
    {
        "id": "leyla",
        "name": "Leyla",
        "description": "Volunteer, 22yo, Baku, mobile-first, AZ native, wants AURA on LinkedIn",
        "lens": "Can I register and get my AURA score today? Is it fast on mobile 4G?",
        "influence": 1.0,
    },
    {
        "id": "attacker",
        "name": "Attacker",
        "description": "Security adversary who knows FastAPI + Supabase + Next.js vulnerabilities",
        "lens": "How do I exploit this? Which path exposes the most attack surface? OWASP top 10.",
        "influence": 1.2,
    },
    {
        "id": "yusif",
        "name": "Yusif",
        "description": "Founder, $50/mo budget, 6-week launch timeline, HR bouquets + LinkedIn growth target",
        "lens": "Does this get us to launch faster? What's the ROI on this session?",
        "influence": 1.0,
    },
    {
        "id": "scaling",
        "name": "Scaling Engineer",
        "description": "Bottleneck analyst, thinks about 10x load",
        "lens": "What breaks at 10x volunteers? Where are the database bottlenecks? Missing indexes?",
        "influence": 1.1,
    },
    {
        "id": "qa",
        "name": "QA Engineer",
        "description": "Test coverage expert, edge cases, regression risk",
        "lens": "What edge cases break each path? What is NOT tested that should be?",
        "influence": 0.9,
    },
]


def build_evaluator_prompt(persona: dict[str, Any]) -> str:
    paths_text = "\n\n".join(
        f"PATH {pid.upper()} — {p['name']}:\n"
        f"  Description: {p['description']}\n"
        f"  Best case: {p['best_case']}\n"
        f"  Worst case: {p['worst_case']}\n"
        f"  Side effects: {p['side_effects']}\n"
        f"  Effort: {p['effort']}\n"
        f"  Dependencies: {', '.join(p['dependencies'])}"
        for pid, p in PATHS.items()
    )

    return f"""You are an independent evaluator for a technical decision about the Volaura project.
You have NOT seen any other evaluator's opinion. Be brutally honest and specific.

ROLE: {persona['name']} — {persona['description']}
YOUR LENS: {persona['lens']}

DECISION: {DECISION['question']}

CONTEXT: {DECISION['context']}

CONSTRAINTS: {DECISION['constraints']}

AFFECTED FILES:
{chr(10).join('  - ' + f for f in DECISION['affected_files'])}

PATHS TO EVALUATE:
{paths_text}

INSTRUCTIONS:
- Score each path 0-10 on EACH dimension (be harsh — 10/10 is near-impossible)
- Write ONE specific concern per path (cite a REAL file/table/endpoint from the context above)
- "I don't know" is valid if you lack context — do NOT invent information
- Your winner must be the path you genuinely believe is best given YOUR specific lens

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "evaluator": "{persona['id']}",
  "scores": {{
    "path_a": {{"technical": 0, "user_impact": 0, "dev_speed": 0, "flexibility": 0, "risk": 0}},
    "path_b": {{"technical": 0, "user_impact": 0, "dev_speed": 0, "flexibility": 0, "risk": 0}},
    "path_c": {{"technical": 0, "user_impact": 0, "dev_speed": 0, "flexibility": 0, "risk": 0}},
    "path_d": {{"technical": 0, "user_impact": 0, "dev_speed": 0, "flexibility": 0, "risk": 0}}
  }},
  "concerns": {{
    "path_a": "specific concern citing real file or dependency",
    "path_b": "specific concern citing real file or dependency",
    "path_c": "specific concern citing real file or dependency",
    "path_d": "specific concern citing real file or dependency"
  }},
  "winner": "path_x",
  "reason": "one sentence citing specific evidence",
  "confidence": 0.0
}}"""


async def call_gemini(persona: dict[str, Any], client: Any) -> dict[str, Any]:
    """Call Gemini 2.5 Flash for one evaluator agent."""
    from google import genai
    from google.genai import types

    prompt = build_evaluator_prompt(persona)

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,  # some variance per evaluator
                max_output_tokens=1024,
            ),
        )
        raw = response.text.strip()
        result = json.loads(raw)
        result["_model"] = "gemini-2.5-flash"
        return result
    except json.JSONDecodeError as e:
        return {
            "evaluator": persona["id"],
            "error": f"JSON parse failed: {e}",
            "raw": response.text[:500] if "response" in dir() else "no response",
            "_model": "gemini-2.5-flash",
        }
    except Exception as e:
        return {
            "evaluator": persona["id"],
            "error": str(e),
            "_model": "gemini-2.5-flash",
        }


def compute_weighted_scores(evaluations: list[dict]) -> dict[str, float]:
    """Aggregate scores across all evaluators using influence weights."""
    influence_map = {p["id"]: p["influence"] for p in PERSONAS}
    path_ids = list(PATHS.keys())
    dimensions = ["technical", "user_impact", "dev_speed", "flexibility", "risk"]

    weighted_totals: dict[str, float] = {p: 0.0 for p in path_ids}
    total_weight = sum(influence_map.values())

    for eval_result in evaluations:
        if "error" in eval_result or "scores" not in eval_result:
            continue
        evaluator_id = eval_result.get("evaluator", "")
        weight = influence_map.get(evaluator_id, 1.0)

        for path_id in path_ids:
            path_scores = eval_result["scores"].get(path_id, {})
            raw_total = sum(path_scores.get(dim, 0) for dim in dimensions)
            weighted_totals[path_id] += (raw_total / 50.0) * weight  # normalize to 0-1

    # Normalize to 0-50 scale
    return {p: round((v / total_weight) * 50, 1) for p, v in weighted_totals.items()}


def detect_divergence(evaluations: list[dict]) -> dict[str, Any]:
    """Find where evaluators disagree most (real signal)."""
    path_ids = list(PATHS.keys())
    winner_votes: dict[str, int] = {p: 0 for p in path_ids}

    for ev in evaluations:
        winner = ev.get("winner")
        if winner in winner_votes:
            winner_votes[winner] += 1

    total_votes = sum(winner_votes.values())
    top_winner = max(winner_votes, key=lambda k: winner_votes[k])
    consensus_pct = winner_votes[top_winner] / max(total_votes, 1)

    return {
        "winner_votes": winner_votes,
        "top_winner": top_winner,
        "consensus_strength": round(consensus_pct, 2),
        "is_genuine_consensus": consensus_pct >= 0.6,
        "split_paths": [p for p, v in winner_votes.items() if v > 0],
    }


async def run_swarm() -> None:
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not set in apps/api/.env")
        print("Add your key and re-run. The swarm evaluators need it.")
        sys.exit(1)

    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)

    print(f"\n🔮 DSP v4.0 Hybrid Swarm — {DECISION['question']}")
    print(f"Stakes: {DECISION['stakes']} | Evaluators: {len(PERSONAS)} Gemini agents | Synthesis: Claude")
    print("━" * 60)
    print(f"Launching {len(PERSONAS)} independent Gemini 2.5 Flash evaluators in parallel...")

    # Launch all evaluators in parallel — no shared context
    tasks = [call_gemini(persona, client) for persona in PERSONAS]
    evaluations = await asyncio.gather(*tasks)

    print(f"✓ All {len(evaluations)} evaluations received\n")

    # Print raw evaluations for synthesis
    print("─── RAW EVALUATIONS (for Claude synthesis) ───")
    for ev in evaluations:
        print(json.dumps(ev, indent=2, ensure_ascii=False))
        print()

    # Compute weighted scores
    weighted_scores = compute_weighted_scores(evaluations)
    divergence = detect_divergence(evaluations)

    print("─── WEIGHTED SCORES ───")
    for path_id, score in sorted(weighted_scores.items(), key=lambda x: -x[1]):
        path_name = PATHS[path_id]["name"]
        marker = " ← WINNER" if path_id == divergence["top_winner"] else ""
        print(f"  {path_id.upper()} — {path_name}: {score}/50{marker}")

    print(f"\n─── DIVERGENCE ───")
    print(f"Winner votes: {divergence['winner_votes']}")
    print(f"Consensus: {divergence['consensus_strength']*100:.0f}% ({divergence['top_winner']})")
    print(f"Genuine consensus: {divergence['is_genuine_consensus']}")
    print("\n[Paste above into Claude for synthesis and DSP v4.0 output]")


if __name__ == "__main__":
    asyncio.run(run_swarm())
