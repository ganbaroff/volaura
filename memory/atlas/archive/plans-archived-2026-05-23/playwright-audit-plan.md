# Playwright E2E Audit Plan — For Atlas Execution

**Created:** 2026-04-12 (Cowork planning session)
**Executes:** Atlas in Claude Code
**Quality standard:** Apple + Toyota. Every flow must work like clockwork before a human touches it.

---

## Pre-requisites (Atlas does this first)

1. Fix `e2e-runner.md` — update backend URL from `modest-happiness-production` → `volauraapi-production`
2. Verify Playwright is installed: `cd apps/web && npx playwright install chromium`
3. Create `apps/web/e2e/helpers.ts` if it doesn't exist — auth helpers, API setup

## 5 Persona Journeys to Test

Each persona = 1 spec file. Run 100+ assertions total across all personas.

### 1. Leyla (22yo, mobile, Baku) — `e2e/leyla-journey.spec.ts`
```
- Land on volaura.app → see landing page in AZ
- Register (email + password) → redirected to welcome
- Welcome page → single CTA to start assessment
- Start assessment → first question appears
- Answer 5+ questions → assessment completes
- See AURA score + radar chart + badge tier
- Score counter animation ≤ 800ms (Law 4)
- No red anywhere on any screen (Law 1)
- Share button works (generates link)
- Mobile viewport (375x812) — all flows
```

### 2. Nigar (HR manager, desktop) — `e2e/nigar-journey.spec.ts`
```
- Login as org admin → see org dashboard
- Search talent by competency → results appear
- Filter by badge tier → filtered
- View talent profile → AURA score visible
- Invite via CSV → upload, parse, send
- Desktop viewport (1440x900)
```

### 3. Kamal (34yo, professional) — `e2e/kamal-journey.spec.ts`
```
- Register → complete assessment → get Gold badge
- Visit /profile → see AURA score + "Discoverable" indicator
- Share AURA → LinkedIn share URL generated
- Retake assessment → 7-day cooldown enforced (expect block)
```

### 4. Anti-gaming bot — `e2e/antigaming.spec.ts`
```
- Start assessment → spam identical answers ("good good good")
- Expect: all_identical_responses flag triggered
- Expect: score penalized (< 40 = no badge)
- Start assessment → very short answers (< 30 words each)
- Expect: min_length gate triggered
```

### 5. Constitution compliance — `e2e/constitution.spec.ts`
```
- Visit every page → grep rendered DOM for:
  - No red text-red-*, bg-red-* classes (Law 1)
  - No "you haven't" / "profile % complete" text (Law 3)
  - All animations < 800ms (Law 4, check CSS)
  - Single primary CTA per screen (Law 5)
- Test with prefers-reduced-motion: reduce → verify animations disabled
- Empty states: no shame language, warm invitation only
```

## Quality Gates

- ALL 5 spec files must pass on `chromium` project
- Leyla journey must also pass on `mobile` project (375x812)
- Zero flaky tests allowed — if a test fails intermittently, fix the test OR the product
- Screenshot diff on key screens (before/after baseline)

## Test Against Production

```bash
cd apps/web
PLAYWRIGHT_BASE_URL=https://volaura.app npx playwright test --reporter=html
```

Use the shadow user approach from `scripts/prod_smoke_e2e.py` — fresh user per run, bypass cooldown for testing.

## What Atlas Reports Back

After running all tests, Atlas writes:
1. `docs/E2E-AUDIT-RESULTS.md` — pass/fail per persona, screenshots of failures
2. Updates `memory/context/sprint-state.md` — E2E test count (was 0)
3. Files bugs in `memory/swarm/proposals.json` for any failure that needs code fix
4. Sends summary to Telegram via ambassador bot

## Definition of Done

```
DONE when:
- 5 spec files, 100+ assertions, all green
- Leyla mobile journey passes
- Anti-gaming gates verified working
- Constitution 5 Laws verified on every page
- Zero red, zero shame text, zero >800ms animation
- Test report saved as HTML artifact
```
