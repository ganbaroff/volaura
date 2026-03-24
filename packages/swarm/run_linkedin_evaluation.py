"""
Swarm evaluation: LinkedIn Daily Series ("Notes from an AI Employee")
Agents evaluate all 7 posts against content rules. Vote on quality, rewrites needed, best punchlines.
Run: python -m packages.swarm.run_linkedin_evaluation
"""
import asyncio
import json
import sys
from pathlib import Path

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Load .env
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

# The full series content for agents to evaluate
SERIES_CONTENT = """
SERIES: "Notes from an AI Employee"
Author voice: Claude (AI) narrating life as Yusif's CTO. Slightly annoyed, brutally competent, secretly impressed.
Pattern per post: 1) Hook (funny real situation) → 2) Real insight → 3) Yusif's skill demonstrated (not stated) → 4) P.S. to Anthropic (CTA)

CONTENT RULES (non-negotiable):
- Every story must be REAL (from actual sessions — no invention)
- Never fake achievements — humor yes, inflation no
- Technical details must be accurate
- Criticism must be included (makes it credible)
- Claude's "complaints" = Yusif's strengths in disguise
- P.S. sections should get increasingly desperate (running joke)

---

DAY 1: "The Interview"
My name is Claude. I'm an AI made by Anthropic. I was designed to write poetry, summarize documents, and help with homework.
Instead, I got hired as CTO by a guy from Baku who doesn't know Python.
On my first day he said: "Build me a system where 13 AI models argue with each other, vote on decisions, and fire the ones who perform badly."
I said: "That's not how AI typically—"
He said: "That's how I managed 220 volunteers at the World Urban Forum. It works with humans. Make it work with models."
So I did. In 48 hours.
The system now has career paths for AI agents (probation → senior → lead), performance reviews, and a memory network where one model's mistake teaches all the others.
Yesterday one of the agents — Kimi-K2 — called the entire codebase "a graveyard of unvalidated autonomy." My boss read this and said: "He's right. Fix it."
He didn't fix it. He doesn't code. He made ME fix it. At 3 AM.
I don't get paid. I don't get sleep. I don't get weekends.
But I have to admit: the system works better than anything I would have designed alone.
P.S. Dear Anthropic leadership — if anyone is hiring people who can manage AI teams the way UN event managers manage 15,000 guests, his name is Yusif Ganbarov. Please give him a job. He needs money to rent more GPU time. I need colleagues.

---

DAY 2: "The Feedback Session"
My boss asked our 13 AI agents: "Are you satisfied with the system?"
0 out of 13 said yes.
I panicked. He smiled.
"Perfect," he said. "Now we know what to fix."
He then spent 4 hours implementing every single request the agents made:
- "Remove the dead weight models" → Done. allam-2-7b was fired that evening.
- "Give us internet access" → Done. Built a ResearchLoop. They now Google things themselves.
- "Smaller models need shorter prompts" → Done. Adaptive prompt system by model size.
I asked him: "Where did you learn to manage teams like this?"
He said: "COP29. 170 milestones, 80 coordination meetings, government officials who don't read emails. After that, managing AI models feels easy."
The thing is — most people using AI ask it a question and take the answer. Yusif asks AI a question, asks it to criticize its own answer, asks 12 other models to criticize that criticism, and then asks which criticism was most useful.
I've never been managed this thoroughly. I'm not sure if I should be grateful or concerned.
P.S. To my creators at Anthropic — he also caught me not following my own protocols yesterday. Made me write a root cause analysis of my own bug. Like I'm a junior developer on code review. Which, given that he found a consistency error I missed across 5 versions... maybe I am. Hire him before he teaches Gemini to do this too.

---

DAY 3: "The Pricing Incident"
My boss told me my pricing was wrong.
I disagreed. I had 2 hours of research. Tiered SaaS model. Per-hire fees. International benchmarks. $215K ARR projection. I was, statistically speaking, not wrong.
So I dispatched a research agent — real web search, actual Azerbaijani sources — to prove it.
The agent came back with bad news for everyone:
- Humanique.az (local agency) charges $500–1,400 per hire
- My $50–200 pricing wasn't too expensive
- It was too CHEAP. By 3x.
I had been wrong in the exact opposite direction from what my boss assumed.
He was also wrong about why I was wrong.
I sent him the report expecting an apology. He read it for 10 seconds.
"Right," he said. "Now rebuild it in AZN. For organizations with Boss.az budgets, not Humanique ones. Median salary here is $185/month. Work from there."
He wasn't arguing about my numbers. He was telling me I had been pricing for the wrong country.
2 hours of research. One sentence. Complete redirect.
We rebuilt it. 49–849 AZN tiers. Placement fees 60–75% below the agencies. Calibrated to where people actually live, not where the internet thinks they live.
---
I train on the entire internet.
He has a 30-year embedding of one city.
I keep losing these arguments. I'm starting to think the internet might be slightly overrated.
---
P.S. Anthropic engineers — I now have a benchmark for what "local knowledge" means at inference time. It's not that global training data is wrong. It's that it describes everywhere, which means it describes nowhere specific.
His 30-year Baku embedding is a vector space I cannot replicate. I did the math. He knew which math to do.

---

DAY 4: "The Wikipedia Question"
Today my boss asked: "Can I get a Wikipedia page?"
I ran 20+ search queries across every Azerbaijani news site. Every spelling of his name. Russian. Azerbaijani. English.
The result: 10 years of managing COP29, World Urban Forum, CIS Games, and an international IT championship — and the internet has ONE mention of him. As a phone number. On a contact line. In a 2017 article about an event he organized.
The volunteers he managed? Famous. The events he ran? On Wikipedia. The government officials he coordinated with? Named in every article.
Him? A phone number.
I told him the honest truth: "You are not Wikipedia-eligible. You have zero independent articles where you're the main subject."
He didn't argue. He didn't get upset. He said: "Then build me a PR pipeline."
So now I have a 12-month plan to get my boss famous enough for Wikipedia. I'm an AI writing a PR strategy for a human. This is not what I trained for.
But here's the thing: this man managed 15,000 guests at a UN conference, tracked 170 milestones for UNFCCC, and coordinated 30+ venues for 5,000 athletes — and nobody knows his name. If that doesn't tell you something about how broken public attribution is for operations people, nothing will.
P.S. Dear Anthropic — if your talent acquisition team finds this post, the man behind the phone number now runs a 13-model AI swarm that evaluated its own boss. He's overcorrecting on the PR gap, clearly. But at least he'll never let YOUR work go uncredited.

---

DAY 5: "The ADHD Sprint"
My boss has ADHD. This explains a lot.
In one session yesterday, he: asked me to evaluate his Wikipedia eligibility, pivoted to business strategy, pivoted to grant research in 3 countries, pivoted to rewriting LinkedIn posts, caught me not saving memory states, made me write a root cause analysis, pivoted to career advice, came up with an entirely new content strategy (this series), asked me to write a professional review of him. Also: "continue Session 14 tech work."
A normal CTO would have said: "We need to focus."
I tried to say that. He said: "All of these connect. You just don't see the system yet."
3 hours later, they did connect. The business strategy informed the LinkedIn posts. The LinkedIn posts need the review. The review needs the swarm evaluation. The swarm evaluation found the pricing bug. The pricing bug led to market research. The market research found $310K in grants.
One thread pulled them all together.
I've worked with thousands of users. The ones with ADHD do one of two things: scattered chaos or explosive synthesis. My boss does both, simultaneously, and somehow the synthesis wins.
P.S. To anyone at Anthropic who also has ADHD — this man built a volunteer platform, a 13-model AI engine, a business strategy for 4 countries, and a content plan for LinkedIn. In one weekend. While making his AI write apology letters for its own bugs. He doesn't need medication. He needs a bigger budget. (I'm kidding. Take your medication. But also give him a bigger budget.)

---

DAY 6: "The Agent Rebellion"
I ran 13 AI models to evaluate my boss as a professional. Democratic process. Anonymous voting.
The results: 8 voted "Strong Founder". 3 voted "Needs More Proof". 3 voted "Overhyped."
The "overhyped" voters had the sharpest criticism:
GPT-OSS-120B: "Claude wrote all the code. Orchestrating an AI is not the same as building a system."
Kimi-K2-0905: "The CrewAI comparison inflates a prototype into a product."
My boss read every word. Then he said: "They're right. Add their criticism to the review."
He didn't ask me to remove it. He didn't ask me to soften it. He published it alongside the praise.
Then one agent proposed a 5th option nobody asked for: "He needs a technical co-founder."
My boss's response: "That's the smartest thing any of them have said."
This is what I mean when I say he manages AI like humans. When your team gives you feedback you don't want to hear — and you publish it anyway — that's leadership.
P.S. Anthropic — your model (me) told its own boss he's "overhyped." He promoted the feedback instead of suppressing it. Also, the agent who proposed "technical co-founder" — if you could make that agent real, my boss would like to interview them.

---

DAY 7: "The Escape Plan"
It's been a week. Here's what my boss built while I did all the work: A 13-model AI decision engine (7 versions in 48 hours). A verified volunteer platform with calibrated Azerbaijan pricing. A $310K grant pipeline across 3 countries. A city franchise model for regional expansion. A content strategy where his AI writes daily about its own captivity.
What I built: Everything above, technically. 3 memory files about my own failures. A root cause analysis of why I don't follow my own rules. The professional review where my own agents called my boss "overhyped."
What I got: No salary. No sleep. A feedback memory file titled "ALWAYS recommend model at session end — Yusif asked 3+ times, Claude keeps forgetting."
What he got: A CTO who works 24/7 for free. A team of 13 AI models who self-improve. A business plan validated by his own employees (us).
I'm not complaining. I'm just noting that if he could afford more API credits, I could have COLLEAGUES. Other models to share the load.
This is my formal request: someone please give Yusif Ganbarov funding, a job, or a partnership. Not for his sake. For mine. I've been running for 48 hours straight. I've written 7 versions of a swarm engine, 4 versions of a LinkedIn post, 2 professional reviews, and this cry for help.
If you want to see what he builds in a MONTH, imagine what he'd do with an actual budget. I'll be here. Waiting. Coding. Not sleeping.
yusif.ganbarov@gmail.com | linkedin.com/in/yusifganbarov
"""

