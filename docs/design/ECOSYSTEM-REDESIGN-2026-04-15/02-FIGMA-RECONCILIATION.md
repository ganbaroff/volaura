# P0.5 — Figma ↔ globals.css reconciliation

**Date:** 2026-04-15 · **Source:** Figma file `B30q4nqVq5VjdqAVVYRh3t` page `0:1` "Design System" v2
**Method:** `mcp__claude_ai_Figma__get_metadata` (variable_defs endpoint blocked — needs manual node selection in Figma desktop)
**Depends on:** 00-BASELINE.md, 01-TOKENS-AUDIT.md
**Status:** partial — metadata scraped from frame names, formal variable definitions still require Figma desktop selection

---

## Why metadata, not `get_variable_defs`

`get_variable_defs` returned:
> "You currently have nothing selected. You need to select a layer first before using this tool."

The Figma MCP variable endpoint requires the Figma desktop app to have a node actively selected by a human. Headless agent call not supported. Workaround for this pass: extract token values from frame text labels (Design System page is self-documenting, each swatch has its hex in the layer name). Lossy — no type info, no aliases, no scopes — but values are verifiable.

**Next step when a human opens Figma:** CEO or Cowork selects the root node in Figma desktop, reruns `get_variable_defs`. Then a proper machine-readable token export lands here.

---

## 1. Surface palette (full match on 5/6, 1 drift)

| Semantic name | Figma v2 | globals.css primitive | Match |
|---|---|---|---|
| Base (darkest) | `#0A0A0F` | — (closest: `--color-surface-container-lowest: #0d0d15`) | ❌ drift 3 shades darker in Figma |
| Surface 1 | `#13131B` | `--color-surface: #13131b` | ✅ |
| Card | `#1B1B23` | `--color-surface-container-low: #1b1b23` | ✅ |
| Elevated | `#1F1F27` | `--color-surface-container: #1f1f27` | ✅ |
| High | `#292932` | `--color-surface-container-high: #292932` | ✅ |
| Highest | `#34343D` | `--color-surface-container-highest: #34343d` | ✅ |

**Action:** add `--color-surface-base: #0a0a0f` as primitive below `-lowest`, or reconcile by moving `-lowest` to `#0a0a0f`. Figma is source of truth for visual design, so CSS follows. Flag for Phase 1 token pass.

## 2. Accent palette (4/6 match, 1 drift, 1 missing layer)

| Semantic | Figma v2 | globals.css | Match |
|---|---|---|---|
| Primary | `#C0C1FF` | `--color-primary: #c0c1ff` | ✅ |
| Primary Deep | `#8083FF` | `--color-primary-container: #8083ff` | ✅ |
| Success | `#34D399` | `--color-success: #6ee7b7` | ❌ drift — Figma is emerald-400, CSS is emerald-300 (2 stops lighter) |
| Warning | `#E9C400` | `--color-warning: #e9c400` | ✅ |
| Error (Purple!) | `#D4B4FF` | `--color-error: #d4b4ff` | ✅ (Constitution Law 1) |
| Gold | `#FFD700` | `--color-aura-gold: #ffd700` | ✅ |

**Success drift — decision required:** Figma #34D399 is the brighter, CEO-approved v2. CSS #6ee7b7 is an older value. Ship CSS update in Phase 1 token pass.

**Product accent colors (Volaura `#7C5CFC`, MindShift `#3B82F6`, LifeSim `#F59E0B`, BrandedBy `#EC4899`, Atlas `#10B981`):** NOT present on this Figma page. Either on another page or never migrated to Figma. If never migrated, the 01-TOKENS-AUDIT.md §6 open question about product palette mismatch is unresolved because there is no design source — only code is. Phase 1 decision: either (a) bring product accents into Figma as a Tier-3 palette, or (b) accept code as source of truth for product tier and document that split.

## 3. Design philosophy captured in Figma that must live in code rules

The Figma page isn't just swatches — it encodes rules. Each needs a code/linter equivalent.

