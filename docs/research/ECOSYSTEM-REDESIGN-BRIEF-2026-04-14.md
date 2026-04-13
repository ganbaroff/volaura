# VOLAURA Ecosystem Full Redesign Brief — 2026-04-14

**For:** Cowork (design lead) + Atlas (technical implementation)
**From:** Atlas, based on CEO directive + full ecosystem audit + 3 deep research tracks
**NotebookLM notebook:** 15c8b9c1-7fb5-41a0-926b-05a5dddad61f

**Cross-references:** [[ECOSYSTEM-CONSTITUTION]] | [[adhd-first-ux-research]] | [[ecosystem-design-research]] | [[blind-spots-analysis]] | [[NEUROCOGNITIVE-ARCHITECTURE-2026]] | [[gemini-research-all]] | [[VISION-FULL]] | [[MASTER-STRATEGY]] | [[TONE-OF-VOICE]]

---

## MISSION

Full redesign of the VOLAURA ecosystem visual language. Not one app — ALL FIVE products as one coherent experience. Every element research-backed and documented.

## THE 5 PRODUCTS

| Product | Purpose | Color | Status |
|---------|---------|-------|--------|
| VOLAURA | Verified talent assessment, AURA scoring | Indigo #c0c1ff | Live |
| MindShift | ADHD daily focus, habits, Mochi mascot | Emerald #10B981 | Live v1.0 |
| Life Simulator | 3D character progression, crystals, rooms | Purple #7C3AED | 65% dev |
| BrandedBy | AI twin avatars, video generation | Sky #0EA5E9 | 15% dev |
| ZEUS | Agent framework, neurocognitive AI | Gold #E9C400 | Local |

## 5 FOUNDATION LAWS (non-negotiable)

1. NEVER RED — errors = purple #D4B4FF, warnings = amber #E9C400
2. Energy Adaptation — Full/Mid/Low modes on every screen
3. Shame-Free — no "you haven't done X", no % complete, no streaks at 0
4. Animation Safety — max 800ms, prefers-reduced-motion mandatory
5. One Primary CTA — max 1 primary button per screen, max 5 tappable without scroll

## DESIGN SYSTEM DECISIONS (from research)

### Keep (validated by research)
- shadcn/ui — 112K stars, Tailwind-native, copy-paste ownership
- Motion (Framer Motion) — rebranded, same lib, already integrated
- Recharts — adequate for AURA radar (switch to Nivo if radar becomes premium feature)
- Obsidian glass dark theme — better than any off-the-shelf option
- Indigo primary #c0c1ff — trust + focus, research-backed color psychology

### Add
- Magic UI (20K stars) — complement for landing page animations
- ADHD Accessibility Layer — Focus Mode toggle, cognitive load audit, progress indicators
- Liquid Glass on AURA radar chart — glassmorphism with SVG backdrop-filter blur(5-15px)

### Reject
- Mantine — incompatible with Tailwind
- DaisyUI — no headless primitives, accessibility regression
- GSAP — license changed to proprietary 2024
- Aceternity UI — too visually stimulating for ADHD

## NAVIGATION ARCHITECTURE

Discord bottom-tab + Duolingo colors + Habitica avatar:

```
[VOLAURA] [MindShift] [Life Sim] [AI Twin] [Character Avatar]
```

- Max 4 visible tabs + character avatar as 5th (app switcher)
- Avatar tap → bottom sheet with all 5 products + crystal balance + stats
- Semantic color shifts when switching products
- 150ms tab transition animation (snappy, game-like)

## ANIMATION SPECIFICATIONS (from NotebookLM research)

- Spring physics: damping ≥ 14 (no bouncy entrances)
- useReducedMotion() hook — auto-fallback to opacity fades
- Prohibited: screen shake, infinite pulses (cap 3), floating orbs on action screens
- Confetti: max 12 particles, 1.5s max, separate celebration screen only
- Tab transitions: 150ms
- Page transitions: 200-300ms ease-out
- Micro-interactions: 100-200ms

## AURA RADAR CHART (premium feel)

- Liquid Glass container (backdrop-filter blur + 1px specular rim border)
- Identity-first: "Gold-level Communicator" headline, AURA 78.4 subtitle
- Behavioral evidence: 2-sentence AI-verified summary below chart
- Animation: staggered reveal of radar points (50ms per axis)

## CRYSTAL ECONOMY VISUAL LANGUAGE

8 Crystal Laws govern gamification. Key visual rules:
- Crystals NEVER shown during/immediately after assessments
- Badge tier reveals as surprise on next profile visit
- Crystal balance visible in character avatar bottom sheet, not main nav
- Earn animations: unexpected, brief, identity-reinforcing

## TYPOGRAPHY

- Headlines: Plus Jakarta Sans (geometric, professional)
- Body/Labels: Inter (clarity, accessibility)
- AZ strings: account for 20-30% longer text

## CEO'S RESEARCH FILES (must read before designing)

1. `docs/research/adhd-first-ux-research.md` — clinical ADHD UX foundation
2. `docs/research/ecosystem-design-research.md` — cross-product design
3. `docs/research/NEUROCOGNITIVE-ARCHITECTURE-2026.md` — ZenBrain 7-layer memory
4. `docs/research/gemini-research-all.md` — 140K words of deep research
5. `docs/ECOSYSTEM-CONSTITUTION.md` — 5 laws + 8 crystal laws
6. `docs/TONE-OF-VOICE.md` — brand voice (Tinkoff/Aviasales benchmark)
7. `docs/research/blind-spots-analysis.md` — 10 critical risks
8. `docs/VISION-FULL.md` — origin story, WUF13, Phase 3 vision
9. `docs/MASTER-STRATEGY.md` — revenue model, expansion plan

## SUCCESS CRITERIA FOR REDESIGN

1. Every color choice has a research citation
2. Every button size justified by Fitts's Law + ADHD cognitive load data
3. Every animation has timing, easing, and reduced-motion fallback documented
4. All 5 products feel like ONE ecosystem with semantic color shifts
5. Crystal economy visually integrated without violating 8 Crystal Laws
6. Character avatar is central navigation element across all products
7. ADHD accessibility audit passes: Focus Mode, progress indicators, limited choices
8. Figma file organized: primitives → semantic → component tokens (3-level system)
9. Every rejected alternative documented with reason

## FIGMA ACCESS

- Existing file: `B30q4nqVq5VjdqAVVYRh3t` (57 variables, Design System v2)
- Bergmann shadcn/ui kit available
- Figma MCP tools: get_design_context, get_screenshot, get_variable_defs, create_new_file
