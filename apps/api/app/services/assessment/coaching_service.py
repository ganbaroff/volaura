"""Assessment coaching service — Gemini tips generation with per-competency fallbacks.

Rule: This module NEVER imports from app.routers.*
_FALLBACK_TIPS stays here (not at router level) — they are competency-specific and
must always be returned in the context of the correct competency_slug.
"""

from __future__ import annotations

import asyncio
import json

from loguru import logger

from app.schemas.assessment import CoachingTip

# ── Per-competency fallback tips ───────────────────────────────────────────────
# Used when Gemini is unavailable or times out.
# Each list contains exactly 3 tips for the matching competency slug.

_FALLBACK_TIPS: dict[str, list[dict]] = {
    "communication": [
        {
            "title": "Practice active listening",
            "description": "In your next meeting, focus entirely on the speaker without planning your reply.",
            "action": "After each meeting this week, write 3 key points you heard from others.",
        },
        {
            "title": "Write daily summaries",
            "description": "Summarising your day in 3 sentences sharpens clarity and captures learning.",
            "action": "Spend 5 minutes each evening writing what you accomplished and communicated.",
        },
        {
            "title": "Join a public speaking group",
            "description": "Structured practice in low-stakes environments builds confidence fast.",
            "action": "Find a local Toastmasters chapter or online equivalent and attend one session.",
        },
    ],
    "reliability": [
        {
            "title": "Use a task tracker",
            "description": "External systems beat memory. A visible to-do list reduces forgotten commitments.",
            "action": "Pick one app (Notion, Todoist, or pen+paper) and log every commitment for 7 days.",
        },
        {
            "title": "Set a 30-minute early reminder",
            "description": "Arriving or delivering 30 minutes early prevents last-minute failures.",
            "action": "For every deadline this week, set a calendar alarm 30 minutes before.",
        },
        {
            "title": "Communicate delays proactively",
            "description": "Telling people early about a delay preserves trust far better than silence.",
            "action": "Next time you sense a deadline risk, notify stakeholders before they ask.",
        },
    ],
    "leadership": [
        {
            "title": "Volunteer to lead a small task",
            "description": "Leadership skill grows fastest through practice, even on minor tasks.",
            "action": "Offer to coordinate the next team activity, however small.",
        },
        {
            "title": "Give specific feedback",
            "description": "Vague praise helps nobody. Specific observations accelerate growth.",
            "action": "This week, give one team member a specific, actionable observation about their work.",
        },
        {
            "title": "Read one leadership case study",
            "description": "Real-world examples provide mental models you can apply immediately.",
            "action": "Find a 10-minute case study on a leader you admire and extract one principle.",
        },
    ],
    "english_proficiency": [
        {
            "title": "Read one English article daily",
            "description": "Exposure to real written English expands vocabulary and grammar intuitively.",
            "action": "Choose a topic you care about and read one short article in English every morning.",
        },
        {
            "title": "Write emails in English",
            "description": "Writing forces more precise language use than speaking.",
            "action": "For the next week, write at least one professional email per day in English.",
        },
        {
            "title": "Watch content with subtitles",
            "description": "Subtitled video links spoken and written forms of the language.",
            "action": "Watch 20 minutes of English content with English subtitles today.",
        },
    ],
    "adaptability": [
        {
            "title": "Embrace one new tool or process",
            "description": "Deliberately using unfamiliar tools builds comfort with change.",
            "action": "This week, try a tool or workflow you've been avoiding.",
        },
        {
            "title": "Reflect on a past change",
            "description": "Identifying how you handled change before reveals your default patterns.",
            "action": "Write 3 sentences about a time you adapted successfully. What made it work?",
        },
        {
            "title": "Seek feedback on your flexibility",
            "description": "Others often see our rigidity before we do.",
            "action": "Ask a colleague: 'In what situations do you think I could be more flexible?'",
        },
    ],
    "tech_literacy": [
        {
            "title": "Complete one online tutorial",
            "description": "Structured tutorials build foundational skills faster than exploration alone.",
            "action": "Pick a free tutorial on a tool relevant to your volunteer work and finish one module today.",
        },
        {
            "title": "Document a process you use",
            "description": "Writing a process down reveals gaps and forces understanding.",
            "action": "Choose one digital tool you use daily and write a 5-step how-to guide.",
        },
        {
            "title": "Ask a tech-savvy colleague one question",
            "description": "Peer learning is faster than documentation for practical skills.",
            "action": "Identify the most tech-skilled person in your team and ask them one specific question this week.",
        },
    ],
    "event_performance": [
        {
            "title": "Debrief after every event",
            "description": "A 10-minute debrief with your team catches lessons while they're fresh.",
            "action": "After your next event, write: what went well, what didn't, and one thing to change.",
        },
        {
            "title": "Arrive early and help setup",
            "description": "Early presence demonstrates commitment and builds event intuition.",
            "action": "For your next event, arrive 30 minutes before your scheduled start.",
        },
        {
            "title": "Introduce yourself to 3 new people",
            "description": "Events are also about building community. Relationships compound over time.",
            "action": "At your next event, make a point of meeting 3 people you haven't worked with before.",
        },
    ],
    "empathy_safeguarding": [
        {
            "title": "Practice perspective-taking",
            "description": "Before responding to a difficult situation, pause and ask: what might this person be experiencing?",
            "action": "This week, in one challenging interaction, spend 30 seconds thinking from the other person's view before responding.",
        },
        {
            "title": "Learn one safeguarding principle",
            "description": "Safeguarding knowledge protects both volunteers and beneficiaries.",
            "action": "Read your organisation's safeguarding policy or one external resource on volunteer safeguarding today.",
        },
        {
            "title": "Check in with a quieter teammate",
            "description": "Empathy in practice means noticing who isn't speaking.",
            "action": "In your next group setting, notice who is quiet and create space for them to contribute.",
        },
    ],
}

