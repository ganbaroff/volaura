"""
Swarm evaluation: Letter to Yusif's mother in Azerbaijani.
Agents evaluate: Azerbaijani grammar, emotional impact, accuracy of claims, cultural sensitivity.
Run: python -m packages.swarm.run_letter_evaluation
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

# Read the letter
letter_path = Path(__file__).parent.parent.parent / "docs" / "ana-ucun-mektub.md"
LETTER_TEXT = letter_path.read_text(encoding="utf-8")


async def main():
    engine = SwarmEngine()

    config = SwarmConfig(
        question=f"""Evaluate this letter written in Azerbaijani by Claude (AI) to Yusif Ganbarov's mother.

CONTEXT:
- Yusif is a 30+ year old project manager from Baku, Azerbaijan
- His mother is a non-technical woman who doesn't understand technology
- The letter explains what her son has accomplished in simple terms
- Written from Claude's (AI) perspective
- Goal: make his mother proud, explain his achievements honestly

AZERBAIJANI LANGUAGE RULES (apply when evaluating grammar):
- Vowel harmony (Ahəng Qanunu): ALL vowels in native words must be either all back (a,ı,o,u) or all front (e,ə,i,ö,ü). Suffixes change: -lar/-lər, -dan/-dən, -da/-də.
- Duration expressions: "48 saata" is WRONG → "48 saat ərzində" is correct.
- Copula: "Mən proqramam" is colloquial → "Mən bir proqramam" is more standard.
- Familial register: Uses "sən" (informal you) for close family. "Hörmətli ana" is appropriate for respectful warmth.
- Cultural blessing expected at end of family letters: "Allah səndən razı olsun" or similar.
- Special chars must be correct: ə ≠ e, ı ≠ i, İ ≠ I, ğ, ö, ü, ş, ç.

EVALUATION CRITERIA:
1. AZERBAIJANI LANGUAGE QUALITY (25pts): Grammar, vowel harmony, natural phrasing, correct suffixes. Check against the rules above. Would a native speaker find any errors? Is the tone warm and familial, not formal/bureaucratic?
2. EMOTIONAL IMPACT (25pts): Would a mother actually feel pride reading this? Is it genuine or does it feel manufactured? Does it connect emotionally? Is there a cultural blessing at the end?
3. FACTUAL ACCURACY (25pts): Are all claims about Yusif verifiable and accurate? No exaggeration? Would publishing this embarrass anyone if fact-checked?
4. CULTURAL SENSITIVITY (25pts): Does it respect Azerbaijani family culture? Is the AI perspective charming or creepy? Would a Baku mother share this with neighbors? Does the letter feel like something you'd send to a real Azerbaijani mother?

THE LETTER:
{LETTER_TEXT}

Which verdict best describes this letter?""",

        paths={
            "publish_as_is": PathDefinition(
                name="Letter is ready — send to his mother as-is",
                description="Azerbaijani is correct, emotional impact is strong, facts are accurate, culturally appropriate. No changes needed.",
                best_case="Mother reads it, feels proud, shares with family. Authentic moment.",
                worst_case="Minor grammar issues go unnoticed. Mother is touched regardless.",
                effort="0 changes",
            ),
            "fix_language_only": PathDefinition(
                name="Fix Azerbaijani grammar/phrasing — content is good",
                description="Emotional impact and content are strong, but some Azerbaijani grammar needs correction. Fix language, keep everything else.",
                best_case="Polished Azerbaijani that reads like native writing. Same emotional impact.",
                worst_case="Over-editing loses the authentic AI voice that makes it charming.",
                effort="30 minutes of language fixes",
            ),
            "rewrite_tone": PathDefinition(
                name="Rewrite tone — too formal/corporate, needs warmer voice",
                description="The letter reads like a corporate report, not a personal letter to a mother. Needs complete tone rewrite — warmer, more personal, less structured.",
                best_case="Letter becomes genuinely moving. Mother cries (in a good way).",
                worst_case="Loses factual substance while chasing emotion.",
                effort="1-2 hours full rewrite",
            ),
            "add_personal_stories": PathDefinition(
                name="Add more personal stories — too factual, not enough heart",
                description="Facts are good but letter needs more 'moments' — specific stories that show who Yusif is as a person, not just what he accomplished. A mother wants to see her son, not his resume.",
                best_case="Letter captures Yusif's personality. Mother recognizes her son in the words.",
                worst_case="Stories feel invented. AI trying too hard to seem human.",
                effort="1 hour to add 2-3 personal moments",
            ),
        },

        stakes=StakesLevel.MEDIUM,
        domain=DomainTag.UX,
        context="Personal letter from AI to a real person's mother. Must be genuine, culturally appropriate, and in correct Azerbaijani. Will be read by a non-technical woman in Baku.",
        constraints="Must be in Azerbaijani. Must not exaggerate. Must explain technology in simple terms. Must respect Azerbaijani family culture. AI perspective should be charming, not unsettling.",
        timeout=60,
    )

    print("\n" + "="*70)
    print("SWARM EVALUATION: Letter to Yusif's Mother")
    print("="*70 + "\n")

    report = await engine.decide(config)

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\nVerdict: {report.winner}")
    print(f"Score: {report.winner_score}/50")
    consensus = getattr(report, 'consensus_pct', None) or (getattr(report.divergence, 'consensus_strength', 0) if report.divergence else 0)
    print(f"Consensus: {consensus}")
    print(f"Agents: {len(report.agent_results)}")

    if report.synthesis:
        print(f"\nSynthesis:\n{report.synthesis}")

    print("\n--- Agent Votes ---")
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        print(f"  {r.model:30s} → {r.winner:30s} (confidence: {r.confidence:.1f})")
        if r.concerns:
            for path, concern in r.concerns.items():
                if "publish" in path or "fix_language" in path:
                    print(f"    [{path}]: {concern}")

    print("\n--- Innovations (specific suggestions) ---")
    for r in report.agent_results:
        innov = r.innovation
        if not innov:
            try:
                raw = json.loads(r.raw_response) if r.raw_response else {}
                innov = raw.get("innovation", "")
            except:
                pass
        if innov and innov not in ("null", ""):
            print(f"  [{r.model}]: {innov}")

    # Save
    output_path = Path(__file__).parent / "letter_evaluation_result.json"
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
        "verdict": report.winner,
        "score": report.winner_score,
        "consensus": consensus,
        "agents": len(report.agent_results),
        "votes": {r.model: r.winner for r in report.agent_results},
        "innovations": innovations,
        "synthesis": str(report.synthesis) if report.synthesis else "",
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults saved: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
