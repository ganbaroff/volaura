# HANDOFF — Design System Assembly (VOLAURA ecosystem)

**From:** Cowork-Atlas (design/content lane)
**To:** the design agent that will assemble/ship the ecosystem design
**Date:** 2026-06-26
**Status of this doc:** authoritative handoff. Built by reading the live repo, not memory.
**Lane note:** this is a *spec* handoff. The receiving agent edits design/CSS/components in the **Code-Atlas lane** — coordinate, do not fork. No code was changed to produce this doc.

---

## 0. TL;DR — do we even have branding / structure / architecture?

**Yes — extensively. The problem is not absence, it is fragmentation + stale canon + missing assets.**

- We have a real, *live* design system (dark "obsidian-glass", 3-tier tokens) in `apps/web/src/app/globals.css`.
- We have a governing **DESIGN-MANIFESTO** (7 laws + face contract) and a **Constitution** (5 Foundation Laws).
- We have **19 design docs** in `docs/design/` + more in `docs/`. That is *too many*, and some contradict each other.
- We have a thin but real **component library** and a clean **Next.js 14 App Router** architecture.

**The three things that are actually broken / missing:**
1. **Two sources of truth disagree.** The March `BRAND-IDENTITY.md` describes a *light-mode, indigo, red-error, JetBrains-Mono* brand. The April manifesto + live CSS are *dark-first, #c0c1ff/#7C5CFC, purple-error-never-red, Plus Jakarta Sans*. A design agent that follows the wrong file rebuilds the wrong product **and violates the Constitution** (red errors are banned).
2. **No brand assets are shipped.** The logo, favicon, illustration set, competency icons and verification badges are *specified* in `BRAND-IDENTITY.md` but **do not exist on disk** (`apps/web/public` has 0 SVGs, no logo files).
3. **The "5 faces feel like one body" ecosystem layer is mostly unbuilt** (face-aware theming is P0 and NOT STARTED).

---

## 1. CANONICAL SOURCE ORDER (read this first — binding)

When two docs disagree, the higher one wins. This order resolves the contradiction.

1. `apps/web/src/app/globals.css` — **live tokens. Ground truth for color/spacing/type/energy.**
2. `docs/ECOSYSTEM-CONSTITUTION.md` — 5 Foundation Laws (supreme).
3. `docs/design/DESIGN-MANIFESTO.md` — 7 Design Laws + Face Definition contract.
4. `.claude/rules/ecosystem-design-gate.md` — the pre-build gate (16 anti-patterns, tiers, transitions).

**Use for STORY/VOICE ONLY, NOT visuals:** `docs/design/BRAND-IDENTITY.md` — its brand story, positioning, voice/tone, AZ language rules and logo *concept* are still valid. Its **colors, fonts, light-mode and red errors are STALE — ignore them.**

**Historical / planning only (do not treat as canon):** the other ~15 files in `docs/design/` (REDESIGN-MEGAPLAN, PHASE-0/1, GAP-INVENTORY, BASELINE, STITCH-DESIGN-SYSTEM, etc.) and `docs/archive/DESIGN_*`.

### The contradiction, explicit (so it can't be gotten wrong)

| Dimension | BRAND-IDENTITY.md (Mar 2026 — STALE) | CANON (globals.css + Manifesto, Apr 2026+) |
|---|---|---|
| Mode | Light (near-white surfaces) | **Dark-first** obsidian `#13131b` ("always dark") |
| Primary | indigo `oklch(0.65 0.25 275)` ≈ `#6D28D9` | `#c0c1ff` (primary) · product-volaura `#7C5CFC` |
| Errors | rose **RED** `oklch(0.65 0.25 25)` | **purple `#d4b4ff` — RED IS BANNED (Law 1)** |
| Mono font | JetBrains Mono | none in canon; headline = **Plus Jakarta Sans**, body = Inter |
| Energy modes | not present | **Full / Mid / Low required from day 1** |
| Scope | single product | **5 faces, one body** |

**Action item (P0, this handoff requests it): retire the stale visual half of `BRAND-IDENTITY.md`** — annotate it as "story/voice only; visuals superseded by globals.css" so no future agent re-introduces light mode or red.

---

## 2. Brand — what exists vs what must be built

**Valid now (from BRAND-IDENTITY.md, keep):**
- Positioning: "Make verified talent visible, measurable, portable." Tagline **"Your Skills, Verified."** Pillars: Verified · Visible · Valued · Growing.
- Voice: formal-but-warm, empowering, transparent. AZ uses formal **"siz"**. Word choices: *Assessment* (not Test), *AURA Score* (not rating/rank), *Earn*, *Journey*, *Opportunity*. CTAs are strong verbs ("Start Assessment", "Share Badge"). Never "Click here" / "Submit".
- Logo **concept**: stylized "V" + 3 concentric "aura" rings; wordmark in a bold sans.

