# VOLAURA Ecosystem — Design Libraries Shortlist
**Date:** 2026-04-13 Baku
**By:** Cowork (Claude Opus 4.6)
**Purpose:** CEO asked "ты можешь найти лучшие библиотеки и репозитории с навыками дизайна для тебя и готовыми элементами?" — this is the researched answer. Every pick justified against Constitution v1.7 (NEVER RED, ADHD-safe, prefers-reduced-motion mandatory).

---

## Decision matrix

| Concern | Pick | Rejected | Why |
|---|---|---|---|
| Core components | **shadcn/ui** (already in) | Mantine, MUI, DaisyUI | Tailwind-native, copy-paste ownership, no runtime, built on Radix (AAA a11y). Already chosen in Redesign Brief v2. |
| Headless primitives | **Radix UI** (via shadcn) | Headless UI, React Aria standalone | Radix covers dialogs, dropdowns, tooltips with AAA a11y. React Aria is excellent but overlap with Radix; keep as escape hatch for complex patterns only. |
| Animation engine | **Motion** (ex-Framer Motion, already in) | GSAP, React Spring, AutoAnimate | Motion passed 16M monthly downloads in 2026, declarative React API, `useReducedMotion()` native. GSAP license proprietary since 2024 — rejected in Brief. |
| Landing / marketing eye candy | **Magic UI** (already approved in Brief) | Aceternity UI | Magic UI 20K+ stars, 50+ animated components. Aceternity rejected in Brief as "too visually stimulating for ADHD" — keep rejection. |
| Character / mascot animation | **Rive** (NEW — add) | Lottie | Rive state machines map to real product state (energy mode, badge tier); 5–10× smaller files (16KB vs 240KB); interactive without code glue. Lottie kept for simple loaders/icons only. |
| Icons | **Lucide React** (already standard) | Heroicons, Radix Icons | Already chosen. Design System Audit flagged emoji-as-icon bug — Lucide is the replacement. |
| Charts | **Recharts** (already in) + Nivo (deferred) | Chart.js, Visx | Recharts adequate for AURA radar. Nivo as upgrade path when radar becomes premium feature (per Brief). |
| Number transitions | **@number-flow/react** (Brief v2) | react-countup, react-spring numbers | Approved in Brief v2. 5KB. Complies with Law 4 (max 800ms) via default settings. |
| List / DOM animations | **@formkit/auto-animate** (Brief v2) | Framer Motion layout, React Flip Toolkit | Approved in Brief v2. 6KB. Zero config. Respects prefers-reduced-motion. |
| Forms | React Hook Form + Zod (already in) | Formik, react-final-form | Already standard per `.claude/rules/frontend.md`. |
| Server/client state | TanStack Query + Zustand (already in) | Redux, Jotai, SWR | Already standard per frontend.md. |

---

## New registries to mine (not adopt wholesale)

- **21st.dev** (serafimcloud/21st) — largest shadcn-compatible marketplace. Treat as "stock photos" — browse, copy individual components, strip decoration, validate against ADHD rules before shipping. **Never auto-install an entire section.**
- **Cult UI** — shadcn registry, decent cards/hover patterns. Similar rule: copy selectively.
- **Animate UI** — shadcn registry focused on motion primitives. Safer than Aceternity.
- **Kokonut UI** — shadcn registry. Check per-component before use.
- **registry.directory** — explorer for all shadcn registries. Starting point for browsing.

**Rule of use:** for every component we import from any registry:
1. Read the source
2. Strip any animation longer than 800ms
3. Add `prefers-reduced-motion` fallback if missing
4. Verify color palette — reject any red/destructive reds
5. Run through `constitution_checker.py --only-live` before commit

---

## MCP servers to connect / use

