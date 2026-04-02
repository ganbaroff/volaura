#!/usr/bin/env python3
"""Heavy Board Run — nemotron-ultra-253b + deepseek-r1 on growth/gamification/UX topic.

Run from project root:
    apps/api/.venv/Scripts/python.exe packages/swarm/board_heavy_run.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

# UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).parent.parent.parent

# Read .env manually
env: dict[str, str] = {}
env_file = project_root / "apps" / "api" / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()

NVIDIA_KEY = env.get("NVIDIA_API_KEY", "")
GEMINI_KEY = env.get("GEMINI_API_KEY", "")

VOLAURA_CONTEXT = """
VOLAURA — Verified Professional Talent Platform.
NOT a volunteer platform. NOT LinkedIn. A platform where skills are PROVEN through adaptive
AI assessment, not claimed on CVs. Users earn an AURA score (0-100) across 8 competencies.
Organizations search verified talent by score. Azerbaijan + CIS market, collectivist culture.

Founder: Yusif, Baku, solo founder, $50/mo budget, 6-week timeline.
Users: Leyla (22yo, mobile, AZ native), Kamal (34yo, professional), Rauf (28yo, brand-builder).
Orgs: Nigar (HR manager, 50+ team), Aynur (corp talent acquisition, 200+ employees).
Crystal economy: AURA assessment → crystals → Life Simulator (Godot 4 game).
Tech: Next.js 14 + FastAPI + Supabase + Tailwind. $50/mo total infra cost.

What's already decided (don't re-research):
- Supabase Realtime for notifications (WebSocket done)
- No Redis, no microservices, no ORM
- AURA score is public by default (CEO decision, locked)
- Crystal economy ties VOLAURA + Life Simulator + MindShift
- Collectivist AZ culture: group > individual competition
"""

BOARD_PERSONAS = [
    {
        "name": "Strategic Board Director (nemotron-ultra)",
        "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        "lens": """You are a board director with 20+ years in consumer tech growth
        (LinkedIn, Duolingo, Notion). You think in retention loops, viral coefficients,
        and ecosystem moats. You focus on: what creates long-term defensibility?
        What growth mechanic survives a competitor with 100x budget?""",
    },
    {
        "name": "Chief People Officer (nemotron-ultra)",
        "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        "lens": """You are a Chief People Officer with expertise in organizational psychology
        and Azerbaijan/CIS workplace culture. You know that collectivist cultures respond
        to group validation, not individual ranking. You focus on: what gamification
        mechanics INCREASE trust and belonging vs create anxiety and comparison?""",
    },
    {
        "name": "DeepSeek R1 Growth Analyst",
        "model": "deepseek-ai/deepseek-r1-0528",
        "lens": """You are a growth analyst specializing in emerging markets.
        You analyze data patterns, funnel metrics, and behavioral economics.
        You focus on: what specific gamification mechanic would maximize D7 retention
        for professional platforms in collectivist cultures? Give numbers and benchmarks.""",
    },
]

TOPIC = """TOPIC: Growth, Gamification, and User Experience for Volaura.

The team has proposed these mechanics so far (from previous agents):
1. AURA Score Leaderboard (council vote — but criticized as too competitive for AZ culture)
2. Milestone Animations + Share CTA (quick win — badge earn moment)
3. Tribe Streaks & Kudos — 3-person accountability circles with tokens that fade if chain breaks
4. Collective AURA Ladders — Crystal Pools lift group visibility rank
5. Growth Trajectory Badges — "you grew 12 points in 30 days" vs static badge status
6. Silent Kudos & Gratitude Ledger — private non-competitive peer appreciation

YOUR TASK:
As a board-level strategic thinker, evaluate these proposals. Then:
1. Identify the ONE mechanic from this list (or a new one) that has highest ROI for
   a bootstrapped AZ/CIS professional platform at early stage.
2. Explain why specifically — what behavioral mechanism makes it work?
3. What is the single biggest risk nobody has mentioned?
4. What does implementation look like in 1 week (specific files/components)?

Be BRUTALLY honest. If all proposals are mediocre, say so and propose something better.

