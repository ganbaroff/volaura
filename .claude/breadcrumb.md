# Session Breadcrumb — 2026-04-11 (Session 93)

## 🔴 READ FIRST (каждую сессию, особенно после /compact)
`C:\Users\user\.claude\projects\C--Projects-VOLAURA\memory\reference_file_map.md` — полная карта проекта. 14 разделов, все критичные пути. 2 минуты чтения = полная ориентация без grep. CEO directive Session 93.


## Где мы
Sprint: Sprint 0 (Ecosystem Wiring) — **bridge → assessment → AURA flow UNBLOCKED**
Last commit: 5c0b006 — submit_answer no longer pre-marks session completed
Branch: main (всё запушено)
Model: Opus 4.6 1M context (switched from Sonnet 1M mid-session)

## Что сделано этой сессией (2 prod bugs зафикшено)

### Bug #1 — bridge не создавал profiles row
**Симптом:** E2E smoke показал `/api/assessment/start` → 500 INTERNAL_ERROR для bridged user
**Root cause:** `assessment_sessions.volunteer_id NOT NULL REFERENCES profiles(id)`. Bridge создавал `auth.users` через `admin.auth.admin.create_user`, но никогда не создавал соответствующий `profiles` row. Register flow делает это явно; bridge пропустил.
**Impact:** Каждый user приходящий из MindShift через bridge НЕ мог начать assessment.
**Fix:** `auth_bridge.py` → `_ensure_profile_row()` — idempotent UPSERT после определения `shared_user_id`. Username = `u{uuid_hex[:16]}` (collision-free).
**Commit:** 8b153e0

### Bug #2 — submit_answer pre-marked session completed, AURA never written
**Симптом:** После fix #1 assessment проходит, но `aura_updated=False` и `/api/aura/me` → 404
**Root cause:** `submit_answer` линии 583-584 устанавливали `status="completed"` в DB когда CAT стопился, но НЕ вызывали `upsert_aura_score`. Потом `/complete/{session_id}` видел status=completed, шёл в BUG-015 idempotency branch и возвращал `aura_updated=False` без RPC. Никогда не writingalось.
**Impact:** КАЖДЫЙ user который проходил assessment до естественного CAT stop оставался без AURA score. В прод — сколько?
**Fix:** Убрал `update_payload["status"] = "completed"` из submit_answer. `/complete` теперь единственный owner finalisation pipeline.
**Commit:** 5c0b006

### Proposals cleanup
21 stale pending proposals вычищены → 0 pending. Все были либо empty output, либо уже реализованные (ANUS sandboxing × 6), либо уже исправленные (leaderboard Law 5), либо мета-жалобы на CTO процесс.

## Что работает в prod (verified via real E2E)
- Bridge → profiles row created
- Assessment start → first question
- Answer loop → CAT drives to is_complete
- Complete → aura_updated=True
- /aura/me → returns total_score + badge_tier
- Anti-gaming flags `all_identical_responses` correctly when smoke uses generic answers (expected)

## Key files
- `scripts/prod_smoke_e2e.py` — real user journey smoke (deploy verification)
- `scripts/debug_aura_rpc.py` — admin-direct RPC debug (used to isolate bug #2 to complete endpoint)

## Что НЕ сделано (следующая сессия)

1. **Git-diff injection** — sprint-state говорит "L1 pending", но фактически session-end.yml УЖЕ делает это. Обновить sprint-state чтобы отразить done.
2. **Gemini 2.5 Pro** — ключ есть, нужен биллинг на aistudio.google.com → swarm judge upgrade
3. **Frontend E2E** — real user walk на volaura.app через browser. Backend E2E теперь OK, UI надо проверить.
4. **Backfill existing bridged users** — если bridge уже работал на проде, но profiles не создавался, возможно есть auth.users без profiles rows. Скрипт `scripts/backfill_bridged_profiles.py` чтобы всем существующим bridged пользователям создать profile.
5. **Backfill AURA для completed-без-AURA sessions** — если user #2 бага был в проде долго, могут быть completed sessions без aura_scores row. Скрипт re-run upsert_aura_score для них.

## Следующая сессия — priorities (если CEO не скажет иное)
1. Backfill сценарии (2 скрипта) — возможно никто из реальных users не пострадал, но надо проверить
2. Frontend E2E walk (browser)
3. Gemini 2.5 Pro biling
4. Уточнить фронт flow — правильно ли клиент вызывает /complete после is_complete=true
