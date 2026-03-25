"""
MiroFish: LinkedIn Post #2 — Social Media Reaction Simulation
Simulates how 5 audience segments react to the coordinator nepotism post (Azerbaijani).
Answers Yusif's question: "How will management react?"

Run: python -m packages.swarm.run_social_reaction
"""
import asyncio
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Load .env
env_path = Path(__file__).parent.parent.parent / "apps" / "api" / ".env"
if env_path.exists():
    import os
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

from packages.swarm.social_reaction import simulate_reactions

# ─── THE POST ───────────────────────────────────────────────────────────────

POST_AZ = """WUF13-də, COP29-da, CIS Games 2025-də koordinatorlarla çalışdım. Senior Manager kimi koordinatorları idarə etdim. Gördüklərimi bir tərəfə qoyun — sistem necə işləyir, onu danışaq.

Böyük tədbirlərdə koordinator seçimi çox vaxt belədir: "onu tanıyıram", "o mənim köhnə iş yoldaşımdır". Peşəkarlıq yox, əlaqə. Nəticə? Qonaqlar çaşır. Komanda dayanır. Könüllülər öz koordinatorlarını arxadan düzəldir.

Amma problemi yaradan insan deyil — sistemdir. Əgər ölçmə mexanizmi yoxdursa, insanlar tanıdıqları adama güvənir. Bu təbii davranışdır. Günahkar deyil, rasionaldır.

Volaura bunu dəyişir. AURA skoru yalnız könüllüləri ölçmür — koordinatorları da ölçür. Ünsiyyət. Etibarlılıq. Liderlik. Adaptasiya.

Bu "daha bir könüllü platformu" deyil. Bu, peşəkarlıq üçün standartdır.

AI CTO-m Claude ilə birlikdə qururuq. Bunu gizlətmirəm — çünki gücü necə işlətdiyindədir, nə olduğunda yox.

Siz iş həyatınızda əlaqə ilə gəlmiş, amma peşəkar olmayan koordinatorla çalışmısınızmı?
#Volaura #Liderlik #Peşəkarlıq #AzərbaycanIT"""

POST_TRANSLATION = """ENGLISH SUMMARY:
I worked with coordinators at WUF13, COP29, CIS Games 2025 as Senior Manager. Let me set aside what I personally saw and talk about how the system works.

At major events, coordinator selection often goes like this: 'I know him', 'he's my old colleague'. Connections, not professionalism. The result? Guests get confused. The team stalls. Volunteers quietly correct their coordinators from behind the scenes.

But the problem isn't the person — it's the system. If there's no measurement mechanism, people trust whoever they know. This is natural behavior. Not guilty, rational.

Volaura changes this. The AURA score doesn't just measure volunteers — it measures coordinators too. Communication. Reliability. Leadership. Adaptability.

This isn't 'just another volunteer platform'. This is a standard for professionalism.

I'm building it with my AI CTO Claude. I'm not hiding this — because power is in how you use it, not in what it is.

Have you worked with a coordinator who was selected through connections, not competence?
#Volaura #Leadership #Professionalism #AzerbaijanIT"""

AUTHOR_CONTEXT = """
CRITICAL RISK CONTEXT:
Yusif currently works in Azerbaijan's event management sector.
His direct managers and colleagues from WUF13, COP29, and CIS Games 2025 are on LinkedIn.
The post's 'connections not professionalism' critique describes practices that happened at events
where his management team made coordinator selections.
Yusif has NOT named any individuals. The critique is systemic, not personal.
But insiders WILL recognize the pattern he describes.
"""


def print_separator(title=""):
    line = "═" * 70
    if title:
        print(f"\n{line}")
        print(f"  {title}")
        print(line)
    else:
        print(line)