RESPONSE FORMAT (JSON only, no markdown):
{
    "title": "one-line summary of your recommendation",
    "severity": "high",
    "type": "idea",
    "winning_mechanic": "name of the mechanic you recommend",
    "why_it_works": "behavioral mechanism — 3-4 sentences",
    "biggest_risk_ignored": "what nobody mentioned — 2 sentences",
    "implementation_sketch": "specific files + components + effort estimate",
    "content": "full analysis as plain text string",
    "confidence": 0.0-1.0
}

CRITICAL: content field must be a plain STRING. No nested JSON."""


async def call_heavy_agent(persona: dict) -> dict | None:
    """Call a single heavy NVIDIA model with extended timeout."""
    prompt = f"""{VOLAURA_CONTEXT}

YOUR ROLE: {persona['name']}
YOUR LENS: {persona['lens']}

{TOPIC}"""

    raw = ""
    model = persona["model"]

    print(f"\n[LAUNCHING] {persona['name']} → {model.split('/')[-1]}", flush=True)

    try:
        from openai import AsyncOpenAI
        resp = await asyncio.wait_for(
            AsyncOpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=NVIDIA_KEY,
            ).chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=1500,
            ),
            timeout=120.0,  # 2 minutes — heavy models need time
        )
        raw = resp.choices[0].message.content or ""
        print(f"[OK] {persona['name']} — got {len(raw)} chars", flush=True)
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] {persona['name']} — 120s exceeded", flush=True)
        return None
    except Exception as e:
        print(f"[ERROR] {persona['name']}: {e}", flush=True)
        return None

    if not raw:
        print(f"[EMPTY] {persona['name']}", flush=True)
        return None

    # Parse — try multiple strategies
    try:
        # Strategy 1: strip markdown fences
        text = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        # Strategy 2: extract first {...} block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        data = json.loads(text)
        data["agent"] = persona["name"]
        data["model"] = model
        return data
    except Exception:
        print(f"[JSON FAIL] {persona['name']} — raw excerpt:", flush=True)
        print(raw[:500], flush=True)
        # Return raw text as structured response
        return {
            "agent": persona["name"],
            "model": model,
            "title": f"[RAW — JSON parse failed] {persona['name']}",
            "content": raw[:2000],
            "confidence": 0.5,
        }


async def main():
    if not NVIDIA_KEY:
        print("ERROR: NVIDIA_API_KEY not set in .env", flush=True)
        sys.exit(1)

    print("=" * 60, flush=True)
    print("VOLAURA BOARD — Heavy Model Growth Analysis", flush=True)
    print(f"Models: nemotron-ultra-253b + deepseek-r1-0528", flush=True)
    print(f"Timeout: 120s per agent", flush=True)
    print("=" * 60, flush=True)

    # Run all 3 in parallel
    results = await asyncio.gather(
        *[call_heavy_agent(p) for p in BOARD_PERSONAS],
        return_exceptions=True,
    )

    print("\n" + "=" * 60, flush=True)
    print("BOARD RESULTS", flush=True)
    print("=" * 60, flush=True)

    output = []
    for r in results:
        if isinstance(r, Exception):
            print(f"\n[EXCEPTION]: {r}", flush=True)
            continue
        if r is None:
            continue

        output.append(r)
        print(f"\n{'─'*50}", flush=True)
        print(f"AGENT: {r.get('agent', '?')}", flush=True)
        print(f"MODEL: {r.get('model', '?').split('/')[-1]}", flush=True)
        print(f"TITLE: {r.get('title', '?')}", flush=True)
        print(f"WINNING MECHANIC: {r.get('winning_mechanic', '?')}", flush=True)
        print(f"CONFIDENCE: {r.get('confidence', '?')}", flush=True)
        print(f"\nWHY IT WORKS:", flush=True)
        print(r.get('why_it_works', r.get('content', '')[:500]), flush=True)
        print(f"\nBIGGEST RISK IGNORED:", flush=True)
        print(r.get('biggest_risk_ignored', 'N/A'), flush=True)
        print(f"\nIMPLEMENTATION:", flush=True)
        print(r.get('implementation_sketch', 'N/A'), flush=True)

    # Save results
    out_path = project_root / "memory" / "swarm" / "board-heavy-results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] {out_path}", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("BOARD RUN COMPLETE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
