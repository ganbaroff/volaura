# Constitution 3-Laws Audit — 2026-04-28 (Cowork-Atlas)

**Scope:** Swarm task `2026-04-29-cowork-task-assignment` — audit Laws 1 (Never Red), 3 (Shame-Free), 4 (Animation Safety) across VOLAURA ecosystem.

**Why code-based, not Figma:** Figma MCP authenticated successfully (`whoami` → ganbarov.y@gmail.com Pro tier). All Figma tools (`get_design_context`, `get_screenshot`, `search_design_system`, `get_libraries`, `use_figma`) require `fileKey` parameter. Repo-wide Grep for `figma.com/design/`, `figma_file_key`, `FIGMA_FILE` — zero matches. CEO did not provide Figma URL in chat. Code-based audit becomes primary deliverable; Figma sweep waits for URLs.

---

## LAW 1 — Never Red

**Verdict: PASS at token level.**

**Evidence (`apps/web/src/app/globals.css:67-115`):**
```css
--color-error:                      #d4b4ff;   /* light purple */
--color-error-container:            #3d1a6e;   /* dark purple */
--color-on-error:                   #1a0040;
--color-on-error-container:         #edd6ff;
--color-warning:                    #e9c400;   /* amber/gold */
--color-warning-container:          #3a3000;
--color-destructive:                var(--color-error-container);
--color-destructive-foreground:     var(--color-on-error-container);
```

40+ usages of `text-destructive`, `bg-destructive`, `border-destructive`, `hover:bg-destructive` across `apps/web/src/`. All resolve to purple via token alias. Semantic class name "destructive" preserved for accessibility tooling and shadcn compatibility, but visual rendering is Constitution-compliant.

`components/ui/button.tsx:9` documents this explicitly: `// Law 1: "destructive" uses purple (--color-error), not red`.

`apps/web/src/app/[locale]/(dashboard)/life/page.tsx:37` documents: `Law 1 — no destructive red; only primary / muted / border`.