**Missing on disk — MUST be designed/produced (currently zero assets):**
- Logo kit: full lockup, icon-only, monochrome, white-reverse — as **SVG**, in canon dark colors (icon stroke uses `--color-primary #c0c1ff` or product accent, **not** the stale indigo).
- `favicon` + Apple touch icon.
- Illustration set (flat, geometric): characters, scenes, empty-states (paths planned at `public/illustrations/...`).
- 8 competency icons + 3 verification-badge icons (specified in BRAND-IDENTITY §6, not built).
- Per-face icons (24×24 inline SVG, active/inactive) for VOLAURA/MindShift/LifeSim/BrandedBy.

---

## 3. Design tokens — CANON = `globals.css` (use tokens, never raw hex in components)

3-tier architecture (Tier 1 primitive → Tier 2 semantic → Tier 3 product). Key live values:

- **Surfaces (dark):** base `--color-surface #13131b`; containers `lowest #0d0d15` → `low #1b1b23` → `#1f1f27` → `high #292932` → `highest #34343d`.
- **Primary (indigo focus):** `--color-primary #c0c1ff`, `--color-primary-container #8083ff`, `--color-on-primary #1000a9`.
- **Tertiary / gold:** `--color-tertiary #e9c400`.
- **Error (purple, Law 1):** `--color-error #d4b4ff`, container `#3d1a6e`. **Never red.**
- **Warning:** amber `#e9c400`. **Success:** `#6ee7b7`.
- **Text:** `--color-on-surface #e4e1ed`, variant `#c7c4d7`; outline `#908fa0` / `#464554`.
- **Focus ring:** `--color-ring #FFFFFF` (21:1 on dark, 4.7:1 on primary — always visible).
- **Product accents (Tier 3, applied via `[data-product]`):** volaura `#7C5CFC` · mindshift `#10B981` · lifesim `#F59E0B` · brandedby `#EC4899` · atlas-system `#5EEAD4` (system-only, never a user tab).
- **Fonts:** body `--font-body "Inter"`, headline `--font-headline "Plus Jakarta Sans"`.
- **Radius / shadow / z / motion:** radii `sm .25 → 2xl 1.5rem`; shadows sm/md/lg + `--shadow-glow`; durations `fast 150 / normal 300 / slow 500 / max 800ms`; spring `damping 14, stiffness 100`.
- **Energy modes:** `[data-energy="full|mid|low"]` (min touch target 44/48/56px; low disables all animation).

**Token GAP to fix (P1): typography size tokens are NOT in CSS.** Add to `@theme`:
`--text-page:24px; --text-section:18px; --text-body:14px; --text-caption:12px; --text-overline:10px; --tracking-overline:0.15em;` then replace ad-hoc `text-sm/lg/2xl` with these. (Account for AZ text +20–30%.)

---

## 4. Non-negotiables — 5 Foundation Laws + anti-patterns (Constitution + gate)

Genetic constraints. A face that breaks one is malformed.
1. **Never red.** Errors purple `#D4B4FF`, warnings amber `#E9C400`, destructive purple-container.
2. **Energy modes** Full/Mid/Low — every screen, day one.
3. **Shame-free language** — no "you missed 3 days", no completion %, no streak punishment.
4. **Animation ≤ 800ms** + `prefers-reduced-motion` mandatory (instant).
5. **One primary CTA per screen.**

Plus the gate's anti-patterns: no spinners (skeletons only), no score-as-headline (identity first), no infinite scroll, no glass on forms/nav, no autoplay, no browser-default focus ring, no pure `#000000` (min `#0a0a0f`), no thin body fonts (<400), no face-specific Tier1/2 tokens, no duplicate components, no silent faces (must write `character_events`).

---

## 5. Architecture (CANON = repo)

- **Stack:** Next.js 14 App Router · TypeScript strict · Tailwind v4 (`@theme` in globals.css) · shadcn-style UI · Framer Motion · TanStack Query · Zustand · react-i18next (**AZ primary, EN second**) · PWA.
- **Routing:** `apps/web/src/app/[locale]/(auth|dashboard|public)/…` + `admin`, `callback`, `welcome`.
- **Component layers (the Skeleton/Skin rule — Manifesto Principle 1):**
  - `components/ui/` = **skeleton**, face-agnostic primitives. Present: `alert, avatar, button, card, empty-state, product-placeholder, skeleton, social-auth-buttons, toast`. **Missing from the inheritance contract: `ProgressBar`** (+ future agent-avatar / agent-speech / cross-face-card).
  - `components/features/{domain}` and per-domain folders (`assessment, aura, dashboard, events, lifesim, …`) = **skin**, accent-aware.
- **Theming mechanism:** `[data-product]` swaps Tier-3 accent today. **`[data-face]` context does NOT exist yet** (see P0 gap).
- **"Skeleton or skin?" is the first question** for any new UI. Skeleton change = Constitution-level, affects all faces.

