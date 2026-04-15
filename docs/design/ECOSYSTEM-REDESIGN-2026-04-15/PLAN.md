# VOLAURA Ecosystem Redesign — Master Plan

**Started:** 2026-04-15 00:30 Baku
**Directive:** CEO Yusif, Session 110 evening — "добить дизайн, Apple/Toyota quality, каждый элемент доказан"
**Owner:** Atlas (coordination + evidence + spec), Cowork (Figma), Claude Code (implementation), Perplexity (research)
**Standard:** Apple (taste + edit ruthlessly) × Toyota (genchi genbutsu + 5 whys) × Constitution v1.7

---

## NORTH STAR (не меняется)

> Лучший, самый современный, самый инновационный дизайн экосистемы из 5 продуктов (VOLAURA · MindShift · Life Simulator · BrandedBy · ZEUS), где каждый элемент доказан evidence-ledger'ом, где продукты визуально связаны как один организм, где энергетические режимы встроены в каждый экран, и где никакое решение не принимается "потому что нравится".

---

## CEO-зафиксированные требования

1. **Новая шрифтовая технология** — variable fonts + `text-wrap: balance/pretty` чтобы текст не ломался ни в одном контейнере.
2. **Scroll-driven animations** — элементы меняются при скроллинге через CSS `animation-timeline` (native 2024) + Framer Motion fallback.
3. **Кросс-продуктовая линковка** — 5 продуктов как единая экосистема, shared shell, identity continuity при переходах.
4. **Evidence-ledger** — каждое решение с доказательством (research / benchmark / A-B данные), не "вкусовщина".
5. **Energy modes** — Full / Mid / Low на каждом экране (Foundation Law 2).
6. **Apple/Toyota quality** — вырезать до одного правильного варианта; 5 whys до глубины; genchi genbutsu перед любым мнением.

---

## 6 фаз