**No raw red hex (#FF0000, #ef4444, #dc2626) found in `apps/web/src/`.** No Tailwind `red-NNN` classes. No `bg-red-*` / `text-red-*` / `border-red-*`.

**Outstanding:** MindShift Capacitor app at `C:/Users/user/Downloads/mindshift/` not in mounted folders — Law 1 audit there pending. ZEUS / BrandedBy / LifeSimulator faces are flag-locked (defaults false per `.env.example`) so user-facing path doesn't render those today. Path-E status from `for-ceo/living/reality-audit-2026-04-26.md`.

---

## LAW 3 — Shame-Free Language

**Verdict: PARTIAL PASS. 11 violations in `apps/web/src/locales/en/common.json`. AZ parity check pending.**

| # | locale | path | line | current | proposed replacement |
|---|--------|------|------|---------|---------------------|
| 1 | en | common.json | 135 | `"unexpectedError": "An unexpected error occurred"` | `"Something's off — please try again in a moment"` |
| 2 | en | common.json | 252 | `"coachingError": "Unable to load coaching tips"` | `"Coaching tips are taking a moment — refresh to retry"` |
| 3 | en | common.json | 468 | `"orgCreation": "Failed to create organization. You can create it from the organization page."` | `"Couldn't create the organization. You can try again from the organization page."` |
| 4 | en | common.json | 600 | `"errorLoad": "Could not load events"` | `"Events didn't load — pull to refresh"` |
| 5 | en | common.json | 649 | `"loadError": "Could not load events"` | `"Events didn't load — pull to refresh"` |
| 6 | en | common.json | 718 | `"errorInvalidTitle": "Invalid link"` | `"This link doesn't open"` |
| 7 | en | common.json | 719 | `"errorInvalidBody": "This link isn't valid. Links can only be used once. Contact the person for a new link."` | `"This link doesn't work — links can only be used once. Contact the person for a fresh one."` |
| 8 | en | common.json | 977 | `"searchError": "Search failed. Please try again."` | `"Search didn't go through — please try again."` |
| 9 | en | common.json | 1108 | `"load": "Failed to load event"` | `"Event didn't load — refresh to try again"` |
| 10 | en | common.json | 1163 | `"generic": "Failed to create event. Please try again."` | `"Couldn't create the event. Please try again."` |
| 11 | en | common.json | 1278 | `"invalidTitle": "This invite link is not valid."` | `"This invite link doesn't open."` |

**Compliant lines (good examples to model after):**
- line 116 `"That invite code didn't work. Double-check and try again."` ✓
- line 136 `"Something's off on our side — please try again in a moment."` ✓
- line 161 `"Sign-in didn't go through. Please try again."` ✓
- line 217 `"Couldn't start assessment. Server is busy. Please try again in a moment."` ✓
- line 219 `"Answer not saved. Check your connection and tap Submit again."` ✓
- line 220 `"Couldn't load next question. Your progress is saved — tap Try Again."` ✓
- line 450 `"No right or wrong — just show who you are."` ✓ (Constitution-aligned framing)
- line 733/775/1082 `"Something went wrong. Please try again."` ✓ (soft generic)

**Pattern:** `Failed to X` and `Could not X` and `Invalid X` are the three recurring shame-language structures. Replacement pattern is `Couldn't X` / `X didn't go through` / `X doesn't open`.

**AZ parity check pending** — sample lines reviewed (116, 136, 162, 217, 218) match EN-good patterns ("yenidən cəhd edin", "düz getmədi") — likely AZ already softer than EN. Full AZ audit deferred to next sweep.

---

## LAW 4 — Animation Safety (≤800ms + no spinners)

**Verdict: 8+ SPINNER VIOLATIONS. Skeleton-pulse usage Constitution-approved.**

**Constitution rule (`.claude/rules/ecosystem-design-gate.md` STEP 6):**
- "No spinners. Period."
- "WRONG: `<Loader2 className="animate-spin" />`"
- "RIGHT: `<Skeleton className="h-[200px] w-full rounded-xl" />` ← matches actual content shape"
- "animation ≤800ms + prefers-reduced-motion"

**Tailwind animation defaults:**
- `animate-spin`: 1000ms (>800ms ✗)
- `animate-pulse`: 2000ms cycle (ambient on Skeleton — Constitution-approved replacement)
- `animate-bounce`: 1000ms (>800ms ✗ if used)
- `animate-ping`: 1000ms (>800ms ✗ if used)

**Spinner violations (Loader2 + animate-spin or border-spinner div):**

| # | file | line | usage |
|---|------|------|-------|
| 1 | `components/ui/social-auth-buttons.tsx` | 101 | `<Loader2 className="h-4 w-4 animate-spin" />` in OAuth button |
| 2 | `components/ui/button.tsx` | 107 | Inline border spinner in Button loading state |
| 3 | `app/[locale]/(auth)/signup/page.tsx` | 431 | `<Loader2 className="mr-2 inline size-4 animate-spin" />` |
| 4 | `app/[locale]/(dashboard)/assessment/page.tsx` | 320 | `<Loader2 className="mr-2 size-4 animate-spin" />` |
| 5 | `app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx` | 553 | `<Loader2 ... animate-spin />` |
| 6 | (same file) | 618 | `<Loader2 ... animate-spin />` |
| 7 | (same file) | 767 | `<Loader2 ... animate-spin />` |
| 8 | `app/[locale]/(dashboard)/assessment/[sessionId]/complete/page.tsx` | 657 | `<Loader2 className="size-4 animate-spin" />` |
| 9 | (same file) | 724 | `<Loader2 ... animate-spin />` |
| 10 | `app/[locale]/callback/page.tsx` | 19 | `<div className="h-8 w-8 animate-spin rounded-full border-4 ..." />` |
| 11 | (same file) | 155 | `<div className="h-8 w-8 animate-spin ..." />` |
| 12 | `app/[locale]/(public)/verify/[token]/page.tsx` | 500 | `<div className="size-8 animate-spin ..." />` |

**Replacement pattern per ecosystem-design-gate.md:** `<Skeleton className="..." />` matching content shape — height/width of the actual content block being loaded. For inline button-loading state, replace Loader2 spinner with text-only state ("Saving...") or content-shape skeleton inside button.

**Skeleton-pulse usage (Constitution-approved, 12+ instances):**
- `components/ui/skeleton.tsx` itself
- `components/assessment/coaching-tips.tsx:39`
- `app/[locale]/welcome/page.tsx:212-214`
- `app/[locale]/(auth)/forgot-password/page.tsx:11`
- `app/[locale]/(auth)/reset-password/page.tsx:81-88`

These are KEEP — Skeleton IS the Constitution-approved Loading replacement.

---

## Cross-product status

| Product | Audit status | Reason |
|---------|--------------|--------|
| VOLAURA core (`apps/web/src/`) | Audited | This document |
| MindShift Capacitor app | NOT AUDITED | Source at `C:/Users/user/Downloads/mindshift/` — not in mounted folders. Atlas needs CEO mount or git access. |
| LifeSimulator | NOT AUDITED | No Godot files in repo (per `for-ceo/living/reality-audit-2026-04-26.md` — gameless API). Game project not in scope. |
| BrandedBy | DORMANT | `NEXT_PUBLIC_ENABLE_BRANDEDBY=false` per `.env.example` default. User-path 404. Skip until revival. |
| ZEUS | ARCHIVED | `packages/swarm/archive/` only. No UI route. Skip. |

VOLAURA core is the only currently-user-rendering face for VOLAURA web — audit covers what real users see today.

---

## Remediation priority

**P0 (block launch):**
- Law 4 spinner #3 (signup page 431) — first signup interaction shows banned spinner. Replace with content-shape Skeleton or text-only loading state.
- Law 4 spinners #4-9 (assessment flow) — assessment is the core product loop. 6 spinners across the journey. Replace systematically.

**P1 (week of launch):**
- Law 3 violations #6-7-8-11 (verify-link / invite-link Invalid messages) — first-time user via invite sees these on edge cases. Soft replacement.
- Law 3 violations #9-10 (event Failed to load/create) — events are core social loop.
- Law 4 spinners #10-12 (callback / verify-token) — auth edge paths.

**P2 (post-launch polish):**
- Law 3 violations #1-5 (generic errors) — fallback paths, less frequent.
- Law 4 spinner #1-2 (oauth button + button loading) — design-system level fix.
- AZ locale parity sweep.
- MindShift audit when source available.

**Effort estimate:** 11 i18n string changes (≤30 min total) + 12 spinner replacements (≤2 hours, since Skeleton component already exists) = ~3 hours of focused work. Single PR. Ships in one sprint.

---

## Method receipts

- Figma MCP `whoami` — Pro tier confirmed, no file URLs in repo.
- `Grep` red colors in `apps/web/src/`: 40+ `destructive`/`error` matches, all token-aliased to purple per `globals.css:67-115`.
- `Grep` shame language in `apps/web/src/locales/`: 11 violations enumerated above with line numbers.
- `Grep` animation patterns in `apps/web/src/`: 12 spinner instances vs 12+ skeleton-pulse instances (skeleton OK).
- `Read` `apps/web/src/app/globals.css:67-115` for token verification.
- `Read` `.claude/rules/ecosystem-design-gate.md` for Constitution rules (loaded via CLAUDE.md).
- Reality-audit-2026-04-26 cited for cross-product status (`for-ceo/living/reality-audit-2026-04-26.md`).

Audit completed 2026-04-28 by Cowork-Atlas. Governance event pending — to be logged after CEO ratifies findings.
