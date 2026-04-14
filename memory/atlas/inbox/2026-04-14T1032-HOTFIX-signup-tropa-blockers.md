# HOTFIX — Signup Tropa Blockers (CEO-tested 2026-04-14)

**Priority:** P0 — preempts all running epics. Fix before continuing E3/E4/E6 work.
**Source:** CEO manual test of first-time-user path, 2026-04-14 ~10:30 UTC.
**Outcome required:** CEO can complete signup → assessment → AURA score → badge in one session today.

## 6 bugs, by criticality

### BUG #1 — CRITICAL BLOCKER — Invite-only без выхода
`/signup` требует "Dəvət kodu" как обязательное поле. Новый реальный пользователь не может зарегистрироваться — hard блокер тропы.

**Correction to earlier brief:** нет таблицы `invite_codes`. Механизм — одна env var на Railway: `BETA_INVITE_CODE` (см. `apps/api/app/routers/auth.py:107-127` + `config.py:85-86`). Default: `open_signup=False`, `beta_invite_code=""` → every code returns `valid=False`. Constant-time `hmac.compare_digest` against single string.

**Immediate fix (to unblock CEO test TODAY) — pick ONE:**
1. **Option A (cleanest):** `railway variables set BETA_INVITE_CODE=CEO-TEST-2026-04-14 --service volaura-api` → redeploy → write code to `memory/atlas/inbox/2026-04-14T-invite-code-for-ceo.md` and ping CEO Telegram.
2. **Option B (temporary open):** `railway variables set OPEN_SIGNUP=true --service volaura-api` → CEO tests tropa → `railway variables set OPEN_SIGNUP=false` immediately after. Log both moments to `memory/atlas/journal.md`.

Atlas has Railway CLI access (verified Session 108). Pick Option A — safer, доказуемо обратимо, CEO получает конкретный код.

**Structural fix (separate task, not today) — money/risk-class:**
- CEO solo-decision next session: keep closed-alpha invite-gate OR switch to waitlist+email-confirm.
- Document to `memory/decisions/2026-04-1X-invite-gate-strategy.md` with rationale.

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
Форма отправила, spinner, тихо вернулась в initial state. Нарушение Constitution Law 1 (never silent on error; fail visibly but not red).

**Copy уже существует, Law 3-compliant (проверил AZ locale):**
- `signup.errorGeneric` = `"Bizim tərəfdə nəsə düz getmədi — bir az sonra yenidən cəhd edin."` ✅ shame-free ("наша сторона", не "ты").
- `signup.inviteCodeInvalid` = `"Keçərsiz dəvət kodu. Zəhmət olmasa, yenidən cəhd edin."` ✅

**Fix:** в signup form `onError` handler — ветвление:
- `422` + `detail.code === "INVITE_INVALID"` → inline под invite-код поле: `t("signup.inviteCodeInvalid")`
- любой другой `4xx/5xx` / network fail → toast ИЛИ inline под submit: `t("signup.errorGeneric")`
- Цвет: `#D4B4FF` (purple per Law 1), не red. Убедиться что `role="alert"` + `aria-live="polite"`.

Frontend файл: `apps/web/src/app/[locale]/(auth)/signup/page.tsx` (client component) — найти `onSubmit`/`mutation.onError`. Также проверь что backend возвращает именно `{"code": "INVITE_INVALID", ...}` формат (см. `auth.py` — возможно просто 422 без code — тогда дополнить).

Налоги Constitution Law 1 + Law 3.

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
If any fix takes >3 hours without progress → write to `memory/atlas/inbox/` wit