### Phase 0 — Baseline (Atlas, 1 день)
**Зачем:** не рисовать по памяти. Посмотреть что сейчас реально живёт на проде.
**Что:**
- Скриншоты всех 18 страниц volaura.app на desktop + mobile viewport
- Сверка Figma Variables vs DESIGN-SYSTEM-AUDIT (март) vs live → что устарело, что PR #7 добавил
- Архивировать устаревшие docs/design/* в `docs/archive/design-pre-redesign-2026-04-15/`
- Список текущих dependencies (Tailwind, Framer Motion, shadcn версии)

**Выход:** `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/00-BASELINE.md` + папка `screenshots/`

### Phase 1 — Discovery swarm (Atlas + 8 агентов, 2 дня, параллельно с Phase 2)
**Зачем:** собрать все дыры глазами 8 специализаций, не одного человека.
**Агенты:**
- design-critique — визуальная иерархия, taste, consistency
- accessibility-auditor — WCAG 2.1 AA, keyboard nav, screen reader
- ux-research — JTBD, friction points, по 4 personas
- behavioral-nudge — cognitive load, decision fatigue, engagement
- cultural-intelligence — AZ/CIS, shame-free language, trust signals
- assessment-science — IRT UX, pre-assessment, DIF visual cues
- performance-engineer — Core Web Vitals, animation cost, font loading
- ecosystem-architect (новый) — cross-product identity, transitions, shared state

**Выход:** `01-GAP-INVENTORY-v1.md` — все дыры приоритизированы P0/P1/P2.

### Phase 2 — Evidence research (Perplexity, 2-3 дня, параллельно с Phase 1)
**Зачем:** каждое спорное решение должно опираться на внешний источник, не на "нам кажется".

**8 тем (полный brief в `02-PERPLEXITY-BRIEF.md`):**
1. Variable fonts 2026 — Inter Variable vs Figtree vs Geist vs Recursive; axes; `text-wrap: balance/pretty` поддержка; performance.
2. Scroll-driven animations — CSS `animation-timeline: scroll()` vs Framer Motion vs GSAP; browser support; accessibility; performance budget.
3. Cross-product design ecosystems — Linear+Raycast+Arc, Notion suite, Adobe CC: transition patterns, shared shell, identity continuity.
4. ADHD-friendly visual design 2025-2026 — свежие peer-reviewed research, не старые meta.
5. Shame-free language в AZ cultural context — native speaker sources.
6. Energy modes UX precedent — Linear compact, Roam low-power, Mercury minimal; как реализуют технически.
7. Pre-Assessment onboarding patterns — Calm, Duolingo, Headspace warm-up flows.
8. B2B talent search UX — LinkedIn Recruiter, Gem, SeekOut: что работает.

**Выход:** `docs/research/design-evidence/<topic>.md` × 8 + живой `evidence-ledger.md`.

### Phase 3 — Specification (Atlas, 3-4 дня)
**Зачем:** слить Phase 1 + Phase 2 в один документ, по которому Cowork рисует.
**Что:**
- Ecosystem map (5 продуктов связаны)
- Energy modes matrix (18 экранов × 5 продуктов × 3 режима)
- Pre-Assessment Layer spec
- B2B search flow spec
- Variable font choice + evidence
- Scroll animation spec + evidence
- Component library v3 (что меняется, что остаётся)
- i18n AZ/EN специфика

**Gate:** CEO читает 15 минут, подписывает или возвращает. Без подписи Phase 4 не стартует.
**Выход:** `03-ECOSYSTEM-DESIGN-SPEC-v3.md`.

### Phase 4 — Figma design (Cowork, 5-7 дней)
**Зачем:** превратить spec в готовый Figma с variables, components, prototypes.
**Что:**
- Design tokens обновлены
- Components × Full/Mid/Low energy × 5 продуктов
- Prototypes со scroll-animations и cross-product transitions
- Figma MCP variables + code-connect mappings

**Выход:** Figma file URL + `04-FIGMA-HANDOFF-v3.md` для Claude Code.

### Phase 5 — Code implementation (Claude Code, 7-10 дней)
**Зачем:** spec + Figma → живой код.
**Что:**
- Tailwind tokens обновлены
- Variable fonts с fallback
- CSS `animation-timeline` + Framer Motion fallback для Safari
- Компоненты перестроены
- Cross-product shell
- i18n AZ/EN прогон
- E2E Playwright тесты обновлены

**Параллельно:** Atlas ревьюит каждый PR.
**Выход:** серия PR в main, shipped.

### Phase 6 — Verification + launch (Atlas + swarm, 2 дня)
**Зачем:** гейт перед "готово".
**Что:**
- Accessibility audit WCAG 2.1 AA
- Performance audit (Lighthouse, Core Web Vitals: LCP/CLS/INP)
- Cultural review AZ нативом
- Constitution compliance (5 laws)
- Visual regression Playwright + screenshots
- CEO проходит все 5 продуктов на телефоне

**Выход:** `06-SIGN-OFF.md` + tag `redesign-v3-shipped`.

---

## Gates (не пропускаются)

| Gate | После фазы | Кто подписывает | Что проверяет |
|------|-----------|-----------------|---------------|
| G1 | Phase 0 | Atlas | Baseline полный, скриншоты есть, устаревшее заархивировано |
| G2 | Phase 1+2 | Atlas | Gap inventory + evidence-ledger непустые, P0 найдены |
| G3 | Phase 3 | **CEO (15 мин read)** | Spec покрывает все дыры + все evidence-ссылки работают |
| G4 | Phase 4 | Cowork + Atlas | Figma = spec 1:1, нет отсебятины |
| G5 | Phase 5 | Atlas | Все PR merged, E2E green, accessibility 95+ Lighthouse |
| G6 | Phase 6 | **CEO** | Прошёл 5 продуктов на телефоне, нет "это плохо" |

---

## RACI

| Phase | Responsible | Accountable | Consulted | Informed |
|-------|-------------|-------------|-----------|----------|
| 0 Baseline | Atlas | Atlas | — | CEO |
| 1 Discovery swarm | Atlas + 8 agents | Atlas | Swarm peer council | CEO |
| 2 Evidence research | Perplexity | Perplexity | Atlas (brief) | CEO |
| 3 Specification | Atlas | Atlas | Cowork, Perplexity | CEO (gate) |
| 4 Figma | Cowork | Cowork | Atlas | CEO |
| 5 Code | Claude Code | Claude Code | Atlas (PR review) | CEO |
| 6 Verification | Atlas + swarm | Atlas | Native AZ speaker | CEO (gate) |

---

## Срок

3-4 недели при полной загрузке всех трёх исполнителей. Не неделя. Не 2 месяца.

## Бюджет

$0 на инструменты (все платформы уже оплачены). Только время.

## Break-glass условия (когда план пересматривается)

- CEO меняет приоритет (Mercury срочно / инвестор просит demo)
- Evidence Phase 2 противоречит CEO-требованиям → возвращаемся к CEO с данными
- Phase 1 swarm находит P0 блокер который должен быть закрыт раньше этого спринта
- Perplexity отказывается — переключаемся на Claude Code для research
