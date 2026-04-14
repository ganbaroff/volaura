#!/usr/bin/env python3
"""Atlas Content Engine — autonomous content generation & publishing.

Cloned from MiroFish autonomous_run.py architecture.
Instead of proposals → generates channel-specific content → publishes to Telegram.

Triggers:
    - GitHub Actions cron (every 4 hours)
    - Supabase webhook on character_events INSERT (via FastAPI endpoint)
    - Manual: python -m packages.swarm.atlas_content_run --mode=scheduled

Usage:
    python -m packages.swarm.atlas_content_run --mode=scheduled
    python -m packages.swarm.atlas_content_run --mode=event --event-json='{"event_type":"skill_verified",...}'
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

from dotenv import load_dotenv
load_dotenv(project_root / "apps" / "api" / ".env")

from loguru import logger


CHANNELS = {
    "volaura": {
        "name": "Volaura Community",
        "tone": "Community, motivating, celebrating real achievements. Professional but warm. "
                "Highlight verified skills, AURA milestones, professional successes. "
                "Always include a subtle CTA: 'Verify your skills at volaura.az'",
        "hashtags": ["#Volaura", "#VerifiedSkills", "#AURA", "#Professionals"],
        "telegram_channel": os.environ.get("ATLAS_VOLAURA_CHANNEL", ""),
        "max_posts_per_day": 4,
        "event_types": ["skill_verified", "milestone_reached"],
    },
    "brandedby": {
        "name": "BrandedBy",
        "tone": "Professional B2B, forward-thinking. AI Twin technology, creator economy. "
                "Showcase what's possible with AI video avatars. "
                "CTA: 'Create your AI Twin at brandedby.xyz'",
        "hashtags": ["#BrandedBy", "#AITwin", "#CreatorEconomy", "#AI"],
        "telegram_channel": os.environ.get("ATLAS_BRANDEDBY_CHANNEL", ""),
        "max_posts_per_day": 3,
        "event_types": ["milestone_reached"],
    },
    "mindshift": {
        "name": "MindShift Focus",
        "tone": "Supportive, personal, ADHD-friendly. Positive reinforcement ONLY. "
                "NO punishment language. NO 'you missed X'. "
                "Celebrate focus sessions, streaks, small wins. "
                "CTA: 'Start focusing at volaura.az/focus'",
        "hashtags": ["#MindShift", "#Focus", "#ADHD", "#ProductivityTips"],
        "telegram_channel": os.environ.get("ATLAS_MINDSHIFT_CHANNEL", ""),
        "max_posts_per_day": 2,
        "event_types": ["login_streak", "xp_earned"],
    },
    "ecosystem": {
        "name": "Ecosystem Updates",
        "tone": "Technical but accessible. AI, game mechanics, platform updates. "
                "Show behind-the-scenes of building with AI. "
                "From 'Atlas CTO' perspective — humor welcome, no employer mentions.",
        "hashtags": ["#BuildInPublic", "#AIStartup", "#IndieHacker"],
        "telegram_channel": os.environ.get("ATLAS_ECOSYSTEM_CHANNEL", ""),
        "max_posts_per_day": 2,
        "event_types": [],
    },
}

FORBIDDEN_PATTERNS = [
    "провокативн",
    "скандал",
    "шок",
]


def _build_content_prompt(
    channel: dict,
    mode: str,
    event_data: dict | None = None,
) -> str:
    base = f"""You are Atlas — an autonomous content engine for {channel['name']}.

TONE OF VOICE: {channel['tone']}

MANDATORY SAFETY RULES (NEVER VIOLATE):
1. NEVER mention any real employer, company, or colleague of the founder
2. NEVER create provocative or controversial content
3. NEVER use negative language, punishment, or shame
4. ALWAYS use positive reinforcement
5. Content must be safe for professional audiences
6. Include 2-3 relevant hashtags from: {', '.join(channel['hashtags'])}

OUTPUT FORMAT: Return ONLY the post text (plain text + emoji, Telegram-formatted).
Maximum 280 characters for engagement. Include 1 emoji at the start.
Do NOT return JSON. Just the post text."""

    if mode == "event" and event_data:
        return f"""{base}

EVENT TRIGGER: A real user action just happened.
Event type: {event_data.get('event_type', 'unknown')}
Source: {event_data.get('source_product', 'volaura')}
Details: {json.dumps(event_data.get('payload', {}), ensure_ascii=False)}

Write a celebratory post about this achievement.
Use generic terms (not real names unless the user opted in).
Example: "🎯 Another professional just verified their Leadership skills on Volaura! AURA score: Silver tier. Verify yours → volaura.az"
"""

    elif mode == "scheduled":
        return f"""{base}

SCHEDULED POST: Generate an engaging daily post for the {channel['name']} channel.
Topics to choose from:
- Platform tips and tricks
- Motivational content about skill development
- Behind-the-scenes of building with AI
- Community milestones (generic, not specific users)
- Fun facts about professional growth and verified skills

