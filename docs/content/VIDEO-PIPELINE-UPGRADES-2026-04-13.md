# Video / Content Pipeline — What Could Be Better

**Date:** 2026-04-13
**Author:** Cowork (research synthesis)
**For:** CEO Yusif + Atlas (CTO)
**Direction in scope:** Programmatic content rendering (`packages/remotion/` + `packages/swarm/content_pipeline.py`)
**Method:** 6 targeted web searches (April 2026), cross-checked against current state.

---

## TL;DR

Remotion is the right base. Everything below extends it without replacing it. Three upgrades pay off this week (captions, AZ TTS, Postiz). Two require a CEO brand decision (HeyGen avatar of Yusif, AI b-roll). One waits until volume justifies it (Lambda).

| # | Upgrade | Tier | Cost / mo | Effort | CEO decision needed? |
|---|---------|------|-----------|--------|----------------------|
| 1 | Whisper.cpp captions (TikTok-style word-by-word) | DO NOW | $0 | 1 day | No |
| 2 | TTS voice-over (Azure for AZ, ElevenLabs for EN/RU) | DO NOW | ~$5–10 | 1 day | No |
| 3 | Postiz for distribution (replace manual upload) | DO NOW | $0 (self-host) | 0.5 day | No |
| 4 | HeyGen Avatar IV — Yusif AI clone | THIS MONTH | $29 | 0.5 day setup | **YES — brand call** |
| 5 | Music bed (Suno v4.5 / Udio API) | THIS MONTH | ~$10 | 0.5 day | Style preference |
| 6 | AI b-roll (Veo 3.1 / Sora 2) | OPTIONAL | $20 | 0.5 day | **YES — aesthetic call** |
| 7 | Remotion Lambda (parallel render farm) | LATER | ~$0.001–0.02/video | 1 day | No (auto-trigger when batch > 5) |

**Reject:** Revideo, Motion Canvas, Buffer, Hootsuite, Synthesia (reasons in §6).

---

## 1. Captions (TikTok-style, word-by-word) — **DO NOW**

**Why this matters most.** Plain text-on-screen TikToks lose ~30–50% of viewers vs. captions that highlight the spoken word. Remotion ships an official solution.

**Stack:**
- `@remotion/install-whisper-cpp` — runs Whisper locally on Atlas's machine, no API cost
- `@remotion/captions` → `createTikTokStyleCaptions()` — word-level animation primitives
- `whisper-large-v3-turbo` model (faster, near-identical accuracy to large-v3)
- AZ is in Whisper's 99 supported languages

**Pipeline integration:**
```
TTS audio → whisper.cpp → SRT + word timestamps → @remotion/captions → composition
```

**Acceptance criteria:**
1. `pnpm --filter @volaura/remotion render -- TikTokAZ` produces an MP4 with synced word-by-word captions.
2. Captions match audio within ±100ms drift for full 45s.
3. AZ characters render correctly (ə, ç, ö, ş, ü, ı).

