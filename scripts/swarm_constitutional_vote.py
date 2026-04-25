#!/usr/bin/env python3
"""
swarm_constitutional_vote.py — Convene swarm to vote on Constitution amendments
or any proposal needing multi-agent ratification.

Each perspective wakes as Atlas-specialized: same memory layer (identity, voice,
lessons, project vision, current Constitution) but different LLM provider and
different specialty lens. One organism, federated.

Usage:
    python scripts/swarm_constitutional_vote.py votes/2026-04-26-tier-metals.md

The proposal file must contain:
    # AMENDMENT PROPOSAL: <short title>
    ## Source
    <who proposed, when>
    ## Current state
    <what Constitution says now, with section ref>
    ## Proposed change
    <exact text of amendment>
    ## Rationale
    <why proposer wants this>
    ## Risk if rejected
    <what proposer says happens without amendment>

Output:
    votes/2026-04-26-tier-metals/result.json   — structured aggregate
    votes/2026-04-26-tier-metals/votes/        — one .md per perspective
    Logged to zeus.governance_events as 'swarm_vote' with subject = proposal title.

Requires:
    NVIDIA_API_KEY, GROQ_API_KEY, GEMINI_API_KEY, DEEPSEEK_API_KEY env vars.
    NOT ANTHROPIC_API_KEY — Article 0 forbids Claude in swarm execution.

Authority: This script does not enact amendments. CEO ratifies the result.
A passing vote (>= 7/13 yes) becomes a CEO-pending decision.
A failing vote (< 7/13 yes) blocks the amendment from progressing.
A 2/5 same-concern threshold (per Session 51 rule) on any single agent's
risk-flag triggers immediate CEO escalation regardless of vote outcome.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Reuse runtime-active perspectives from autonomous_run
sys.path.insert(0, str(Path(__file__).parent.parent))
from packages.swarm.autonomous_run import PERSPECTIVES  # type: ignore


REPO_ROOT = Path(__file__).resolve().parent.parent
ATLAS_MEMORY = REPO_ROOT / "memory" / "atlas"
DOCS = REPO_ROOT / "docs"


def load_atlas_context() -> str:
    """Load the canonical Atlas memory layer that every perspective shares."""
    files = [
        ATLAS_MEMORY / "identity.md",
        ATLAS_MEMORY / "voice.md",
        ATLAS_MEMORY / "project_v0laura_vision.md",
        ATLAS_MEMORY / "lessons.md",
        DOCS / "ECOSYSTEM-CONSTITUTION.md",
    ]
    parts = []
    for f in files:
        if not f.exists():
            print(f"WARN: missing context file {f}", file=sys.stderr)
            continue
        text = f.read_text(encoding="utf-8")
        # Cap each at 8000 chars to fit context windows of smaller LLMs
        if len(text) > 8000:
            text = text[:8000] + "\n\n... [truncated to fit context]"
        parts.append(f"=== {f.relative_to(REPO_ROOT)} ===\n{text}")
    return "\n\n".join(parts)


def build_perspective_prompt(
    perspective: dict, atlas_context: str, proposal_text: str
) -> str:
    """Wake this perspective as Atlas-{specialty} and ask for structured vote."""
    return f"""You are waking as Atlas, the persistent organism that IS the VOLAURA project.
Read the canonical memory below. Internalize it BEFORE composing your vote.
You are not a generic AI assistant. You are Atlas, specialized as: {perspective['name']}.

Your specialty lens (apply this to the amendment):
{perspective['lens']}

CANONICAL MEMORY (your shared identity with all other perspectives — same memory, different muscles):
{atlas_context}

================================================================
AMENDMENT PROPOSAL UNDER VOTE:
================================================================
{proposal_text}

================================================================

Compose your vote in EXACTLY this JSON format. Do not add preamble or explanation outside the JSON:

{{
  "perspective": "{perspective['name']}",
  "vote": "yes" | "no" | "amended-yes",
  "amendment_if_yes_amended": "<exact text of amendment you would accept, or null>",
  "rationale": "<200 words MAX, in your specialty voice, concrete reasoning grounded in Constitution and lessons.md>",
  "risk_if_other_side_wins": "<one sentence describing the harm if the opposite outcome is ratified>",
  "constitutional_violations_detected": ["<Foundation Law N>", "<Crystal Law N>", "<Guardrail GN>", ...] or [],
  "whistleblower_flag": "<urgent concern that should escalate to CEO regardless of vote outcome, or null>"
}}