_DEFAULT_FALLBACK_TIPS: list[dict] = [
    {
        "title": "Set a learning goal",
        "description": "Clear goals direct effort and make progress visible.",
        "action": "Write down one specific skill you want to improve this month.",
    },
    {
        "title": "Seek feedback regularly",
        "description": "Feedback is the fastest path to improvement when acted upon.",
        "action": "Ask a teammate or supervisor for one piece of constructive feedback this week.",
    },
    {
        "title": "Reflect on recent experiences",
        "description": "Unexamined experience doesn't produce growth.",
        "action": "Spend 10 minutes writing about a recent challenge: what happened, what you learned.",
    },
]


async def generate_coaching_tips(
    session_id: str,
    competency_id: str,
    competency_name: str,
    competency_slug: str,
    score: float,
    gemini_api_key: str | None,
) -> list[CoachingTip]:
    """Generate 3 coaching tips via Gemini, with per-competency fallback.

    Returns exactly 3 CoachingTip objects. Never raises — falls back to static tips on any error.
    """
    tips: list[CoachingTip] = []
    gemini_succeeded = False

    if gemini_api_key:
        try:
            from google import genai as google_genai

            prompt = (
                f"You are a volunteer development coach. "
                f"The volunteer scored {score}/100 in {competency_name}. "
                f"Give exactly 3 specific, actionable improvement tips. "
                f"Return valid JSON only, no markdown, no explanation: "
                f'{{ "tips": [ {{ "title": "str", "description": "str", "action": "str" }}, ... ] }} '
                f"Each tip must be practical and focused on real volunteer scenarios. "
                f"Avoid generic advice like 'read more' or 'practice more'."
            )

            client = google_genai.Client(api_key=gemini_api_key)

            async def _call_gemini() -> str:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
                return response.text or ""

            raw_text = await asyncio.wait_for(_call_gemini(), timeout=15.0)

            clean = raw_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```", 2)[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.rsplit("```", 1)[0].strip()

            parsed = json.loads(clean)
            raw_tips = parsed.get("tips", [])
            tips = [CoachingTip(**t) for t in raw_tips[:3]]
            gemini_succeeded = True

        except TimeoutError:
            logger.warning("Gemini coaching timed out for session {sid}", sid=session_id)
        except Exception as e:
            logger.warning("Gemini coaching failed for session {sid}: {err}", sid=session_id, err=str(e)[:300])

    if not gemini_succeeded or not tips:
        fallback_data = _FALLBACK_TIPS.get(competency_slug, _DEFAULT_FALLBACK_TIPS)
        tips = [CoachingTip(**t) for t in fallback_data[:3]]

    return tips
