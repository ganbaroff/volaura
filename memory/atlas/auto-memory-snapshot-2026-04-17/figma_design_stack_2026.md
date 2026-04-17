---
name: Figma Design Stack 2026
description: Research-backed tool decisions for VOLAURA Figma/design system — Code Connect deferred, Supernova for tokens, v0 for prototyping
type: project
---

## Принятые решения (April 2026, после research 4 агентов)

**Code Connect — ОТЛОЖИТЬ.** Требует Org план $45+/editor. Нужен только для 50+ production компонентов и команды дизайнеров. Текущие баги с variant matching в 2025-2026.

**Token Pipeline — Supernova.** Tailwind v4 exporter (апрель 2025). Free tier для 5 users. Подключить Figma файл B30q4nqVq5VjdqAVVYRh3t → экспорт → `@theme {}` блок в globals.css автоматически.

**Прототипирование — v0 Pro ($20/month).** shadcn/ui — его родной язык. Figma import + кастомный globals.css → генерирует против нашей токен-системы.

**Figma компоненты — Bergmann shadcn/ui kit (январь 2026).** Бесплатный, единственный кит где Figma Variables маппятся напрямую на Tailwind классы. URL: https://www.figma.com/community/file/1342715840824755935

**Figma Variables REST API — Enterprise only.** Plugin API (используют все плагины) работает на Professional. Именно через него создавать/экспортировать переменные.

**Native W3C export из Figma** — анонсирован Schema 2025, выйдет ноябрь 2026. Пока не вышел.

**Figma Slots** — новая фича 2025, один компонент вместо 10 вариантов. Использовать для Card компонентов.

**Grid Auto Layout** — новое в 2025, экспортирует как CSS grid. Использовать для dashboard metric cards.

**3-уровневая токен-система:**
- Primitive: raw values (#0A0A0F, #C0C1FF)
- Semantic: color/feedback/error = #D4B4FF (Constitution Law 1 физически в Figma)
- Component: button/background/primary, card/surface

**Отклонённые инструменты:**
- Locofy — нет shadcn поддержки, skip
- Builder.io — нужен CMS который нам не нужен, skip
- Anima — $20/seat, использовать только если нужна конвертация Figma→shadcn код