| MCP | Status | Why |
|---|---|---|
| **Figma MCP** | ✅ Connected (ganbarov.y@gmail.com, Pro) | `get_metadata`, `get_design_context`, `get_screenshot`, `get_variable_defs`, `search_design_system`, `get_code_connect_map`, `create_design_system_rules`, `generate_diagram`. Cowork will use all of these once CEO provides a Figma file URL. |
| **shadcn MCP** (ui.shadcn.com/docs/mcp) | ⬜ Not connected | Lets Cowork/Atlas install shadcn components via natural language in the repo. Worth connecting — one-time setup. |
| **Rive** | ⬜ No official MCP | Use web workflow (Rive editor → `.riv` export → `@rive-app/react-canvas`). No MCP needed but worth a skill file to remember the workflow. |

Action: ask CEO to share a Figma URL so Cowork can drive Figma directly. Atlas to add shadcn MCP config to `.claude/mcp.json` (optional, P3).

---

## Token / theming workflow

**Decision:** Tailwind 4 `@theme {}` block in `apps/web/app/globals.css` is the source of truth. No tailwind.config.js. No separate Figma token tool (for now — Tokens Studio is overkill at our size).

**Pipeline (proposed):**
1. Tokens defined in `globals.css` with semantic names (`--color-energy-full`, `--color-energy-mid`, `--color-energy-low`, `--color-badge-gold`, etc.).
2. Figma variables mirror the same names (manual sync at first — 1 hour work).
3. `mcp__Figma__get_variable_defs` pulls Figma variables; diff against `globals.css` fires a CI warning if drift > 5%.
4. Radix primitives wrapped with a thin `components/ui/*` layer that consumes tokens only — no hardcoded hex.

**Outcome:** one change in `globals.css` propagates everywhere, Figma matches code, design system audit score goes from 62/100 → 90+ on the token dimension alone.

---

## Skills Cowork will lean on

Internal design skills now available:

- `design:design-system-management` — token governance + pattern library
- `design:design-critique` — structured feedback loop (Cowork critiques own plan + Atlas's implementation)
- `design:accessibility-review` — WCAG 2.1 AA audit on every ship
- `design:ux-writing` — microcopy (CTAs, empty states, error messages) in AZ + EN
- `design:user-research` — synthesize existing 17 CEO research docs into actionable themes
- `design:design-handoff` — developer specs from every design delivery

Cowork will run these in the order: research-synthesis → critique → design-system → handoff → accessibility.

---

## External references that drove these picks

- Builder.io, Untitled UI, DesignRevision, Subframe — 2026 roundups of React UI libs
- Rive.app and dev.to UIAnimation series — Rive vs Lottie for interactive mascots
- Motion.dev docs — GSAP vs Motion comparison
- 21st.dev + registry.directory — active shadcn marketplace
- Constitution v1.7 — Law 1–5 + Crystal Laws (internal, authoritative)

---

## Next steps (Cowork owns)

1. Phase-0 design plan (`docs/design/PHASE-0-ECOSYSTEM-DESIGN-PLAN.md`) — written in same session as this file.
2. Once CEO provides a Figma URL, Cowork runs the first Figma MCP sweep + design critique.
3. Token audit: diff `globals.css` vs Brief v2 spec, produce a migration PR.
4. ADHD accessibility layer: "Focus Mode" toggle + cognitive-load reducer as a global provider in `apps/web/app/[locale]/layout.tsx`.

---

## Sources (live)

- [14 Best React UI Component Libraries in 2026 — Untitled UI](https://www.untitledui.com/blog/react-component-libraries)
- [15 Best React UI Libraries for 2026 — Builder.io](https://www.builder.io/blog/react-component-libraries-2026)
- [Best Tailwind Component Libraries 2026 — DesignRevision](https://designrevision.com/blog/best-tailwind-component-libraries)
- [Motion — JavaScript & React animation library](https://motion.dev/)
- [GSAP vs Motion — motion.dev docs](https://motion.dev/docs/gsap-vs-motion)
- [Rive vs Lottie — Rive official](https://rive.app/blog/rive-as-a-lottie-alternative)
- [21st.dev GitHub — serafimcloud/21st](https://github.com/serafimcloud/21st)
- [registry.directory — shadcn registry explorer](https://registry.directory/)
- [shadcn/ui MCP server docs](https://ui.shadcn.com/docs/mcp)
- [awesome-shadcn-ui — birobirobiro](https://github.com/birobirobiro/awesome-shadcn-ui)