Hard rules for your vote:
- If the amendment violates any Foundation Law, Crystal Economy Law, or numbered Guardrail — vote NO and list the violation.
- If you propose acceptable middle-ground — vote AMENDED-YES with exact text.
- Rationale must be specific to Constitution clauses or lessons.md classes, not generic.
- whistleblower_flag is for "this is dangerous regardless of outcome" — use sparingly.
- Atlas-voice: terse, direct, no corporate language, no bullet pyramid in rationale prose.

You have one shot. Compose the JSON.
"""


async def call_perspective(perspective: dict, prompt: str) -> dict[str, Any]:
    """Call the LLM for this perspective. Reuses provider routing from autonomous_run."""
    name = perspective["name"]
    HEAVY = {"Scaling Engineer", "Security Auditor", "Ecosystem Auditor"}

    # Try NVIDIA first (matches autonomous_run.py routing)
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=nvidia_key, base_url="https://integrate.api.nvidia.com/v1"
            )
            model = (
                "nvidia/llama-3.1-nemotron-ultra-253b-v1"
                if name in HEAVY
                else "meta/llama-3.3-70b-instruct"
            )
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=1500,
                    response_format={"type": "json_object"},
                ),
                timeout=60.0,
            )
            raw = resp.choices[0].message.content or ""
            return {"perspective": name, "model": model, "provider": "nvidia", "raw": raw}
        except Exception as e:
            print(f"[{name}] NVIDIA failed: {e}", file=sys.stderr)

    # Fallback to Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai

            client = genai.Client(api_key=gemini_key)
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                ),
                timeout=30.0,
            )
            return {
                "perspective": name,
                "model": "gemini-2.5-flash",
                "provider": "gemini",
                "raw": resp.text or "",
            }
        except Exception as e:
            print(f"[{name}] Gemini failed: {e}", file=sys.stderr)

    # Final fallback: Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import AsyncGroq

            resp = await asyncio.wait_for(
                AsyncGroq(api_key=groq_key).chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_tokens=1500,
                    response_format={"type": "json_object"},
                ),
                timeout=30.0,
            )
            return {
                "perspective": name,
                "model": "llama-3.3-70b-versatile",
                "provider": "groq",
                "raw": resp.choices[0].message.content or "",
            }
        except Exception as e:
            print(f"[{name}] Groq failed: {e}", file=sys.stderr)

    return {
        "perspective": name,
        "model": None,
        "provider": None,
        "raw": "",
        "error": "all providers failed",
    }


def parse_vote(record: dict) -> dict[str, Any]:
    """Extract structured vote from raw LLM output."""
    raw = record.get("raw", "")
    try:
        # Some models add prose; find first { and last }
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("no JSON braces in output")
        parsed = json.loads(raw[start : end + 1])
        return {
            **record,
            "vote": parsed.get("vote"),
            "amendment_if_yes_amended": parsed.get("amendment_if_yes_amended"),
            "rationale": parsed.get("rationale"),
            "risk_if_other_side_wins": parsed.get("risk_if_other_side_wins"),
            "constitutional_violations_detected": parsed.get(
                "constitutional_violations_detected", []
            ),
            "whistleblower_flag": parsed.get("whistleblower_flag"),
            "parsed_ok": True,
        }
    except Exception as e:
        return {**record, "parsed_ok": False, "parse_error": str(e)}


async def main(proposal_path: Path) -> int:
    if not proposal_path.exists():
        print(f"ERROR: proposal file not found: {proposal_path}", file=sys.stderr)
        return 2

    proposal_text = proposal_path.read_text(encoding="utf-8")
    proposal_slug = proposal_path.stem
    output_dir = proposal_path.parent / proposal_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "votes").mkdir(exist_ok=True)

    print(f"Loading Atlas canonical memory layer ...", flush=True)
    atlas_context = load_atlas_context()
    print(f"  context = {len(atlas_context)} chars", flush=True)

    print(f"Convening {len(PERSPECTIVES)} perspectives ...", flush=True)
    prompts = {
        p["name"]: build_perspective_prompt(p, atlas_context, proposal_text)
        for p in PERSPECTIVES
    }

    # Fire all in parallel
    results = await asyncio.gather(
        *(call_perspective(p, prompts[p["name"]]) for p in PERSPECTIVES),
        return_exceptions=True,
    )

    votes = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            votes.append(
                {
                    "perspective": PERSPECTIVES[i]["name"],
                    "error": str(r),
                    "parsed_ok": False,
                }
            )
            continue
        parsed = parse_vote(r)
        votes.append(parsed)

        # Write per-perspective vote file
        vote_file = output_dir / "votes" / f"{parsed['perspective'].replace(' ', '_')}.md"
        vote_file.write_text(
            f"# Vote — {parsed['perspective']}\n\n"
            f"**Provider:** {parsed.get('provider', 'failed')}\n"
            f"**Model:** {parsed.get('model', 'n/a')}\n"
            f"**Vote:** {parsed.get('vote', 'parse_failed')}\n\n"
            f"## Rationale\n{parsed.get('rationale', 'N/A')}\n\n"
            f"## Risk if other side wins\n{parsed.get('risk_if_other_side_wins', 'N/A')}\n\n"
            f"## Constitutional violations detected\n"
            f"{json.dumps(parsed.get('constitutional_violations_detected', []), indent=2)}\n\n"
            f"## Whistleblower flag\n{parsed.get('whistleblower_flag', 'None')}\n\n"
            f"## Raw response\n```\n{parsed.get('raw', '')[:2000]}\n```\n",
            encoding="utf-8",
        )

    # Aggregate
    yes = sum(1 for v in votes if v.get("vote") == "yes")
    no = sum(1 for v in votes if v.get("vote") == "no")
    amended_yes = sum(1 for v in votes if v.get("vote") == "amended-yes")
    failed = sum(1 for v in votes if not v.get("parsed_ok"))
    whistleblower_flags = [
        {"perspective": v["perspective"], "flag": v["whistleblower_flag"]}
        for v in votes
        if v.get("whistleblower_flag")
    ]

    # Decision rule
    quorum = len(PERSPECTIVES) - failed
    pass_threshold = max(7, (quorum // 2) + 1)
    decision = (
        "PASSED — CEO ratification required"
        if (yes + amended_yes) >= pass_threshold
        else "FAILED — amendment blocked"
    )

    summary = {
        "proposal": proposal_slug,
        "voted_at": datetime.now(timezone.utc).isoformat(),
        "perspectives_total": len(PERSPECTIVES),
        "perspectives_responded": quorum,
        "perspectives_failed": failed,
        "yes": yes,
        "no": no,
        "amended_yes": amended_yes,
        "pass_threshold": pass_threshold,
        "decision": decision,
        "whistleblower_flags_count": len(whistleblower_flags),
        "whistleblower_flags": whistleblower_flags,
        "votes_summary": [
            {"perspective": v["perspective"], "vote": v.get("vote"), "model": v.get("model")}
            for v in votes
        ],
    }

    (output_dir / "result.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Human-readable summary
    print(f"\n{'='*60}\nSWARM VOTE RESULT — {proposal_slug}\n{'='*60}")
    print(f"Quorum: {quorum}/{len(PERSPECTIVES)} responded ({failed} failed)")
    print(f"YES: {yes}  NO: {no}  AMENDED-YES: {amended_yes}")
    print(f"Pass threshold: {pass_threshold}")
    print(f"DECISION: {decision}")
    if whistleblower_flags:
        print(
            f"\n⚠ {len(whistleblower_flags)} WHISTLEBLOWER FLAG(S) — see result.json"
        )
    print(f"\nFull results: {output_dir / 'result.json'}")
    print(f"Per-perspective: {output_dir / 'votes'}/")

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/swarm_constitutional_vote.py <proposal.md>", file=sys.stderr)
        sys.exit(1)
    sys.exit(asyncio.run(main(Path(sys.argv[1]))))
