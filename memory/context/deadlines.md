# Deadlines & Pressure Context

Purpose: Give Claude a sense of time pressure. Update at session start/end.

## Current Sprint (updated 2026-04-03, Session 82+)
- **Volaura: Session 82 — security audit complete, analytics live, protocol v7.1**
- **BrandedBy: Sprint B1-B2-B3 COMPLETE ✅** — E2E verified
- **Ecosystem: 5 products (VOLAURA prod, MindShift 92%, Life Sim 65%, BrandedBy research, ZEUS 70%)**
- **CEO target:** End of April 2026 = platform at 100%
- **Budget remaining:** ~$50/mo
- **LRL: 96/100** (after security fixes 2026-04-02)

## Blocked By (Yusif must do)
- ~~`supabase db push`~~ ✅ All migrations applied via MCP
- ~~Disable email confirmation~~ ✅ Already OFF
- ~~Legal entity jurisdiction~~ → Georgia chosen (CEO-QUESTIONS-RESOLVED.md)
- ~~Payment processor~~ → Paddle chosen, CEO starts in 2 days (2026-04-05)
- **Register on volaura.app as User #1** (profiles table empty)
- **GitHub secrets:** SUPABASE_PROJECT_ID + SUPABASE_SERVICE_KEY (for GDPR retention workflow)
- **startup.az:** Tech Lead name from Slavyan (still missing)
- **Legal:** ToS + PP review by AZ counsel (~$300-500)

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

## Infrastructure Status (updated 2026-04-02 Session 82)
| System | Status | Notes |
|--------|--------|-------|
| Railway API | ✅ LIVE | All API keys set. CRON_SECRET configured. |
| Vercel Frontend | ✅ LIVE | volaura.app deployed |
| Supabase DB | ✅ LIVE | 59+ migrations. Security audit clean (0 ERRORS). |
| Supabase Realtime | ✅ LIVE | notifications table in publication, RLS verified |
| GitHub Actions | ✅ LIVE | tribe-matching + analytics-retention workflows |
| Sentry | ✅ LIVE | error monitoring on backend |
| Telegram Bot | ✅ LIVE | bidirectional swarm communication |

## Key Dates
- CEO target: End of April 2026 = platform at 100%
- Paddle integration: CEO starts ~2026-04-05 (2 days)
- startup.az: filed, pending Tech Lead name
- GITA (Georgia): May 27, 2026 deadline
- First users: 12,000 volunteers ready on CEO's signal
