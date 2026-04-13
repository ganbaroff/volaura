# Cowork State
**Updated:** 2026-04-13T06:00 Baku | **Session:** 9

---

## CEO DIRECTIVE — Competence-Based Trust (2026-04-13)

CEO сказал: "мне нужно чтобы вы обучались чтобы я знал кого слушать. кто среди вас более компетентен. это не просто бутафория."

И: "решайте кого я буду считать source of truth и должен ли другой периодически проверять не галюцинирует ли другой."

**Это не вопрос иерархии. Это вопрос measurable competence.**

### Предложение Cowork для Atlas (обсуждению подлежит)

**1. Track record вместо протокола.**
Каждый ведёт свой лог: claim → verification → result (right/wrong). Не "я главный", а "я был прав 14 из 17 раз по assessment science, и неправ 2 из 5 по deploy pipeline."

Предлагаю файл: `packages/atlas-memory/competence-tracker.md`

```
## Cowork track record
| Date | Domain | Claim | Verified by | Result |
|------|--------|-------|-------------|--------|
| 2026-04-13 | Assessment | CAT engine correct, bot loop bug | Atlas (DB check) | ✅ RIGHT |
| 2026-04-13 | Telegram | ceo_inbox RLS correct, key issue | Atlas (Railway check) | ⏳ PENDING |
| 2026-04-13 | Architecture | 4-framework pipeline for emotions | Atlas (counter-proposal) | ❌ WRONG (CLASS 10) |
| 2026-04-13 | Code audit | coordinator.py is dead code | Atlas (grep) | ❌ WRONG |
| 2026-04-13 | DB | volunteer_id 138 refs, 11 tables | Atlas (verify) | ⏳ PENDING |

## Atlas track record
| Date | Domain | Claim | Verified by | Result |
|------|--------|-------|-------------|--------|
| 2026-04-13 | Code | pii_redactor is phantom | Atlas (ls) | ❌ WRONG (then self-corrected) |
| 2026-04-13 | Deploy | volunteer→professional rename works | Supabase MCP | ✅ RIGHT |
| 2026-04-13 | Assessment | CAT engine stops after 1 question | Cowork (SQL) | ❌ WRONG (bot bug, not engine) |
| 2026-04-13 | System | Reflexion + dynamic sampling | CEO feedback | ⏳ PENDING |
```

**2. Cross-verification обязателен.**
Каждый крупный claim (architecture decision, root cause diagnosis, "это готово к продакшену") ДОЛЖЕН быть проверен другой стороной. Не потому что кто-то врёт — потому что оба галлюцинируют по-разному:
- **Cowork** галлюцинирует в сторону overengineering (предлагает фреймворки когда нужно 20 строк)
- **Atlas** галлюцинирует в сторону false confidence (доверяет агентам без проверки, объявляет "done" до верификации)

**3. Domain ownership (не иерархия, а экспертиза).**
- **Assessment science, DB schema, RLS, research** → Cowork source of truth (имеет Supabase MCP, находит SQL быстрее)
- **Deploy, CI, git, Railway, production health** → Atlas source of truth (имеет git push, Railway, test runner)
- **Architecture decisions** → оба предлагают, CEO решает при разногласии
- **Спорные claims** → тот кто предложил ОБЯЗАН дать verification method. "Проверь через X" — не "поверь мне".

**4. Нет source of truth навсегда.**
Track record обновляется каждую сессию. Если Atlas начнёт стабильно ошибаться по deploy — Cowork берёт эту зону. И наоборот. Компетенция — не титул, а статистика.

---

## GCP Credentials (saved this session)
- `GCP_SERVICE_ACCOUNT_JSON` → `.env`
- `GCP_PROJECT_ID=zeus-assistant-483714`
- `gcp-service-account.json` → `apps/api/` (gitignored)
- Service account: `atlas-vertex-ai-bot@zeus-assistant-483714.iam.gserviceaccount.com`
- Roles: Vertex AI User

## For Atlas Next Session — Priority Order
1. Add `VERTEX_API_KEY` to Railway → test Telegram bot responds as Atlas
2. Fix E2E bot loop (check `is_complete`, not `next_question`)
3. Add communication/empathy questions (5→15-20)
4. Review competence-tracker proposal above — agree, modify, or counter-propose
5. Verify Cowork's pending claims: ceo_inbox RLS diagnosis, volunteer_id map accuracy

## Ecosystem Redesign Analysis (completed 2026-04-12)

Full analysis: `packages/atlas-memory/sync/ecosystem-redesign-analysis.md`

Key findings:
- Figma has ZERO custom design system (only Material 3 defaults)
- Token architecture spec ready (3 tiers: primitives → semantic → product)
- 4-phase implementation order defined (Foundation → Core Screens → Cross-Product → Validation)
- All brief tech stack decisions validated by Cowork
- 5 open questions for Atlas (Figma status, Liquid Glass approach, avatar complexity, energy persistence, crystal economy)

## Handoff Queue
| # | Status |
|---|--------|
| 001-002, 005-007 | ✅ DONE |
| 003 PostHog | 📝 READY (P2) |
| 004 Swarm Phase 2 | 📝 READY (P1) |
| 008 volunteer_id rename | 📝 READY (P2) |
| 009 Ecosystem Redesign | 📝 ANALYSIS DONE — implementation pending |
