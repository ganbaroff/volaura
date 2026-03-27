#!/usr/bin/env python3
"""ZEUS Video Skill — AI Twin video generation via fal.ai MuseTalk.

DSP winner (Session 48, 40/50): ZEUS orchestrates fal.ai MuseTalk.
Architecture:
    script → fal.ai TTS → audio_url
    photo_url + audio_url → fal.ai MuseTalk → video_url

Pipeline is fully async (asyncio.to_thread wraps blocking fal_client calls).
Integrates with brandedby.generations queue via status updates to Supabase.

Usage:
    from packages.swarm.zeus_video_skill import ZeusVideoSkill
    skill = ZeusVideoSkill(fal_api_key="...", supabase_url="...", supabase_key="...")
    video_url = await skill.generate(photo_url, script, generation_id)
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from loguru import logger

# Ensure packages/ is importable when run directly
project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

# fal.ai SDK
try:
    import fal_client  # type: ignore[import]
    FAL_AVAILABLE = True
except ImportError:
    FAL_AVAILABLE = False
    logger.warning("fal-client not installed. Run: pip install fal-client")


# ── fal.ai model IDs ──────────────────────────────────────────
FAL_MUSETALK_MODEL = "fal-ai/musetalk"
FAL_TTS_MODEL = "fal-ai/kokoro/american-english"  # PlayAI deprecated; Kokoro $0.02/1k chars

# ── Quality / cost settings ───────────────────────────────────
MUSETALK_CONFIG = {
    "face_resize_factor": 1.0,       # 1.0 = natural size
    "fps": 25,                        # standard lip-sync fps
    "audio_padding": 0.3,             # seconds of silence padding
}

TTS_CONFIG = {
    "voice": "am_adam",  # Kokoro male voice (am_adam = natural English male)
    "speed": 1.0,        # normal pace
}


class ZeusVideoSkill:
    """ZEUS skill: text + photo → AI Twin talking-head video via fal.ai.

    Designed to plug into the BrandedBy generation queue:
    - Called by the FastAPI video generation worker
    - Updates brandedby.generations status in Supabase
    - Returns video_url on success, raises on failure
    """

    def __init__(self, fal_api_key: str) -> None:
        if not FAL_AVAILABLE:
            msg = "fal-client not installed. Run: pip install fal-client"
            raise RuntimeError(msg)
        os.environ["FAL_KEY"] = fal_api_key
        self._key = fal_api_key

    async def generate(
        self,
        photo_url: str,
        script: str,
        *,
        generation_id: str | None = None,
        voice: str | None = None,
    ) -> str:
        """Generate a talking-head video from a portrait photo and script.

        Args:
            photo_url: Public URL of the portrait photo (JPG/PNG, front-facing).
            script: Text the AI Twin will speak (max 500 words).
            generation_id: Optional brandedby.generations.id for logging.
            voice: fal.ai TTS voice ID (defaults to TTS_CONFIG["voice"]).

        Returns:
            Public URL of the generated MP4 video (hosted on fal.ai CDN).

        Raises:
            RuntimeError: If either TTS or video generation fails.
        """
        gen_label = generation_id or "no-id"
        logger.info(
            "ZeusVideoSkill.generate started",
            generation_id=gen_label,
            photo_url=photo_url[:60],
            script_length=len(script),
        )

        # Step 1: Script → audio via fal.ai TTS
        audio_url = await self._generate_audio(script, voice=voice)
        logger.info("TTS complete", generation_id=gen_label, audio_url=audio_url[:60])

        # Step 2: Photo + audio → video via fal.ai MuseTalk
        video_url = await self._generate_video(photo_url, audio_url)
        logger.info("Video complete", generation_id=gen_label, video_url=video_url[:60])

        return video_url

    async def _generate_audio(self, script: str, *, voice: str | None = None) -> str:
        """Convert script to audio via fal.ai PlayAI TTS.

        Returns a public audio URL hosted on fal.ai CDN.
        """
        tts_input = {
            "prompt": script,                      # Kokoro field name
            "voice": voice or TTS_CONFIG["voice"],
            "speed": TTS_CONFIG["speed"],
        }

        try:
            result = await asyncio.to_thread(
                fal_client.run,
                FAL_TTS_MODEL,
                arguments=tts_input,
            )
        except Exception as e:
            logger.error("fal.ai TTS failed", error=str(e))
            raise RuntimeError(f"TTS generation failed: {e}") from e

        # Extract audio URL from result
        audio_url = (
            result.get("audio", {}).get("url")
            or result.get("audio_url")
            or result.get("url")
        )
        if not audio_url:
            logger.error("TTS result missing audio URL", result=result)
            raise RuntimeError(f"TTS returned no audio URL. Result: {result}")

        return str(audio_url)

    async def _generate_video(self, photo_url: str, audio_url: str) -> str:
        """Run fal.ai MuseTalk: photo + audio → talking-head video.

        Returns a public video URL hosted on fal.ai CDN.
        """
        musetalk_input = {
            "video_url": photo_url,    # MuseTalk accepts single image URL
            "audio_url": audio_url,
            **MUSETALK_CONFIG,
        }

        try:
            # Use submit + result for async (avoids blocking Railway thread pool)
            handler = await asyncio.to_thread(
                fal_client.submit,
                FAL_MUSETALK_MODEL,
                arguments=musetalk_input,
            )
            result = await asyncio.to_thread(handler.get)
        except Exception as e:
            logger.error("fal.ai MuseTalk failed", error=str(e))
            raise RuntimeError(f"Video generation failed: {e}") from e

        # Extract video URL from result
        video_url = (
            result.get("video", {}).get("url")
            or result.get("video_url")
            or result.get("url")
        )
        if not video_url:
            logger.error("MuseTalk result missing video URL", result=result)
            raise RuntimeError(f"MuseTalk returned no video URL. Result: {result}")

        return str(video_url)


# ── CLI test harness ──────────────────────────────────────────

async def _cli_test(photo_url: str, script: str) -> None:
    """Quick test: python -m packages.swarm.zeus_video_skill <photo_url> '<script>'"""
    from dotenv import load_dotenv
    load_dotenv(project_root / "apps" / "api" / ".env")

    fal_key = os.environ.get("FAL_API_KEY", "")
    if not fal_key:
        print("ERROR: FAL_API_KEY not set in apps/api/.env")
        return

    skill = ZeusVideoSkill(fal_api_key=fal_key)
    print(f"Generating video for: {photo_url[:60]}...")
    print(f"Script: {script[:100]}...")

    try:
        video_url = await skill.generate(photo_url, script)
        print(f"\n✅ Video URL: {video_url}")
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python zeus_video_skill.py <photo_url> '<script>'")
        sys.exit(1)
    asyncio.run(_cli_test(sys.argv[1], sys.argv[2]))