async def main():
    print_separator("MIROFISH: Social Media Reaction Simulation")
    print("Post: LinkedIn Post #2 — Coordinator Nepotism (Azerbaijani)")
    print("Stakes: HIGH (career implications)")
    print("Running simulation...\n")

    report = await simulate_reactions(
        post_text=POST_AZ,
        translation=POST_TRANSLATION,
        author_context=AUTHOR_CONTEXT,
        timeout_seconds=90.0,
    )

    # ─── YUSIF'S MAIN QUESTION: MANAGEMENT REACTION ──────────────────────
    print_separator("MANAGEMENT / SECTOR INSIDERS — YOUR MAIN QUESTION")
    print("These are former managers and colleagues from WUF13, COP29, CIS Games.")
    print("Will they feel personally accused?\n")

    # Extract management-specific insights from synthesis and agent results
    management_insights = []
    for r in report.agent_results:
        concerns_str = str(r.concerns) if r.concerns else ""
        if concerns_str and any(
            kw in concerns_str.lower()
            for kw in ["manag", "insider", "colleague", "former", "event", "cop", "wuf", "cis"]
        ):
            management_insights.append(f"  [{r.model}]: {concerns_str}")

    if management_insights:
        for insight in management_insights[:4]:
            print(insight)
    else:
        # Print top agent concerns about the publish decision
        print("  Agent concerns about publishing:")
        for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True)[:4]:
            if r.concerns:
                print(f"  [{r.model}]: {str(r.concerns)}")

    # ─── PUBLISH RECOMMENDATION ───────────────────────────────────────────
    print_separator("PUBLISH RECOMMENDATION")
    print(f"Winner: {report.winner}")
    print(f"Score:  {report.winner_score}/50 (gate: ≥35 required)")
    consensus = (
        getattr(report, "consensus_pct", None)
        or (
            getattr(report.divergence, "consensus_strength", 0)
            if report.divergence
            else 0
        )
    )
    if isinstance(consensus, float) and consensus <= 1.0:
        print(f"Consensus: {consensus:.0%}")
    else:
        print(f"Consensus: {consensus}")
    print(f"Agents consulted: {len(report.agent_results)}")
    print(f"Cost: ${report.total_cost_estimate:.4f}")

    # ─── FULL SYNTHESIS ───────────────────────────────────────────────────
    if report.synthesis:
        print_separator("AUDIENCE REACTION SYNTHESIS")
        print(report.synthesis)

    # ─── ALL AGENT VOTES ──────────────────────────────────────────────────
    print_separator("AGENT VOTES")
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        concern_str = f"\n    Concern: {str(r.concerns)}" if r.concerns else ""
        print(f"  {r.model:45s} → {r.winner:30s} (confidence: {r.confidence:.1f}){concern_str}")

    # ─── INNOVATION / SPECIFIC REACTION PREDICTIONS ───────────────────────
    print_separator("SPECIFIC REACTION PREDICTIONS (from agents)")
    predictions_found = 0
    for r in report.agent_results:
        try:
            raw = json.loads(r.raw_response) if r.raw_response else {}
            innov = raw.get("innovation", "")
            if innov and innov not in ("null", "", None):
                print(f"\n  [{r.model}]:")
                print(f"  {innov}")
                predictions_found += 1
        except (json.JSONDecodeError, TypeError):
            pass
    if predictions_found == 0:
        print("  (No innovation fields returned — see synthesis above)")

    # ─── SAVE RESULTS ─────────────────────────────────────────────────────
    output_path = Path(__file__).parent / "social_reaction_result.json"
    output_data = {
        "post": "LinkedIn Post #2 — Coordinator Nepotism (AZ)",
        "verdict": report.winner,
        "score": report.winner_score,
        "consensus": str(consensus),
        "agents": len(report.agent_results),
        "cost": report.total_cost_estimate,
        "votes": {r.model: r.winner for r in report.agent_results},
        "concerns": {r.model: str(r.concerns) for r in report.agent_results if r.concerns},
        "synthesis": str(report.synthesis) if report.synthesis else "",
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_path = Path(__file__).parent / "social_reaction_summary.md"
    path_descriptions = {
        "publish_now": "Publish as-is",
        "revise_tone": "Revise tone first",
        "publish_with_disclaimer": "Add systemic framing sentence",
        "delay_and_add_english": "Publish AZ + EN same day",
    }
    lines = [
        "# MiroFish: LinkedIn Post #2 — Audience Reaction Simulation",
        f"**Post:** Coordinator Nepotism (Azerbaijani)",
        f"**Date:** 2026-03-24",
        f"**Agents:** {len(report.agent_results)} | **Cost:** ${report.total_cost_estimate:.4f}",
        "",
        f"## Verdict: {path_descriptions.get(report.winner, report.winner)} — {report.winner_score}/50",
        f"Consensus: {consensus}",
        "",
        "## Full Synthesis",
        str(report.synthesis) if report.synthesis else "N/A",
        "",
        "## Agent Votes",
    ]
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        concern_str = f" | Concern: {str(r.concerns)}" if r.concerns else ""
        lines.append(f"- **{r.model}** → {r.winner} (confidence: {r.confidence:.1f}){concern_str}")

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print_separator()
    print(f"Results saved: {output_path}")
    print(f"Summary saved: {summary_path}")
    print_separator()


if __name__ == "__main__":
    asyncio.run(main())