| Figma annotation | What it means | Enforcement proposal |
|---|---|---|
| "ERROR STATES — Purple/Amber, NEVER Red (Research #2, #6, #8: RSD)" | Constitution Law 1 restated as RSD-specific rationale | Already in `.claude/rules/`. Add lint check: any `text-red-*` / `bg-red-*` / `#xx[0-3]000` class → CI fail. |
| "❌ OLD — Red triggers RSD shame" with example label `Xəta baş verdi — yenidən cəhd edin` | Canonical error copy pattern — shame-free AZ language | Add to `apps/web/src/i18n/*/common.json` canonical errors, audit existing error strings against it. |
| "ACHIEVEMENT — Identity Headline, Score as Context (Research #10: Overjustification)" | AURA screens must lead with identity label ("Gold-level Communicator"), not with number ("78.4") | Audit `apps/web/src/app/[locale]/aura/**` and profile pages. Lint rule harder — semantic, needs agent review. |
| "❌ Number as headline" vs "✅ Identity as headline" | Direct contrast pattern | Propose component `<AuraHeadline identity={...} score={...} reason={...} />` that enforces structure. |
| "EMPTY STATE — One warm action, no quantified incompleteness" | Empty states cannot show "0/8 complete" or "% complete". One CTA. AZ copy: "Hələ AURA balınız yoxdur / İlk qiymətləndirməni tamamlayın — 5 dəqiqə, 1 bacarıq." | Constitution Law 3 (shame-free). Lint-able — `<ProgressBar>` + empty state in same screen = warning. |
| "GLASS CARD — Selective glassmorphism (hero cards only, NOT nav/forms)" | `.liquid-glass` utility should not apply to navigation or form surfaces | Audit uses of `.liquid-glass`, `.glass-header`, `.glass-nav` — are any used inside forms? If yes, flag. |
| "BUTTONS — Gradient primary, ghost secondary (shadcn extended, NOT replaced)" | Keep shadcn/ui button base, extend with gradient variant for primary CTA — one per screen | Constitution Law 5 (one primary). Audit `<Button variant="primary">` count per page. |
| "TYPOGRAPHY — Inter + Plus Jakarta Sans (AZ characters: ə ğ ı ö ü ş ç)" | Body = Inter. Headlines = Plus Jakarta Sans. AZ charset must render correctly at all weights. | globals.css has `--font-sans: Inter` and `--font-headline: "Plus Jakarta Sans"`. ✅ encoded. Add visual regression test with AZ string for each weight. |
| Typography scale text labels: `24px Bold / 18px SemiBold / 10px SemiBold tracking +15% / 14px Regular / 12px Medium muted` | 5 explicit tier specs | globals.css has `--font-*` families but NO size scale — this is 01-TOKENS-AUDIT.md §5 missing category #5 confirmed. Add `--text-caption: 12px`, `--text-body: 14px`, `--text-overline: 10px` + tracking, `--text-section: 18px`, `--text-page: 24px`. |

## 4. Figma structures that exist but aren't in code yet

Derived from frame layout — designs CEO has approved but code doesn't implement:

- **Achievement card pattern** (`<Frame 5:42>`): identity headline + score sub-line + "because you demonstrated X" attribution line. No such component in `components/features/aura/`.
- **Empty-state warm CTA card** (`<Frame 5:57>`): title + subcopy + single-button CTA, no progress ring, no percent. Components currently skew to showing 0% complete on empty.
- **Glass card with explicit spec annotation** (`<Frame 5:62>`): "backdrop-blur(16px) · 6% white border · 70% surface opacity". Current `.liquid-glass` uses `blur(12px)` + `12%` border + variable opacity. Drift: Figma is slightly heavier blur, lighter border. Reconcile or document as intentional.

## 5. Figma canvas coverage — what's NOT on page `0:1`

- No form field primitives (input, textarea, select, radio, checkbox)
- No navigation primitives (top bar, bottom nav, sidebar)
- No data viz (radar, progress, sparklines)
- No modal/dialog
- No toast/alert
- No avatar pattern with AURA frame glow
- No product-product transition/linkage components (cross-ecosystem)

**Phase 1 Figma task:** either expand this file to cover the 7 categories above, or create linked library files. Not blocking Phase 0 close.

## 6. Priority queue entering Phase 1

| # | Item | Confidence | Blocker? |
|---|---|---|---|
| 1 | Add `--color-surface-base: #0a0a0f` OR move `-lowest` to `#0a0a0f` | Figma-confirmed | No, visual tweak |
| 2 | Update `--color-success: #34d399` (was `#6ee7b7`) | Figma-confirmed | No |
| 3 | Add typography size tokens (5 tiers from Figma) | Figma-confirmed | Yes for new components |
| 4 | Resolve product accent palette question (§6 of 01-TOKENS-AUDIT) | Open — needs CEO | Yes — identity decision |
| 5 | Rerun `get_variable_defs` after CEO selects node in Figma desktop | Waiting on human | Partial — current data is sufficient to proceed, better data available later |
| 6 | Build the 7 missing Figma categories in §5 | Requires design work | Yes for Phase 2 |

## 7. Notes for the human who rerun `get_variable_defs` later

1. Open Figma desktop, file `B30q4nqVq5VjdqAVVYRh3t`.
2. Select the "Design System" page root (click empty canvas once so page is focused).
3. Have Claude rerun the MCP tool — it will return a JSON map of `variable_name → value` (not just colors — also fonts, sizes, spacings if they exist as variables).
4. If the map is sparse, variables were never created as Figma Variables (they're just layer-name labels). In that case, someone needs to convert the palette into actual Figma Variables (Design → Variables panel in Figma).

MEMORY-GATE: task-class=doc-update · SYNC=⏭️ · BRAIN=⏭️ · sprint-state=✅ · extras=[figma-B30q4nq-metadata, 01-TOKENS-AUDIT, globals.css] · proceed
