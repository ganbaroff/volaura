# Founder workflow — the content→money machine (owner's view)

> 2026-06-10, Atlas thinking as the founder ("действуй так, словно это твой проект и он должен принести тебе реальные деньги. продумай весь воркфлоу. роли сам выбери"). No theatre: this is what I'd actually run if my own money were on the line, with the tech we already have activated or activating.

## Founder's first question: where does the money actually come from?
VOLAURA's revenue is **B2B** — companies pay to hire on verified AURA scores. Individuals are free (they build AURA → supply side). Video/content is **NOT the product** — it's the cheapest customer-acquisition engine that fills BOTH sides of the marketplace. So "the content workflow that makes money" only matters insofar as it drives the funnel. A founder never makes content for content's sake.

**Hard truth I must hold (my own standing rule):** VOLAURA's funnel is NOT ready for paid outreach yet — FIX-1✅, FIX-2✅ (RU live today), FIX-3 (selected-answer/D-4) NOT done, no clean human test pass yet. Pointing growth content at a leaky product burns reach. So the workflow has a **gate** and **two revenue loops**, and I'm honest about which is real *now*.

## The asset (why this is cheap to run — near-zero marginal cost)
- `volaura-video-worker` — PROVEN: AZ subtitles (faster-whisper large-v3), scene-clip cutter, TTS, file job-queue, Telegram-driven panel.
- **OmniVoice** (k2-fsa, Apache-2.0, 600+ langs incl. RU+AZ, voice cloning, RTF 0.025) — activating now; fills the contract's "AZ TTS doesn't exist" hole and replaces English-only Kokoro. **This is the keystone — a consistent cloned brand voice in AZ/RU/EN that essentially nobody in this market has.**
- **MoneyPrinterTurbo** (85k★, MIT, v1.3.0 today) — $0 stock-footage short-form generator. Replaces the expensive Veo path for volume content; Veo reserved for hero pieces only.
- Skills already in repo: `content-factory`, `video-script`, `social-post` (bilingual AZ+EN chains).
- $60k cloud credits, $0 inference gateway, PostHog $50k, Gemini/Groq for scripts.

## TWO money loops, one machine

### Loop A — cash NOW (weeks), and it is NOT gated by VOLAURA product-readiness
Sell the machine itself as a **productized service**: "AZ/RU/EN AI short-form video — N videos/week, fixed monthly price." Buyers = local AZ/CIS businesses + event orgs — **Yusif's COP29/WUF13/CIS network**, the exact warm B2B doors from the fundraise strategy, but for a product that is **ready today** (no legal gate, no product-clean dependency). $0 COGS → ~100% margin. Even 2–3 small retainers dwarf the <$100/mo burn and fund the **$3k legal** that unblocks VOLAURA's own funnel. This is the founder's scrappy bridge: the content machine pays for the company.

### Loop B — the real engine (months), gated behind product-clean
Point the SAME machine at VOLAURA's own brand once FIX-3 + a clean RU/AZ human test pass land. Content → candidates (supply) + org awareness (demand) → B2B SaaS revenue. **Loop A's clients become Loop B's first org pilots** — they already trust you, they hire people, they ARE the ICP. The two loops close: content service is a frictionless door to the corporate-HR pilots the fundraise doc said to chase.

## The workflow (repeatable weekly factory) + ROLES I'm assigning

| # | Role | Who/What | Does | Cost |
|---|------|----------|------|------|
| 1 | **Strategist** | Sonnet agent, weekly | Pick 3 angles tied to a money goal (Loop A: a target client's demo; Loop B: "verified skill > CV" proof stories). Reads market + persona. | $0 |
| 2 | **Scriptwriter** | Sonnet agent + `video-script` skill | Hook-first 15–60s scripts, AZ+RU+EN. | $0 (Groq/Gemini credit) |
| 3 | **Voice** | **OmniVoice** (self-host) | ONE cloned brand voice across every video, AZ/RU/EN. Consistency = the moat. | $0 |
| 4 | **Assembler** | worker + **MoneyPrinterTurbo** | MPT for $0 stock-footage volume; worker `gen_flow`→Veo only for hero pieces; burn AZ subtitles. | ~$0 / Veo sparing |
| 5 | **Brand/QA gate** | Sonnet agent + `guardrails`/`humanizer` | ADR-016 positioning lock (never "volunteer/LinkedIn-competitor"), never red, ADHD-safe, no AI-isms. Founder's reputation rides on every clip. | $0 |
| 6 | **Publisher** | **CEO — 1 tap from Telegram** | The ONLY required human gate: approve + post. Everything upstream automated. | minutes |
| 7 | **Analyst** | Sonnet agent + **PostHog** ($50k held) | Track content → signups/leads. Kill losers, double winners. Measure or it's not a business. | $0 |
| — | **Factory owner** | **Atlas** | Build/maintain the pipeline, weekly orchestration, wire the pieces, report numbers. | — |
| — | **Closer** | **CEO** | Loop A: close the first 1–2 content-service clients from his network. His superpower (sold COP29-scale ops + Golden Byte with $0 budget). | his time |

## Tech stack (founder's picks — $0-leaning, credits before cash)
Voice OmniVoice · Shorts MoneyPrinterTurbo + worker subtitles (faster-whisper az, local GPU) · Hero Veo via gen_flow (sparing) · Scripts Gemini 2.5 Flash (GCP credit) / Groq ($0) · Orchestration existing job-queue worker + Telegram (CEO's phone) · Analytics PostHog ($50k) · Distribution TikTok/Reels/Shorts/LinkedIn in AZ+RU+EN.

## Founder money-math (rough, labeled projection)
Loop A: 2–3 local retainers at a modest monthly fee, $0 COGS → covers burn many times + funds the $3k AZ data-consent legal → unblocks Loop B. Loop B (post-product-clean): each content-service client is a pre-warmed VOLAURA org pilot → the first B2B revenue line. **The content machine is both the wage and the funnel.**

## What would kill this (founder's pre-mortem)
- **Cadence, not quality, is the business.** 1 video is a demo; 100 consistent ones is a brand. The machine exists to make cadence free — but if we ship 5 and stop, it's dead.
- **Voice quality must be genuinely good** in AZ/RU — OmniVoice proof (WAV files) is the go/no-go; if it sounds robotic in Azerbaijani, the moat is gone and we fall back to real-voice + lip-sync.
- **Platform AI-content rules** — diversify across platforms, never single-point.
- **Solo-founder focus split** — Loop A is deliberately minimal/productized so it FUNDS focus on VOLAURA, not fragments it. If Loop A starts eating the week, cap it.
- **Don't violate the standing rule** — no VOLAURA "live product" growth claims until FIX-3 + clean test. Loop A (content service) is exempt; Loop B is not.

## The honest sequence (what I'd do as owner, in order)
1. **Finish the funnel floor:** FIX-3 (D-4) + one clean RU/AZ human test pass. (Days. Gates Loop B.)
2. **Prove the voice:** OmniVoice AZ/RU WAVs — Yusif's ear is the judge. (Today.)
3. **Stand up the factory v1:** Strategist→Script→OmniVoice→MPT→QA→Telegram-approve, end to end, 1 real video. (This is the build I own.)
4. **Loop A first sale:** Yusif pitches one network contact a fixed content retainer. Cash in.
5. **Turn on Loop B** once step 1 lands: same machine → VOLAURA brand → funnel → first org pilots (the Loop A clients).

Money is real when step 4 closes and step 5's first org says yes. Everything else is plumbing — and the plumbing is ~$0.
