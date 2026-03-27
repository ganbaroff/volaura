# Deadlines & Pressure Context

Purpose: Give Claude a sense of time pressure. Update at session start/end.

## Current Sprint
- **Volaura: Sprint 10 IN PROGRESS** (org dashboard done, activation wave pending)
- **BrandedBy: Sprint B1-B2-B3 COMPLETE ✅** — E2E verified, LIVE on volaura.app
- **Ecosystem: Sprint A0 COMPLETE ✅ | Sprint A1 NEXT**
- **Weeks remaining:** ~1 week (of 6 total, started 2026-03-23)
- **Budget remaining:** ~$50/mo + fal.ai (pay-per-video ~$0.05-0.10 each)

## Blocked By (Yusif must do)
- ~~`supabase db push`~~ ✅ All 35 migrations applied via MCP (Sessions 43-50)
- ~~Disable email confirmation~~ ✅ Already OFF (confirmed Session 43)
- **GoDaddy A record for brandedby.xyz** → `@ 76.76.21.21` (5 min action)
- Post 003 angle decision ("Antigravity" rejected as Mistake #40)
- Legal entity jurisdiction — Georgia, Turkey, or AZ?
- Pasha Bank meeting date
- Monetization pricing confirmation: 4.99 AZN/month for Pro confirmed?
- Payment processor: Stripe or Kapital Bank first?
- ~10 HR coordinator names for activation wave referral codes

## Milestone Status
- Week 1 end: ✅ Backend + DB complete (74 tests)
- Week 2 end: ✅ Frontend scaffold + auth working + all UI components built
- Week 3 end: ✅ Integration sprint done + security hardening (3 CRITICAL resolved)
- Week 4 end: ✅ Sprint 9 — CSV invite, assessment flow fixes, assessment hardening (512 tests)
- Week 5: ✅ Sprint A0 — character_state thalamus + monetization docs + BrandedBy B1-B2-B3
  - character_events + game_crystal_ledger + game_character_rewards LIVE
  - BrandedBy: brandedby.* schema, 8 API routes, personality service
  - BrandedBy: ZeusVideoSkill E2E verified (Kokoro TTS + SadTalker, ~2 min)
  - BrandedBy: share mechanic (LinkedIn + TikTok) LIVE on volaura.app
  - Activation wave infra: Groq fallback, referral tracking, scenario_ru
  - Org B2B dashboard: /me/dashboard + /me/volunteers live
- Week 6 (current): ⏳ Sprint A1 (crystal bridge) + activation wave + beta launch
  - Remaining: UTM capture, welcome page, badge share, RU translations

## Infrastructure Status (as of 2026-03-27 Session 50)
| System | Status | Notes |
|--------|--------|-------|
| Railway API | ✅ LIVE | FAL_API_KEY + GROQ_API_KEY now set. Video worker running. |
| Vercel Frontend | ✅ LIVE | volaura.app → latest deploy with BrandedBy |
| Supabase DB | ✅ LIVE | 35 migrations applied |
| fal.ai | ✅ LIVE | Balance topped up. SadTalker + Kokoro E2E verified. |
| GitHub Actions | ✅ LIVE | swarm daily run at 09:00 Baku |
| Sentry | ✅ LIVE | error monitoring on backend |
| brandedby.xyz | ⏳ PENDING | Added to Vercel, needs GoDaddy A record @ 76.76.21.21 |
| Telegram Bot | ⚠️ UNVERIFIED | CEO hasn't confirmed receipt |

## Key Dates
- Beta launch target: End of Week 6 (~2026-04-03)
- Anthropic application deadline: TBD (Yusif's timeline)
- Pasha Bank meeting: TBD (CEO relationship)
- First 100 volunteers: Free tier (business decision, no paywall on assessment)
