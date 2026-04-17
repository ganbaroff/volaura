---
name: BrandedBy Video Generation Research
description: AI video provider comparison — D-ID wins Phase 1, LivePortrait non-commercial, Kling LipSync Phase 2
type: project
---

## Video Generation Provider Decision (2026-03-27, Session 47)

**Phase 1 Winner: D-ID Lite ($5.90/mo)**
- 10 min video included, 1 API call (photo + text → video)
- Simplest integration, 4x faster than realtime, 119 languages
- Watermark on Lite (upgrade to Pro $29/mo removes it)

**Phase 2: Kling LipSync on fal.ai ($0.42/30s video)**
- Best quality motion (head nods, body language)
- Requires TTS pipeline (Gemini TTS or Kokoro)
- 100 videos/month = ~$42

**AVOID:**
- LivePortrait — InsightFace models = non-commercial license
- OmniHuman — $4+/video, too expensive for startup
- ElevenLabs — 7 responses/day on $22/mo = 70x worse

**Why:** Research validated by web search of Replicate, fal.ai, D-ID, HeyGen pricing pages.

**How to apply:** D-ID API key goes in `apps/api/.env` as `DID_API_KEY`. Config already added to `config.py`.
