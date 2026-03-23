#!/usr/bin/env python3
"""
Decision Simulation Engine — MiroFish-adapted scorer.

This script runs the numerical scoring phase of the DSP algorithm.
It takes agent evaluations as JSON input and produces weighted scores,
margin analysis, and a winner declaration.

Usage:
    python simulate.py --input evaluations.json --output result.json

    Or pipe JSON directly:
    echo '{"paths": [...], "agents": [...], "evaluations": [...]}' | python simulate.py

Input JSON schema:
{
    "decision": "Short description of what we're deciding",
    "stakes": "low|medium|high|critical",
    "paths": [
        {"id": "A", "name": "Path Name", "description": "What this path does"}
    ],
    "agents": [
        {"id": "leyla", "name": "Leyla (Volunteer)", "influence_weight": 1.0}
    ],
    "evaluations": [
        {
            "agent_id": "leyla",
            "path_id": "A",
            "scores": {
                "technical": 7,
                "user_impact": 9,
                "dev_speed": 6,
                "flexibility": 8,
                "risk": 7
            },
            "stance": "support",
            "reasoning": "One sentence why"
        }
    ]
}
"""

import json
import sys
import argparse
from typing import Dict, Any, List


def calculate_weighted_scores(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate weighted path scores from agent evaluations.

    Mirrors MiroFish's sentiment aggregation across simulation rounds,
    but applied to structured scoring dimensions.
    """
    paths = {p["id"]: p for p in data["paths"]}
    agents = {a["id"]: a for a in data["agents"]}

    # Group evaluations by path
    path_evals: Dict[str, List[Dict]] = {p_id: [] for p_id in paths}
    for ev in data["evaluations"]:
        path_evals[ev["path_id"]].append(ev)

    dimensions = ["technical", "user_impact", "dev_speed", "flexibility", "risk"]
    results = {}

    for path_id, evals in path_evals.items():
        if not evals:
            continue

        total_weight = sum(agents[e["agent_id"]]["influence_weight"] for e in evals)

        dim_scores = {}
        for dim in dimensions:
            weighted_sum = sum(
                e["scores"][dim] * agents[e["agent_id"]]["influence_weight"]
                for e in evals
            )
            dim_scores[dim] = round(weighted_sum / total_weight, 2)

        total = round(sum(dim_scores.values()), 2)

        # Stance summary
        stances = {}
        for e in evals:
            stance = e.get("stance", "neutral")
            stances[stance] = stances.get(stance, 0) + 1

        results[path_id] = {
            "path_id": path_id,
            "path_name": paths[path_id]["name"],
            "dimension_scores": dim_scores,
            "total_score": total,
            "max_possible": 50,
            "stances": stances,
            "agent_verdicts": [
                {
                    "agent": agents[e["agent_id"]]["name"],
                    "stance": e.get("stance"),
                    "reasoning": e.get("reasoning", ""),
                    "score": sum(e["scores"].values())
                }
                for e in evals
            ]
        }

    # Sort by total score descending
    ranked = sorted(results.values(), key=lambda x: x["total_score"], reverse=True)

    winner = ranked[0] if ranked else None
    runner_up = ranked[1] if len(ranked) > 1 else None

    margin = round(winner["total_score"] - runner_up["total_score"], 2) if runner_up else 50

    # Margin interpretation (calibrated from MiroFish sentiment convergence thresholds)
    if margin < 3:
        margin_label = "razor-thin — consider human tiebreak"
    elif margin < 5:
        margin_label = "narrow — winner is slightly favored"
    elif margin < 10:
        margin_label = "clear — winner is solidly better"
    else:
        margin_label = "decisive — strong consensus"

    # Check calibration rules
    warnings = []

    # Rule 1: No unanimous votes
    if winner and all(v["stance"] == "support" for v in winner["agent_verdicts"]):
        warnings.append("All agents unanimously support winner — paths may not be diverse enough")

    # Rule 2: Attacker must find vulnerabilities
    attacker_evals = [e for e in data["evaluations"] if e["agent_id"] == "attacker"]
    if attacker_evals and all(e["scores"]["risk"] >= 8 for e in attacker_evals):
        warnings.append("Attacker found no significant risks in any path — simulation may be too shallow")

    return {
        "decision": data.get("decision", ""),
        "stakes": data.get("stakes", "medium"),
        "ranked_paths": [
            {
                "rank": i + 1,
                "is_winner": i == 0,
                **r
            }
            for i, r in enumerate(ranked)
        ],
        "winner": {
            "path_id": winner["path_id"],
            "path_name": winner["path_name"],
            "score": winner["total_score"],
        } if winner else None,
        "margin": margin,
        "margin_label": margin_label,
        "fallback": {
            "path_id": runner_up["path_id"],
            "path_name": runner_up["path_name"],
            "score": runner_up["total_score"],
        } if runner_up else None,
        "warnings": warnings,
    }


def format_output(result: Dict[str, Any]) -> str:
    """Format result as the DSP output block."""
    w = result["winner"]
    fb = result.get("fallback")

    lines = [
        f"🔮 DSP: {result['decision']}",
        "━" * 50,
        f"Stakes: {result['stakes'].upper()} | Margin: {result['margin']} pts ({result['margin_label']})",
        "",
        "📊 Path Scores:",
    ]

    for r in result["ranked_paths"]:
        marker = " ← WINNER" if r["is_winner"] else ""
        lines.append(f"  Path {r['path_id']} — {r['path_name']}: {r['total_score']}/50{marker}")
        dims = r["dimension_scores"]
        lines.append(f"    Tech:{dims['technical']} User:{dims['user_impact']} Speed:{dims['dev_speed']} Flex:{dims['flexibility']} Risk:{dims['risk']}")

    lines.extend([
        "",
        f"🏆 Winner: Path {w['path_id']} ({w['path_name']}) — {w['score']}/50",
    ])

    if fb:
        lines.append(f"🔄 Fallback: Path {fb['path_id']} ({fb['path_name']}) — {fb['score']}/50")

    if result["warnings"]:
        lines.append("")
        lines.append("⚠️ Calibration Warnings:")
        for warn in result["warnings"]:
            lines.append(f"  - {warn}")

    lines.append("━" * 50)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Decision Simulation Scorer")
    parser.add_argument("--input", "-i", help="Input JSON file path")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--format", "-f", choices=["json", "text", "both"], default="both",
                       help="Output format")
    args = parser.parse_args()

    # Read input
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # Calculate
    result = calculate_weighted_scores(data)

    # Output
    if args.format in ("json", "both"):
        json_out = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_out)
        if args.format == "json":
            print(json_out)

    if args.format in ("text", "both"):
        print(format_output(result))


if __name__ == "__main__":
    main()