---

## 6. Gaps the design agent must close (verified against `MANIFESTO-GAP-ANALYSIS.md` + this audit)

Current alignment: **~70%.** Clean already: no-red ✅, no leaderboard ✅, no profile-% ✅, no thin fonts ✅.

**P0 (blocks the ecosystem):**
- **EGAP-1 Face-aware component theming** — add `[data-face]` context so Cards/Buttons re-theme on tab switch. "Without this, five faces are impossible." NOT STARTED.
- **Source-of-truth reconciliation** — adopt §1 canon order; annotate stale `BRAND-IDENTITY.md`.

**P1:**
- Ship the **brand asset kit** (§2) — currently zero on disk.
- **Typography tokens** in CSS (§3); **global `:focus-visible`** style (defined token, not applied).
- Replace **63 spinners** with content-shaped skeletons; fix **streak-shame copy** (`tribe-card.tsx` "Keep your streak alive"); add **`ProgressBar`**.
- **Cross-face event card** + **tab-bar face-switch animation** (200ms accent crossfade, prefetch) + **cross-face moment cards** (dual-accent, deep link). Backend (`character_events`) is ready; frontend is zero.
- Real content for **one non-VOLAURA face (MindShift is closest)**.

**P2:** Figma↔CSS token drift (Figma `#0A0A0F` vs code `#0d0d15`, success `#34D399` vs `#6ee7b7`, glass blur 16 vs 12); remove `autoPlay` in brandedby; agent-character UI slots; energy testing across faces.

---

## 7. Task brief for the design agent (phased, with acceptance criteria)

**Phase 0 — Align (½ day).** Read the 4 canon files. Produce `docs/design/SOURCE-OF-TRUTH.md` (1 page) that states the canon order and retires the stale visual half of BRAND-IDENTITY. *Done when:* the contradiction table is resolved in-repo and BRAND-IDENTITY.md carries a "visuals superseded" banner.

**Phase 1 — Brand assets (1–2 days).** Produce logo kit (lockup/icon/mono/reverse SVG) + favicon + per-face icons + 8 competency + 3 verification icons, all in canon dark tokens. *Done when:* assets live under `apps/web/public/brand/…`, render on dark `#13131b`, pass contrast, and the icon uses a canon accent (not `#6D28D9`).

**Phase 2 — Token + primitive hygiene (1 day).** Add typography tokens; global focus-visible; `ProgressBar`; kill spinners→skeletons; fix shame copy. *Done when:* gap-analysis P1 product rows are closed.

**Phase 3 — Ecosystem layer (2–3 days).** `[data-face]` theming (P0); cross-face event card; tab-bar transition; MindShift face real content. *Done when:* switching tabs re-themes accent live, and one cross-face moment renders end-to-end.

### Definition of Done for ANY component (from design-handoff skill)
- References **tokens, not raw values** (`var(--color-…)`, never inline hex).
- Renders correctly at **Full / Mid / Low** energy.
- Implements **all states**: default · hover · active · disabled · **loading (skeleton, not spinner)** · empty · error.
- Visible **`:focus-visible`** (white ring); keyboard-operable; ARIA name/role/value; logical focus order.
- Contrast: body **≥7:1** on surface (we exceed AA); large text ≥4.5:1; UI ≥3:1.
- **No red; one primary CTA;** writes to `character_events` if it represents a user action.
- AZ tested with `ə ğ ı ö ü ş ç` at every weight (account for +20–30% length).

---

## 8. Open decisions for CEO (only Yusif can answer — keep to these 3)
1. **Logo:** keep the "V + aura-rings" concept and have the agent produce it, or commission a fresh mark?
2. **Light mode is officially dead** (canon says dark-only). Confirm so we can retire it everywhere, not just in code.
3. **Which face gets real design after VOLAURA?** (Recommendation: MindShift — closest to buildable, and it already has a live prototype.)

---

## 9. How this handoff was produced (skill fingerprints, anti-theater)
- `design:design-handoff` → structure (tokens-not-values, all-states, edge cases, accessibility, "describe the why"), the Phase briefs + Definition-of-Done.
- Design-system audit (read `globals.css`, manifesto, gap-analysis, brand-identity) → the contradiction table + token inventory + gap list.
- `design:accessibility-review` rules → the contrast/focus criteria in §7 DoD.
- Verified on disk: `apps/web/public` has 0 SVGs (assets missing); `components/ui` has 9 primitives; 19 docs in `docs/design/`.

**Canon files to open first:** `apps/web/src/app/globals.css` · `docs/design/DESIGN-MANIFESTO.md` · `docs/ECOSYSTEM-CONSTITUTION.md` · `.claude/rules/ecosystem-design-gate.md`.
