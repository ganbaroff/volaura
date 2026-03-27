# AI Twin — Concept Document v1.0
> Yusif's design, 2026-03-27 | Agent-critiqued + revised

## Core Concept

A digital avatar powered by the user's own character_state JSON "brain."
Not an autonomous agent. Not a metaverse NPC. Not ElevenLabs.

**The user's AI Twin:**
- Knows their AURA scores, verified skills, login streak, Life Sim stats
- Can speak in their style (not pretend to be them — "drafts for approval" pattern)
- Lives in a simple visual world (their Life Sim character, eventually)
- Is theirs: personal, private, controlled by them

---

## What It Is / Is Not

| IS | IS NOT |
|----|--------|
| AI that drafts text in your tone | AI that speaks as you without your approval |
| Voice synthesis of YOUR character's story | Autonomous agent acting on your behalf |
| Personal knowledge base from your data | Replacement for your real presence |
| Metaverse character you guide | Celebrity deepfake |
| Optionally voice-enabled (Kokoro) | ElevenLabs subscription at $22/month |

**Critical pattern: AI draft + user approves.**
Лейла agent identified "AI speaks FOR you" as reputational risk. Revised: AI generates draft → user reviews → user publishes. Never autonomous.

---

## Phases

### Phase 1 (Now — text only, $0 extra cost)
- AI Twin is a text interface: "Ask your character anything"
- Powered by character_state JSON (crystals, skills, stats, streak)
- Example: "Your character has Communication 78 and Leadership 65. What volunteer role fits you best?"
- Gemini 2.5 Flash as brain (already in stack)
- No video. No voice. Just context-aware responses.
- Cost: $0 (Gemini free tier handles volume)

### Phase 2 (Sprint A4 — voice, Kokoro)
- Kokoro TTS (82M params, Apache 2.0, CPU, Railway deployable)
- User records 30-second voice sample → Kokoro voice-clones
- AI Twin can narrate your character's story in your voice
- Free tier: 48h queue. Crystal skip: 10 crystals → 1h. Pro: immediate.
- Cost: $0 (CPU inference, Railway resource already paid)

### Phase 3 (Sprint A5+ — animated photo)
- User uploads one photo
- SadTalker or Wav2Lip makes it talk (open source)
- No real-time. Batch generate video clip.
- 72h queue (free) → 25 crystals (2h) → Pro (immediate)
- Cost: ~$0.01-0.05 per generation (Replicate or self-hosted)

### Phase 4 (Year 2 — AI avatar video)
- Custom 3D/2D avatar (not user's face)
- Talking head reads your messages
- HeyGen or open-source alternative
- Ultra tier / enterprise feature
- Cost: TBD at scale

---

## Multi-Avatar Interaction (Simplified)

**NOT:** Real-time AI-to-AI autonomous chat (too complex, ZEUS dependency)

**YES:** Async message exchange
1. User A's AI Twin sends a message to User B
2. Stored in Supabase (Realtime subscription)
3. User B reviews → publishes as themselves
4. Pattern: identical to MiroFish swarm (async, consolidated summary)

This is buildable in Sprint A5 with zero new infrastructure.

---

## Technical Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Brain (context) | character_state JSON → Gemini 2.5 Flash | Free tier |
| Voice synthesis | Kokoro (CPU, self-hosted) | $0 |
| Expressive voice | Bark via Replicate [laughs][coughs][sighs] | $0.01/response |
| Animated photo | SadTalker (open source) | Replicate: $0.03/video |
| Fine-tuned voice | Parler-TTS on Modal.com | $0.003/response |
| Storage | Supabase Storage | Free tier |
| Queue | priority_queue table + pg_cron | $0 |

**Removed from plan:** ElevenLabs ($22/month = 7 responses/day — 70x worse than alternatives)

---

## BrandedBy Integration

The AI Twin concept extends naturally to BrandedBy:
- Celebrities ALREADY have verified identity (SIMA) + face data
- Celebrity AI Twin = digital version for fan interactions
- Fan asks celebrity twin a question → celebrity reviews/edits AI draft → publishes
- This is the celebrity engagement feature that justifies BrandedBy premium

BrandedBy Phase 1 implementation uses this same "AI draft + approve" pattern.

---

## Privacy Principles

1. Character data never leaves user's control (no selling, no sharing without consent)
2. Voice sample stored encrypted, user can delete anytime
3. "AI speaking as you" always shows [AI Draft] label until user explicitly publishes
4. AI Twin's outputs are tagged as AI-generated in LinkedIn posts
5. No training on user data without explicit opt-in

---

## Success Metrics

| Phase | Success Signal |
|-------|---------------|
| Phase 1 (text) | 20% of users ask AI Twin something in first week |
| Phase 2 (voice) | 5% of users generate voice clip, 40% share it |
| Phase 3 (video) | 2% of users generate video, crystal purchase rate doubles |
| Multi-avatar | Average 3 AI Twin interactions per active user per month |