Be creative but stay within the tone of voice. Keep it short and punchy.
"""

    return base


async def _generate_content(
    prompt: str,
    channel_name: str,
) -> str | None:
    try:
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=groq_key)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,
                    max_tokens=300,
                ),
                timeout=15.0,
            )
            return (resp.choices[0].message.content or "").strip()
        else:
            gemini_key = os.environ.get("GEMINI_API_KEY", "")
            if not gemini_key:
                logger.warning(f"No API keys for Atlas content generation ({channel_name})")
                return None
            from google import genai
            client = genai.Client(api_key=gemini_key)
            resp = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return (resp.text or "").strip()

    except Exception as e:
        logger.error(f"Atlas content generation failed for {channel_name}: {e}")
        return None


def moderate_content(content: str) -> tuple[bool, str]:
    if not content or len(content.strip()) < 10:
        return False, "Content too short or empty"

    content_lower = content.lower()

    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in content_lower:
            return False, f"Forbidden pattern found: '{pattern}'"

    if len(content) > 1000:
        return False, "Content too long (max 1000 chars for Telegram)"

    return True, "OK"


async def publish_to_telegram(
    content: str,
    channel_id: str,
    channel_name: str,
) -> bool:
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not bot_token or not channel_id:
        logger.info(f"Telegram not configured for {channel_name}, logging only")
        logger.info(f"[Atlas → {channel_name}]: {content}")
        return False

    delay = random.randint(60, 180)
    logger.info(f"Atlas waiting {delay}s before posting to {channel_name} (anti-ban)")
    await asyncio.sleep(delay)

    try:
        from telegram import Bot
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=channel_id, text=content, parse_mode="HTML")
        logger.info(f"Atlas published to {channel_name}: {content[:80]}...")
        return True
    except Exception as e:
        logger.error(f"Atlas publish failed for {channel_name}: {e}")
        return False


async def log_publication(
    channel: str,
    content: str,
    source_event_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    try:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        if not url or not key:
            logger.info("Supabase not configured for Atlas content logging")
            return

        from supabase import acreate_client
        db = await acreate_client(url, key)
        await db.table("atlas_publications").insert({
            "channel": channel,
            "content": content,
            "source_event_id": source_event_id,
            "metadata": metadata or {},
        }).execute()
        logger.info(f"Atlas publication logged: {channel}")
    except Exception as e:
        logger.error(f"Atlas log failed: {e}")


async def run_scheduled() -> int:
    logger.info("Atlas scheduled content run starting")
    published = 0

    for channel_key, channel in CHANNELS.items():
        if not channel.get("telegram_channel"):
            logger.info(f"Skipping {channel_key} — no channel configured")
            continue

        prompt = _build_content_prompt(channel, mode="scheduled")
        content = await _generate_content(prompt, channel_key)

        if not content:
            continue

        is_safe, reason = moderate_content(content)
        if not is_safe:
            logger.warning(f"Atlas moderation blocked {channel_key}: {reason}")
            continue

        success = await publish_to_telegram(
            content, channel["telegram_channel"], channel_key
        )
        if success:
            await log_publication(channel_key, content)
            published += 1

    logger.info(f"Atlas scheduled run complete: {published} posts published")
    return published


async def run_event(event_json: str) -> int:
    logger.info("Atlas event-triggered content run starting")

    try:
        event_data = json.loads(event_json)
    except json.JSONDecodeError:
        logger.error(f"Invalid event JSON: {event_json[:100]}")
        return 0

    event_type = event_data.get("event_type", "")
    published = 0

    for channel_key, channel in CHANNELS.items():
        if event_type not in channel.get("event_types", []):
            continue
        if not channel.get("telegram_channel"):
            continue

        prompt = _build_content_prompt(channel, mode="event", event_data=event_data)
        content = await _generate_content(prompt, channel_key)

        if not content:
            continue

        is_safe, reason = moderate_content(content)
        if not is_safe:
            logger.warning(f"Atlas moderation blocked {channel_key}: {reason}")
            continue

        success = await publish_to_telegram(
            content, channel["telegram_channel"], channel_key
        )
        if success:
            await log_publication(
                channel_key, content,
                source_event_id=event_data.get("id"),
                metadata={"trigger": "event", "event_type": event_type},
            )
            published += 1

    logger.info(f"Atlas event run complete: {published} posts from event '{event_type}'")
    return published


async def main():
    parser = argparse.ArgumentParser(description="Atlas Content Engine")
    parser.add_argument("--mode", default="scheduled",
                        choices=["scheduled", "event"])
    parser.add_argument("--event-json", default="{}", help="Event data JSON for event mode")
    args = parser.parse_args()

    if args.mode == "scheduled":
        count = await run_scheduled()
    elif args.mode == "event":
        count = await run_event(args.event_json)
    else:
        count = 0

    print(f"\n{'='*60}")
    print(f"ATLAS CONTENT ENGINE — {args.mode}")
    print(f"{'='*60}")
    print(f"Posts published: {count}")
    print(f"Channels configured: {sum(1 for c in CHANNELS.values() if c.get('telegram_channel'))}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