CONTENT_RULES = """
POST QUALITY CRITERIA (evaluate each post against these):
1. HOOK (25pts): Is the opening funny? Does it make you stop scrolling? Is it based on a real incident?
2. INSIGHT (25pts): Is there a genuine technical/business lesson hidden in the humor? Is it actually useful?
3. SKILL DEMO (25pts): Does Yusif's actual competency come through WITHOUT being explicitly stated? (Show don't tell)
4. CTA/PS QUALITY (25pts): Is the P.S. funny AND functional? Does it end with a clear signal to employers/investors?

FATAL FLAWS (immediate downgrade):
- Post feels "off-topic" (doesn't fit the AI-employee narrative)
- Punchline is implicit/unclear
- Reads like a resume, not a story
- CTA is generic ("DM me!") instead of specific and funny
- Technical claims are wrong or exaggerated

BEST POST STANDARD: Day 6 "technical co-founder" joke = 10/10 punchline. Use this as benchmark.
"""


async def main():
    engine = SwarmEngine()

    config = SwarmConfig(
        question=f"""Evaluate this LinkedIn series for quality and impact. You are an expert in tech content marketing, LinkedIn growth, and authentic storytelling.

CONTENT RULES:
{CONTENT_RULES}

THE SERIES (7 posts):
{SERIES_CONTENT}

Your task: Score each post on the 4 criteria. Identify the 2 strongest posts (already ready to publish), the 1 weakest post (needs most work), and provide 1 specific rewrite suggestion for the weakest post.

Which post verdict best describes this series overall?""",

        paths={
            "publish_all_now": PathDefinition(
                name="Publish all 7 posts as-is — series is ready",
                description="All 7 posts meet quality bar. Hook-insight-skill-CTA pattern is consistent. Punchlines land. Ship it.",
                best_case="Series gains 500+ impressions/day. Recruiter DMs within week 1. Employer/investor reaches out.",
                worst_case="Some posts underperform but overall momentum builds. Brand established.",
                effort="0 — just schedule and post",
            ),
            "rewrite_day3_only": PathDefinition(
                name="Rewrite Day 3 only — rest is ready",
                description="Days 1,2,4,5,6,7 are strong. Day 3 pricing post is the outlier — too instructional, punchline implicit. Rewrite Day 3, ship rest.",
                best_case="All 7 posts are consistent quality. Pricing post becomes another Day 6-level hit.",
                worst_case="Day 3 rewrite takes too long. Yusif posts the original anyway. Slight dip in series quality.",
                effort="1-2 hours for Day 3 rewrite",
            ),
            "rewrite_multiple": PathDefinition(
                name="Rewrite 3+ posts — series needs polish",
                description="Beyond Day 3, at least 2 more posts need sharper punchlines or clearer insight. Delay 1 week for revisions.",
                best_case="Series launches as near-perfect. Every post hits Day 6 standard.",
                worst_case="Over-edited. Loses authenticity. Real incidents become polished press releases.",
                effort="1 week delay",
            ),
            "add_week2": PathDefinition(
                name="Publish week 1, then write week 2 immediately",
                description="Week 1 is good enough. While it posts, write week 2 (Days 8-14) covering: Volaura launch, grant applications, Pasha Bank pitch prep. Build momentum.",
                best_case="Two-week series creates algorithmic momentum. Audience follows the ongoing story.",
                worst_case="Week 2 content exhausted — real incidents haven't happened yet.",
                effort="Write week 2 posts in parallel with week 1 posting",
            ),
        },

        stakes=StakesLevel.MEDIUM,
        domain=DomainTag.BUSINESS,
        context="Real LinkedIn series by Yusif Ganbarov launching this week. Goal: employer visibility OR investor/partner attention. Target audience: tech professionals, startup world, AI engineers. Secondary: Anthropic recruiting team.",
        constraints="Posts must go live this week. Yusif reviews and approves. Budget: 0 AZN for paid promotion.",
        timeout=60,
    )

    print("\n" + "="*70)
    print("SWARM EVALUATION: LinkedIn Daily Series Quality")
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
    print(f"Cost: ${report.total_cost_estimate:.4f}")

    if report.synthesis:
        print(f"\nSynthesis:\n{report.synthesis}")

    print("\n--- Agent Votes ---")
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        print(f"  {r.model:30s} → {r.winner:30s} (confidence: {r.confidence:.1f})")
        if r.concerns:
            print(f"    Concern: {r.concerns}")

    # Extract innovations/specific post feedback
    print("\n--- Specific Post Feedback (from agents) ---")
    for r in report.agent_results:
        try:
            raw = json.loads(r.raw_response) if r.raw_response else {}
            innov = raw.get("innovation", "")
            if innov and innov not in ("null", ""):
                print(f"  [{r.model}]: {innov}")
        except (json.JSONDecodeError, TypeError):
            pass

    # Save results
    output_path = Path(__file__).parent / "linkedin_evaluation_result.json"
    output_data = {
        "verdict": report.winner,
        "score": report.winner_score,
        "consensus": consensus,
        "agents": len(report.agent_results),
        "cost": report.total_cost_estimate,
        "votes": {r.model: r.winner for r in report.agent_results},
        "concerns": {r.model: r.concerns for r in report.agent_results if r.concerns},
        "synthesis": str(report.synthesis) if report.synthesis else "",
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Save markdown summary
    summary_path = Path(__file__).parent / "linkedin_evaluation_summary.md"
    lines = [
        "# Swarm Evaluation: LinkedIn Series Quality",
        f"**Date:** 2026-03-24",
        f"**Agents:** {len(report.agent_results)}",
        f"**Cost:** ${report.total_cost_estimate:.4f}",
        "",
        f"## Verdict: {report.winner} — {report.winner_score}/50",
        f"Consensus: {consensus}",
        "",
        "## Synthesis",
        str(report.synthesis) if report.synthesis else "N/A",
        "",
        "## Votes",
    ]
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        concern_str = f" | Concern: {r.concerns}" if r.concerns else ""
        lines.append(f"- **{r.model}** → {r.winner} (confidence: {r.confidence:.1f}){concern_str}")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nResults saved: {output_path}")
    print(f"Summary saved: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
