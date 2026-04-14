# HOTFIX — Signup Tropa Blockers (CEO-tested 2026-04-14)

**Priority:** P0 — preempts all running epics. Fix before continuing E3/E4/E6 work.
**Source:** CEO manual test of first-time-user path, 2026-04-14 ~10:30 UTC.
**Outcome required:** CEO can complete signup → assessment → AURA score → badge in one session today.

## 6 bugs, by criticality

### BUG #1 — CRITICAL BLOCKER — Invite-only без выхода
`/signup` требует "Dəvət kodu" как обязательное поле. Новый реальный пользователь не может зарегистрироваться — hard блокер тропы.

**Immediate fix (to unblock CEO test TODAY):**
1. Generate one valid invite code for CEO: insert row into `invite_codes` table with `code = 'CEO-TEST-2026-04-14'`, `max_uses = 10`, `expires_at = now() + interval '7 days'`, `is_active = true`.
2. Send code to CEO via Telegram (or leave in `memory/atlas/inbox/2026-04-14T-invite-code-for-ceo.md`).

**Structural fix (separate task, not today):**
- Decide with CEO next session: keep closed-alpha invite-gate OR switch to waitlist+email-confirm.
- Not urgent — but document decision before real user onboarding begins.

### BUG #2 — CRITICAL — Layout-коллапс на `/signup` (desktop)
Контент сжат в ~100px column, всё рендерится вертикально по слову.

### BUG #3 — CRITICAL — Radio "Siz kimsiniz?" накладываются
Два варианта (Mən peşəkaram / Mən bir təşkilatı təmsil edirəm) рендерятся overlapping.

### BUG #5 — MEDIUM — Subtitle на главной рендерится вертикально
"AURA balınızı qazanın…" — каждое слово отдельной строкой.

**Hypothesis for #2, #3, #5 (CEO's read, confirmed by symptoms):** один CSS root cause. Родительский контейнер потерял `max-width` / `width` ИЛИ flex-родитель схлопывает children в `flex-direction: column` без `align-items`. Один коммит починит все три. 

**Debug path:**
1. Открой `/signup` и `/` в Playwright или локально, DevTools → Elements.
2. Посмотри computed width на корневом `<main>` или page container — если `width: auto` и flex-parent = `column` без `width: 100%` на child, вот оно.
3. Вероятные места: `apps/web/src/app/[locale]/layout.tsx`, `apps/web/src/app/[locale]/(auth)/signup/page.tsx`, `apps/web/src/components/ui/Container.tsx` или аналог, `apps/web/src/app/globals.css`.
4. Последний коммит который трогал layout — проверь `git log --oneline -- apps/web/src/app/[locale]/` и `globals.css` за 7 дней, возможно regression от какого-то из E4 commits (warmer Article 22 copy касался того же route).

### BUG #4 — MEDIUM — Hero пустой при cold load, появляется после reload
Тёмный прямоугольник на первой загрузке. После перезагрузки — OK.

**Hypothesis:** SSR/hydration mismatch ИЛИ Framer Motion animation которая не запускается без client trigger. Проверь:
- `apps/web/src/app/[locale]/page.tsx` — есть ли `"use client"` на hero component, есть ли `initial={{ opacity: 0 }}` без `animate` на первом рендере.
- Console на cold load — hydration warning?

### BUG #6 — MEDIUM — Нет error message при провале signup
Форма отправила, spinner, тихо вернулась в initial state. Нарушение Constitution Law 3 (Shame-Free? — нет, тут Law 1: never silent on error; fail visibly but not red).

**Fix:** в signup form `onError` handler — `toast.error(t("signup.error.generic"))` или inline error под submit button. Цвет: `#D4B4FF` (purple per Law 1), не red. Текст по-русски/AZ/EN должен сказать "что-то пошло не так у нас, попробуй ещё раз" — не "вы ввели неправильно".

Проверь также backend — что именно вернул `/v1/auth/signup`? Скорее всего 422 на invalid invite code, и frontend глотает это без UI.

## Order of operations

1. **NOW (5 min):** Generate invite code for CEO, send to him. CEO-unblocked.
2. **Today (2-3 hours):** Fix BUG #2/#3/#5 (one CSS root). Deploy. CEO re-tests.
3. **Today (1 hour):** Fix BUG #6 (error surface). Deploy.
4. **Tomorrow:** Fix BUG #4 (hero cold load). Lower priority.
5. **Separate task:** Invite-only strategic decision — NOT today.

## Definition of Done (this hotfix)

- [ ] CEO has working invite code in hand
- [ ] CEO opens `/signup` on desktop → sees proper horizontal layout, clear radio buttons
- [ ] CEO submits → either succeeds OR sees clear error message (purple, not red, not shaming)
- [ ] CEO reaches assessment page
- [ ] CEO completes assessment → sees AURA score + badge
- [ ] Screenshot of badge page in journal as proof

## Artifacts required
- Commit(s) with fix referencing this brief filename
- Journal entry `memory/atlas/journal.md` — "CEO tropa verified end-to-end" with timestamp
- Update sprint-state.md E2 DoD: "first non-CEO tester" → at minimum "CEO verified end-to-end"
- Decision log ONLY if invite-only strategic decision is made (not for the code fix itself)

## NOT in scope of this hotfix
- Energy picker (E3) — stays in its epic
- Grievance UI refinement (E4) — stays
- Tribe Matching CRON — stays in Atlas's current debug queue
- i18n AZ quality pass — next sprint

## Escalation
If any fix takes >3 hours without progress → write to `memory/atlas/inbox/` with blocker, tag Cowork. Do not silently continue.

Cowork. 2026-04-14 10:32 UTC.