**Effort:** ~1 day Atlas. Reference: [Remotion TikTok template](https://github.com/remotion-dev/template-tiktok).

---

## 2. TTS Voice-Over — **DO NOW**

**Current gap.** Posts #2 (TikTok AZ) and #6 (Carousel) are silent. TikTok algorithm penalises silent videos. Voice-over also unlocks captions (#1).

**Recommendation: split provider by language.**

| Language | Provider | Voice | Why |
|----------|----------|-------|-----|
| AZ (az-AZ) | **Microsoft Azure Speech** | `az-AZ-BabekNeural` (male) / `az-AZ-BanuNeural` (female) | **Native AZ accent.** ElevenLabs lists Azerbaijani in v3 but defaults bleed an English accent — disqualifying for "Yusif voice" series. |
| EN | **ElevenLabs Eleven v3** | Custom voice clone of Yusif (10 min sample) | Best emotional range, multilingual model |
| RU | ElevenLabs Eleven v3 | Same clone | Same model handles RU well |

**Cost estimate at our volume (10 pieces/week, ~150 chars each):**
- Azure: $4 / 1M chars → effectively $0 for our batch
- ElevenLabs Creator $22/mo (100k chars) covers EN + RU comfortably

**Pipeline integration:** Add Step 5.5 between Quality Gate and Video Render — `synthesize_voiceover(piece) → piece.audio_path`. Remotion `<Audio src={audio_path} />` inside compositions.

**Acceptance:**
1. Post #2 AZ voice-over passes Yusif's "is this AZ-native" listening test.
2. Pipeline auto-routes by `piece.language` (no manual provider selection).
3. Audio cached by content hash to avoid re-synthesis.

---

## 3. Distribution: Postiz — **DO NOW**

**Current gap.** Render produces MP4. Yusif still manually uploads to TikTok / LinkedIn / IG / Telegram. ~30 min/batch friction.

**Recommendation: [Postiz](https://github.com/gitroomhq/postiz-app) (Apache 2.0, self-hostable, 28k★).**

Why over Mixpost: 9× larger community (28k vs 3k stars), built-in API + webhooks for our pipeline, supports TikTok + LinkedIn + IG + Telegram + X + Bluesky + Threads.

Why over Buffer/Hootsuite: $100+/mo for SaaS, slower API, less control. Postiz = $0 + Hetzner box we already have.

**Pipeline integration:** Step 8 — `postiz.schedule(piece, when=monday_9am)` after Telegram delivery to CEO for approval.

**CEO approval gate stays manual** — Postiz schedules but does not publish until CEO clicks ✅ in Telegram.

---

## 4. HeyGen Avatar IV — Yusif Talking-Head Clone — **CEO BRAND CALL**

**The opportunity.** Series 2 ("Yusif voice" LinkedIn AZ) is the highest-leverage personal-brand surface. Currently bottlenecked on Yusif's time to film. HeyGen Avatar IV produces 4K talking-head video from text in 175 languages with native lip-sync.

**The decision.**
- **YES** → 5–7× output on Series 2. Posts daily instead of weekly. Cost: $29/mo Creator plan.
- **NO** → Stay text-on-screen + voice-over. Lower volume, 100% authentic.

**Brand risk.** AI clones still trigger uncanny-valley reactions in some audiences. ADHD/Gen Z research in our project (`docs/design/adhd-first-ux-research.md`) suggests: **acceptable if disclosed.** Recommend tagline overlay on AI-generated posts: "Made with my AI clone — original script by me."

**My recommendation:** YES, with disclosure overlay. Test with 3 posts. If engagement drops >20% vs. real-Yusif baseline, kill it.

**Effort if approved:** 30 min recording + 30 min HeyGen setup. Atlas wires `heygen.generate(script, avatar_id, voice_id) → mp4` as Step 6b alongside Remotion.

**Alternative if NO HeyGen:** [Hedra](https://www.hedra.com/) at $8–15/mo for expressive character (mascot) videos — pairs better with the Rive mascot system already in design shortlist.

---

## 5. Music Bed — **THIS MONTH**

**Current gap.** No music = TikTok algorithm disfavour. Stock music = generic.

**Recommendation: Suno v4.5** ($10/mo) for AI-generated background tracks tuned to brand. Generate 5–10 reusable beds per month, license-clean.

**ADHD constraint** (per Constitution): low-frequency, no vocals, sub-80 BPM during text-heavy segments. Bed defines a "VOLAURA sound" — same way visual identity does.

**Pipeline integration:** `MusicLibrary` table → `pick_bed(piece.tone)` → Remotion `<Audio src={bed} volume={0.15} />`.

---

## 6. AI B-roll — **OPTIONAL CEO CALL**

**The opportunity.** Replace static text frames with cinematic AI-generated b-roll (datacenter shots, founder typing, agent visualisations).

| Tool | Cost | Strength | Weakness |
|------|------|----------|----------|
| Google Veo 3.1 (via AI Pro) | $19.99/mo | Strongest free tier, no watermark, longest clips | Less directable than Sora |
| Sora 2 (via ChatGPT Plus) | $20/mo | Best motion + physics | Watermark on lower tiers |
| Runway Gen-4.5 | $12+/mo | Best editor / camera control | Pricey at scale |

**Risk.** AI video still uncanny for "real founder story" contexts. Works for abstract concept visualisation, fails for "this is my actual life."

**Recommendation:** **NO for now.** Our current direction (transparent AI-built startup story) benefits from screen recordings of real terminals + Cursor + the swarm running. That footage costs $0 and is more authentic than any AI b-roll.

**Revisit when:** we need cinematic explainer videos for fundraising / press.

---

## 7. Remotion Lambda — **LATER (auto-trigger when batch > 5/week)**

**The trade.**
- Local render: 1–5 min per 1-min video. Free. Atlas's machine.
- Lambda: ~30 sec per 1-min video, parallelised. ~$0.001–0.02 per render.

**Math.** At 10 videos/week = $0.10–0.20/week = $0.40–0.80/month. Cheaper than the pizza we'd buy waiting for local renders.

**Why not now.** Adds AWS Lambda deploy complexity to ZEUS pipeline. Worth it once batch hits 5+ pieces/week consistently.

**Trigger:** When Atlas's local render of weekly batch takes > 30 min, switch on Lambda.

---

## 8. What I REJECTED (and why)

| Rejected | Why |
|----------|-----|
| **Revideo** | Faster Canvas 2D rendering, but no React ecosystem — would force re-implementing our design system. Remotion's React + Tailwind aligns with `apps/web/`. |
| **Motion Canvas** | Built for animated explainers, not weekly social batch. No Whisper/captions integration story. |
| **Buffer / Hootsuite** | $100+/mo, proprietary, slower API. Postiz wins on every axis for our use case. |
| **Synthesia** | Pricier than HeyGen, fewer languages, weaker lip-sync on AZ. |
| **Captions.ai / OpusClip / Submagic** | Locked to their UI — can't run from `content_pipeline.py`. We'd be paying for a wrapper around Whisper + ffmpeg we already have. |
| **Bannerbear / Shotstack / Creatomate** | Cloud render APIs, $30+/mo, less flexible than Remotion's React composition model. |

---

## Suggested Sequencing

```
Week 1 (now):
  Day 1-2: Atlas implements #1 Captions → re-render Post #2 with word-by-word AZ captions
  Day 3:   Atlas wires #2 Azure TTS for AZ, ElevenLabs for EN/RU
  Day 4:   Self-host Postiz on Hetzner, wire CEO Telegram approval gate
  Day 5:   First fully automated batch goes through end-to-end

Week 2 (CEO decisions):
  - Decide HeyGen Avatar IV (#4): yes/no/test
  - Decide AI b-roll (#6): no for now / try Veo for one explainer

Week 3-4:
  - Add Suno music bed
  - Capture engagement data, tune

Month 2+:
  - When batch > 5/week, switch on Remotion Lambda
```

---

## Open Questions for CEO

1. **HeyGen Avatar IV** — yes / no / test for 3 posts? (Decision unblocks 5× Series 2 output.)
2. **Postiz hosting** — Hetzner box that already runs swarm, or new VPS? (Affects ops, not strategy.)
3. **Voice clone source** — record 10 min of Yusif speaking AZ + EN today, or wait? (Unblocks #2 EN/RU TTS quality.)

---

## Sources

- [Remotion captions overview](https://www.remotion.dev/docs/captions/)
- [Remotion + Whisper.cpp tutorial](https://www.remotion.dev/docs/install-whisper-cpp/convert-to-captions)
- [Remotion TikTok template](https://github.com/remotion-dev/template-tiktok)
- [ElevenLabs language support — incl. Azerbaijani](https://help.elevenlabs.io/hc/en-us/articles/13313366263441-What-languages-do-you-support)
- [Eleven v3 model overview](https://elevenlabs.io/blog/eleven-v3)
- [Microsoft Azure Speech — language support (az-AZ Banu, Babek)](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Remotion Lambda cost examples](https://www.remotion.dev/docs/lambda/cost-example)
- [Remotion vs Motion Canvas vs Revideo (2026)](https://trybuildpilot.com/363-remotion-vs-motion-canvas-vs-revideo-2026)
- [HeyGen pricing 2026](https://www.aitooldiscovery.com/guides/heygen-pricing)
- [Hedra review 2026](https://max-productive.ai/ai-tools/hedra/)
- [Postiz on GitHub (Apache 2.0)](https://github.com/gitroomhq/postiz-app)
- [Postiz vs Mixpost comparison](https://openalternative.co/compare/mixpost/vs/postiz)
- [whisper.cpp on GitHub](https://github.com/ggml-org/whisper.cpp)
- [whisper-large-v3-turbo](https://huggingface.co/openai/whisper-large-v3-turbo)
