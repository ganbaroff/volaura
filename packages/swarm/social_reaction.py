"""
Reusable LinkedIn social media reaction simulator.
MiroFish primary use case: simulate how audience segments react BEFORE publishing.

Usage:
    from packages.swarm.social_reaction import simulate_reactions
    report = await simulate_reactions(post_text, translation, context_extra)
"""
import asyncio
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

from packages.swarm import SwarmEngine, SwarmConfig, StakesLevel
from packages.swarm.types import DomainTag, PathDefinition

AUDIENCE_SEGMENTS = """
AUDIENCE SEGMENTS TO SIMULATE (evaluate the post from each perspective):

SEGMENT 1 — Management / Sector Insiders
People who ALSO worked at WUF13, COP29, CIS Games — former managers and colleagues.
They recognize themselves in the 'connections not professionalism' critique.
Key question: Will they feel personally accused, or will they recognize a systemic critique?
What do they actually do with this post?

SEGMENT 2 — HR Managers on LinkedIn
Professional HR people who see AURA score as potentially competing with their judgment.
They have personal investment in defending current hiring practices.
But they also know the nepotism problem is real. Will they validate or defend?

SEGMENT 3 — Startup Founders / Investors
Looking at Yusif as a potential founder to back. Is the problem real and large?
Is the AI CTO disclosure a strength (honest) or a weakness (he needs AI to build)?
Would they DM him, share to their network, or scroll past?

SEGMENT 4 — Volunteers and Event Professionals
People who have lived this frustration directly — worked under a coordinator selected
by connections. High emotional resonance. High share probability.
What comment do they leave? What do they feel?

SEGMENT 5 — Former Colleagues / Personal Network
Yusif's direct LinkedIn network: people who know him personally from past work.
The post changes their perception of him in some direction.
Will they be proud, concerned, surprised, or confused?

For EACH segment, provide:
1. emotional_reaction: offended | validates | curious | neutral | surprised
2. likely_action: like | share | comment | ignore | DM | unfollow | share_privately
3. verbatim_comment: exactly what they would write in comments (in their natural voice and language)
4. professional_risk_to_yusif: LOW | MEDIUM | HIGH | CRITICAL
5. key_reason: one sentence explaining the core of their reaction
"""


async def simulate_reactions(
    post_text: str,
    translation: str,
    author_context: str = "",
    timeout_seconds: float = 90.0,
):
    """
    Simulate LinkedIn audience reactions to a post before publishing.

    Args:
        post_text: The actual post (any language)
        translation: English summary for non-native-language models
        author_context: Extra context about the author's situation
        timeout_seconds: Max wait time for agents

    Returns:
        SwarmReport with publish recommendation as winner
    """
    engine = SwarmEngine()

    full_context = f"""Author: Yusif Ganbarov, founder of Volaura (volunteer competency platform, Baku, Azerbaijan).
Post is published on LinkedIn. His management team from WUF13, COP29, CIS Games 2025 can see this post.
Goal: employer visibility + Volaura launch awareness.
Budget: 0 AZN for promotion.
{author_context}"""

    config = SwarmConfig(
        question=f"""You are a LinkedIn audience reaction simulator. Your job is to predict REAL human reactions — not ideal reactions, not polite reactions. What would people ACTUALLY feel and do?

POST TEXT (original language):
{post_text}

ENGLISH TRANSLATION / SUMMARY:
{translation}

{AUDIENCE_SEGMENTS}

After simulating all 5 segments, give an OVERALL PUBLISH RECOMMENDATION considering all risks and opportunities.
Be specific. Be honest. If the post risks real relationships, say so clearly.
""",
        paths={
            "publish_now": PathDefinition(
                name="Publish as-is — post is ready",
                description="Sector insiders recognize systemic critique, not personal accusation. Volunteers and network will amplify. Professional risk is acceptable.",
                best_case="Volunteers share widely. Founders and investors engage. Opens B2B conversations with HR teams.",
                worst_case="1-2 former colleagues feel indirectly accused. Private messages, not public confrontation.",
                effort="0 — post immediately",
            ),
            "revise_tone": PathDefinition(
                name="Revise first — soften sector language",
                description="Keep the message but reduce specific event name prominence. Slightly less direct on coordinator selection critique.",
                best_case="Same reach, meaningfully lower risk to professional relationships.",
                worst_case="Loses sharpness. Post becomes generic LinkedIn content that nobody shares.",
                effort="1-2 hours revision + re-simulation",
            ),
            "publish_with_disclaimer": PathDefinition(
                name="Add systemic framing sentence",
                description="Open with: 'Mən heç bir şəxsi ittiham etmirəm — sistem haqqında danışıram.' (I accuse no one personally — I am talking about the system.) This pre-empts the most likely negative interpretation.",
                best_case="Reduces insider offense. Keeps directness. One sentence does the defensive work.",
                worst_case="Reads as defensive. Weakens the post. Sophisticated readers see it as a tell.",
                effort="15 minutes",
            ),
            "delay_and_add_english": PathDefinition(
                name="Post AZ + EN version same day",
                description="Publish Azerbaijani version for local audience + English version same day for international event management professionals who validate the systemic problem at scale.",
                best_case="International validation reduces perception of 'this is a local complaint about specific people'.",
                worst_case="Two posts on same day dilutes attention. EN version feels like a translation, loses authenticity.",
                effort="2-3 hours for EN draft + scheduling",
            ),
        },
        stakes=StakesLevel.HIGH,
        domain=DomainTag.BUSINESS,
        context=full_context,
        timeout_seconds=timeout_seconds,
    )

    report = await engine.decide(config)
    return report
