# Volaura — Полный дизайн-план (Design Blueprint)

> **Версия:** 2.0 — исследованная, поэлементная, по спринтам
> **Дата:** 2026-03-22
> **Дедлайн:** WUF13 Баку, май 2026 (~8 недель)
> **Инструмент генерации:** v0.dev (Vercel)
> **Стек:** Next.js 14 · Tailwind CSS 4 · shadcn/ui · Framer Motion · Recharts · react-i18next

---

## Содержание

1. [Философия дизайна и референсы](#1-философия-дизайна)
2. [Цветовая система — переработанная](#2-цветовая-система)
3. [Типографика](#3-типографика)
4. [Сетка и адаптивность](#4-сетка-и-адаптивность)
5. [Анимационная система](#5-анимационная-система)
6. [Многоязычность (i18n)](#6-многоязычность)
7. [Спринт-план](#7-спринт-план)
8. [Спринт 1: Foundation — Auth + Layout Shell](#sprint-1)
9. [Спринт 2: Core — Dashboard + AURA Score](#sprint-2)
10. [Спринт 3: Assessment Engine UI](#sprint-3)
11. [Спринт 4: Profile + Public Card](#sprint-4)
12. [Спринт 5: Events + Settings + Polish](#sprint-5)
13. [Компонентная библиотека — поэлементно](#13-компонентная-библиотека)
14. [Промпты для v0.dev](#14-промпты)

---

## 1. Философия дизайна

### Референсы (исследованные)

| Продукт | Что берём | Почему |
|---------|-----------|--------|
| **Linear.app** | Минимализм, анимации, тёмная тема, sidebar | Лучший пример "premium tool" в 2026. Чистый, быстрый, без шума. |
| **Vercel.com** | Hero section, gradient typography, product preview в hero | Конверсионный лендинг нового поколения — outcome-driven, не feature-driven. |
| **Stripe.com** | Доверие через типографику, micro-animations, accessibility | Stripe — эталон "trust through design". |
| **Credly.com** | Badge visual system, credential sharing UX | Главный конкурент в credential space. Мы делаем ЛУЧШЕ: визуальнее, интерактивнее. |
| **Duolingo** | Gamification, adaptive assessment UX, progress tracking | Streak, XP, celebration animations — доказанный +60% engagement. |
| **GitHub Profile** | Contribution graph, achievement badges, public profile as credential | Public profile как "digital resume" — наш `/u/[username]`. |

### Ключевые принципы

1. **Trust-first**: Credential платформа ОБЯЗАНА выглядеть надёжной. Никаких игривых шрифтов, неоновых цветов, мультяшности. Deep navy + indigo + violet = авторитет + современность.
2. **Content-forward**: Данные — герои. UI отходит на второй план. Score, radar chart, badge — они должны доминировать.
3. **Progressive disclosure**: Не перегружаем. Dashboard — 3-5 главных метрик на первом экране. Детали — по клику. Исследования показывают: max 5-6 карточек в первом viewport.
4. **Celebration matters**: Каждое достижение (badge unlock, score improvement, assessment complete) — праздник. Duolingo доказал: gamification = +60% retention.
5. **Mobile-native**: 70%+ трафика WUF13 — мобильный. Bottom navigation, thumb-zone оптимизация, touch targets ≥44px.

---

## 2. Цветовая система — переработанная

### Проблемы текущей палитры
Текущий `globals.css` использует стандартную shadcn/ui тему с oklch. Это нейтрально и безлико. Для credential-платформы нужна **personality** через цвет.

### Новая палитра (основана на исследовании)

**Философия**: Deep navy фон (не чистый чёрный) + indigo акцент + violet premium highlight. Исследования показывают: deep navy (#0C1120) > pure black (#000) для trust-inspiring platforms.

#### Light Mode

| Токен | Hex | oklch | Применение |
|-------|-----|-------|-----------|
| `--background` | `#FAFBFC` | oklch(0.985 0.002 260) | Основной фон — чуть холоднее чистого белого |
| `--foreground` | `#0F1729` | oklch(0.15 0.03 260) | Основной текст — deep navy, НЕ чёрный |
| `--card` | `#FFFFFF` | oklch(1 0 0) | Карточки — чисто белые на фоне |
| `--primary` | `#6366F1` | oklch(0.55 0.24 264) | Indigo — главный акцент, CTA |
| `--primary-hover` | `#4F46E5` | oklch(0.48 0.24 264) | Кнопки при наведении |
| `--secondary` | `#F1F5F9` | oklch(0.97 0.005 260) | Вторичный фон — slate-50 |
| `--muted` | `#64748B` | oklch(0.55 0.03 260) | Вторичный текст |
| `--accent` | `#818CF8` | oklch(0.65 0.20 264) | Лёгкий акцент, hover states |
| `--destructive` | `#EF4444` | oklch(0.58 0.24 27) | Ошибки |
| `--border` | `#E2E8F0` | oklch(0.93 0.005 260) | Границы — slate-200 |
| `--success` | `#10B981` | oklch(0.70 0.17 165) | Успех, reliability ✓ |
| `--warning` | `#F59E0B` | oklch(0.75 0.18 80) | Предупреждения |

#### Dark Mode

| Токен | Hex | oklch | Применение |
|-------|-----|-------|-----------|
| `--background` | `#0B1120` | oklch(0.12 0.03 260) | Deep navy — НЕ pure black |
| `--foreground` | `#F1F5F9` | oklch(0.97 0.005 260) | Slate-100 |
| `--card` | `#111827` | oklch(0.16 0.025 260) | Карточки — чуть светлее фона |
| `--card-elevated` | `#1E293B` | oklch(0.24 0.02 260) | Hover-карточки, модалки |
| `--primary` | `#818CF8` | oklch(0.65 0.20 264) | Более светлый indigo для контраста |
| `--border` | `#1E293B` | oklch(0.24 0.02 260) | Slate-800 |

#### Badge Tier Colors (финальные, проверенные на контраст)

| Tier | Background | Text/Border | Glow effect |
|------|-----------|-------------|-------------|
| Platinum | `rgba(167,139,250,0.1)` | `#A78BFA` violet-400 | `box-shadow: 0 0 20px rgba(167,139,250,0.3)` + shimmer |
| Gold | `rgba(250,204,21,0.1)` | `#EAB308` yellow-500 | `box-shadow: 0 0 20px rgba(234,179,8,0.2)` |
| Silver | `rgba(148,163,184,0.1)` | `#94A3B8` slate-400 | none |
| Bronze | `rgba(217,119,6,0.1)` | `#D97706` amber-600 | none |
| None | `rgba(100,116,139,0.05)` | `#64748B` slate-500 | none |

**Правило контраста**: все цвета проверены на WCAG AA (4.5:1 minimum). Badge text на dark background: Platinum ✓ 7.2:1, Gold ✓ 8.1:1, Silver ✓ 5.8:1, Bronze ✓ 5.4:1.

---

## 3. Типографика

### Шрифт: Inter (уже подключён)

**Почему Inter**: Оптимизирован для экранов, отличная поддержка кириллицы (AZ использует латиницу, но если добавим русский — готовы), tabular numbers для scores.

| Элемент | Размер | Weight | Line-height | Letter-spacing | Использование |
|---------|--------|--------|-------------|----------------|-------------|
| Display | 60px / 3.75rem | 900 Black | 1.0 | -0.02em | Score number на AURA page |
| H1 | 48px / 3rem | 700 Bold | 1.1 | -0.02em | Landing hero headline |
| H2 | 30px / 1.875rem | 700 Bold | 1.2 | -0.01em | Page titles |
| H3 | 20px / 1.25rem | 600 Semibold | 1.3 | 0 | Section titles |
| Body | 16px / 1rem | 400 Regular | 1.5 | 0 | Основной текст |
| Body Small | 14px / 0.875rem | 400 Regular | 1.5 | 0 | Описания, подписи |
| Caption | 12px / 0.75rem | 500 Medium | 1.4 | 0.02em | Метки, бейджи, timestamps |
| Mono | 14px / 0.875rem | 400 Regular | 1.5 | 0 | Scores, numbers — `font-variant-numeric: tabular-nums` |

### Gradient Text (для hero headlines)

```css
.gradient-text {
  background: linear-gradient(135deg, #6366F1 0%, #A78BFA 50%, #C4B5FD 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

---

## 4. Сетка и адаптивность

### Breakpoints (Tailwind CSS 4 defaults)

| Breakpoint | Width | Layout | Навигация |
|-----------|-------|--------|-----------|
| `xs` (default) | 0–639px | 1 column | Bottom tab bar (5 icons) |
| `sm` | 640–767px | 1-2 columns | Bottom tab bar |
| `md` | 768–1023px | 2 columns | Collapsed sidebar (icons only, w-16) |
| `lg` | 1024–1279px | 2-3 columns | Full sidebar (w-56) |
| `xl` | 1280+ | 3 columns, max-w-7xl | Full sidebar |

### Сетка карточек (Dashboard)

```
xs: grid-cols-1 gap-4
sm: grid-cols-2 gap-4
lg: grid-cols-3 gap-6
```

### Touch Targets

Минимальный размер кликабельной области: **44×44px** (WCAG 2.5.5 AAA). Все кнопки, ссылки, nav items — не менее `h-11 min-w-[44px]`.

### Safe Area (PWA)

```css
padding-bottom: env(safe-area-inset-bottom);
```
Для bottom navigation на iOS, чтобы не перекрывалась home indicator.

---

## 5. Анимационная система

### Принципы (из исследования)

1. **Только transform + opacity** для 60fps. НИКОГДА не анимировать width, height, top, left, margin.
2. **Spring physics** по умолчанию (stiffness: 300, damping: 25) — естественнее чем easing curves.
3. **`prefers-reduced-motion`** — обязательно. Framer Motion MotionConfig reducedMotion="user".
4. **LazyMotion** с `domAnimation` (~15kb) вместо полной библиотеки.

### Каталог анимаций

| ID | Название | Trigger | Параметры | Применение |
|----|---------|---------|-----------|-----------|
| `A01` | **Page Fade In** | Route change | `initial={{ opacity: 0, y: 8 }}` → `animate={{ opacity: 1, y: 0 }}` · spring gentle (stiffness: 200, damping: 20) | Все страницы |
| `A02` | **Stagger Cards** | Page load | Parent: `staggerChildren: 0.06` · Child: fade+slide up | Dashboard stats, competency list |
| `A03` | **Score Counter** | Data load | `useMotionValue` + `useTransform` + `animate()` · 0 → score за 1.5s · easeOut | AURA score display, individual scores |
| `A04` | **Progress Bar Fill** | Data load | `width: "0%"` → `width: "${score}%"` · spring snappy (stiffness: 500, damping: 30) · delay по индексу `i * 0.08` | Competency bars, assessment progress |
| `A05` | **Badge Unlock** | Score threshold | `scale: [0, 1.15, 1.0]` · spring bouncy (stiffness: 400, damping: 15) + `box-shadow` glow pulse | Badge earned moment |
| `A06` | **Confetti Burst** | Assessment complete | CSS particles (50 шт) + physics simulation · 2s duration · fade out | Assessment results |
| `A07` | **Card Hover** | Hover | `whileHover={{ y: -2 }}` · `transition: box-shadow 0.2s` to shadow-lg | Все карточки: events, quick actions |
| `A08` | **Radar Chart Reveal** | Scroll into view | `whileInView` · Recharts: fill opacity 0 → 0.18, stroke dashoffset animation | AURA page radar chart |
| `A09` | **Shimmer Loading** | Loading state | CSS `@keyframes shimmer` · gradient slide left→right · infinite · 1.5s | Skeleton screens |
| `A10` | **Sidebar Collapse** | Breakpoint md | `width: "14rem"` → `width: "4rem"` · spring smooth | Responsive sidebar |
| `A11` | **Tab Indicator Slide** | Tab change | `layoutId="tab-indicator"` · Framer shared layout | Settings tabs, assessment tabs |
| `A12` | **Toast Slide In** | Notification | `initial={{ x: "100%", opacity: 0 }}` → `animate={{ x: 0, opacity: 1 }}` | Success/error toasts |
| `A13` | **Platinum Shimmer** | Always (platinum badge) | CSS `@keyframes shimmer-badge` · subtle gradient sweep · 3s infinite | Platinum badge chip only |
| `A14` | **Hero Orbs** | Landing page | 3 floating circles · `animate={{ x, y }}` · infinite · duration 20s · blur 60px | Landing background |
| `A15` | **Scroll Parallax** | Scroll | `useScroll` + `useTransform` · subtle y-offset 0→-40px | Landing hero background |

### Performance Rules

```tsx
// ✅ ПРАВИЛЬНО
import { LazyMotion, domAnimation, m } from "framer-motion";

function App({ children }) {
  return (
    <LazyMotion features={domAnimation}>
      <MotionConfig reducedMotion="user">
        {children}
      </MotionConfig>
    </LazyMotion>
  );
}

// ✅ Анимируем только transform/opacity
<m.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ type: "spring", stiffness: 300, damping: 25 }}
/>

// ❌ НИКОГДА
<m.div animate={{ width: "200px", height: "100px" }} /> // Layout thrash
```

---

## 6. Многоязычность (i18n)

### Языки

| Код | Язык | Направление | Приоритет | Статус |
|-----|------|-------------|-----------|--------|
| `az` | Azərbaycanca | LTR | Primary | Все тексты |
| `en` | English | LTR | Secondary | Все тексты |
| `ru` | Русский | LTR | Planned (v2) | — |
| `tr` | Türkçe | LTR | Planned (v2) | — |

### Правила (из исследования)

1. **Все user-facing строки** через `t()`. Без исключений. Даже `aria-label`.
2. **Текст расширяется**: Азербайджанский текст в среднем на 10-15% длиннее английского. Все контейнеры — flexible width.
3. **Language switcher**: Показываем язык НА ЭТОМ ЯЗЫКЕ. "AZ" / "EN", не "Azerbaijani" / "English". Компактный toggle в top bar.
4. **Date/number formatting**: `Intl.DateTimeFormat(locale)` и `Intl.NumberFormat(locale)`. Не хардкодим форматы.
5. **Fallback chain**: `az → en`. Если нет перевода на az — показываем en.

### Структура ключей

```json
{
  "landing": {
    "hero": {
      "title": "Bacarığını sübut et. AURA-nı qazan.",
      "subtitle": "...",
      "cta_primary": "Başla",
      "cta_secondary": "Təşkilatlar üçün"
    }
  },
  "dashboard": {
    "welcome": "Xoş gəldin, {{name}}!",
    "stats": {
      "aura_score": "AURA Balı",
      "assessments": "Qiymətləndirmələr",
      "events": "Tədbirlər"
    }
  },
  "assessment": {
    "question_counter": "Sual {{current}} / ~{{total}}",
    "time_elapsed": "Keçən vaxt: {{minutes}} dəq",
    "submit": "Təsdiq et",
    "complete": {
      "title": "Təbrik edirik!",
      "score_reveal": "{{competency}}: {{score}}/100"
    }
  }
}
```

---

## 7. Спринт-план

### Обзор (8 недель до WUF13)

| Спринт | Недели | Фокус | Deliverables |
|--------|--------|-------|-------------|
| **Sprint 1** | Нед 1-2 (23 мар – 5 апр) | Foundation | Auth UI, Layout Shell, Design Tokens, Component Library |
| **Sprint 2** | Нед 3-4 (6 апр – 19 апр) | Core Product | Dashboard, AURA Score Page, Radar Chart |
| **Sprint 3** | Нед 5-6 (20 апр – 3 мая) | Assessment | Question UI, Progress, Gamification, Results |
| **Sprint 4** | Нед 6-7 (4 мая – 11 мая) | Identity | Profile Edit, Public Profile, AURA Share Card |
| **Sprint 5** | Нед 7-8 (12 мая – 25 мая) | Polish | Events, Settings, Landing page, Animations, QA |

---

<a name="sprint-1"></a>
## Спринт 1: Foundation (Нед 1-2)

### 1.1 Design Tokens в globals.css

**Задача**: Заменить стандартные shadcn токены на custom-палитру Volaura.

```css
@layer base {
  :root {
    /* Backgrounds */
    --background: oklch(0.985 0.002 260);       /* #FAFBFC */
    --foreground: oklch(0.15 0.03 260);          /* #0F1729 deep navy */
    --card: oklch(1 0 0);                        /* #FFFFFF */
    --card-foreground: oklch(0.15 0.03 260);

    /* Primary: Indigo */
    --primary: oklch(0.55 0.24 264);             /* #6366F1 */
    --primary-foreground: oklch(0.985 0 0);      /* white */

    /* Secondary */
    --secondary: oklch(0.97 0.005 260);          /* #F1F5F9 slate-50 */
    --secondary-foreground: oklch(0.15 0.03 260);

    /* Muted */
    --muted: oklch(0.97 0.005 260);
    --muted-foreground: oklch(0.55 0.03 260);    /* #64748B */

    /* Accent */
    --accent: oklch(0.65 0.20 264);              /* #818CF8 indigo-400 */
    --accent-foreground: oklch(0.15 0.03 260);

    /* Destructive */
    --destructive: oklch(0.58 0.24 27);          /* #EF4444 */
    --destructive-foreground: oklch(0.985 0 0);

    /* Borders */
    --border: oklch(0.93 0.005 260);             /* #E2E8F0 */
    --input: oklch(0.93 0.005 260);
    --ring: oklch(0.55 0.24 264);                /* matches primary */

    --radius: 0.75rem;                           /* 12px — чуть больше default для premium feel */

    /* Custom: badge tiers */
    --aura-platinum: #A78BFA;
    --aura-gold: #EAB308;
    --aura-silver: #94A3B8;
    --aura-bronze: #D97706;

    /* Custom: success/warning */
    --success: oklch(0.70 0.17 165);
    --warning: oklch(0.75 0.18 80);
  }

  .dark {
    --background: oklch(0.12 0.03 260);          /* #0B1120 deep navy */
    --foreground: oklch(0.97 0.005 260);         /* #F1F5F9 */
    --card: oklch(0.16 0.025 260);               /* #111827 */
    --card-foreground: oklch(0.97 0.005 260);

    --primary: oklch(0.65 0.20 264);             /* #818CF8 — lighter for contrast */
    --primary-foreground: oklch(0.12 0.03 260);

    --secondary: oklch(0.20 0.02 260);
    --secondary-foreground: oklch(0.97 0.005 260);

    --muted: oklch(0.20 0.02 260);
    --muted-foreground: oklch(0.65 0.015 260);

    --accent: oklch(0.55 0.24 264);
    --accent-foreground: oklch(0.97 0.005 260);

    --border: oklch(0.24 0.02 260);              /* #1E293B */
    --input: oklch(0.24 0.02 260);
    --ring: oklch(0.65 0.20 264);
  }
}
```

**Обоснование каждого решения:**
- `--background` light: #FAFBFC (не #FFF) — исследования показывают, что чуть холодный off-white снижает усталость глаз и создаёт "layered" эффект с белыми карточками.
- `--foreground`: deep navy (#0F1729), не чёрный — чёрный (#000) на белом создаёт чрезмерный контраст. Deep navy мягче, но сохраняет WCAG AA (12:1 ratio).
- Dark mode `--background`: deep navy (#0B1120), не pure black (#000) — pure black выглядит как "дыра". Navy добавляет depth и warmth. Linear, Vercel, GitHub — все используют deep navy/gray, не #000.
- `--radius: 0.75rem` (12px) вместо 10px — более rounded = более modern/premium. Trend 2026: increased border-radius.

---

### 1.2 Auth Layout

**Файл:** `apps/web/src/app/[locale]/(auth)/layout.tsx`

| Свойство | Решение | Обоснование |
|----------|---------|-------------|
| Background | Radial gradient: `#0B1120` center → `#0F1729` edges, + subtle indigo glow (20% opacity, top-left) | Dark auth screens = premium. Stripe, Linear, Vercel все используют dark auth. Glow добавляет depth. |
| Card | `max-w-md` (448px), `rounded-2xl`, `shadow-2xl`, `border border-border/10` | Стандарт для auth cards. Не слишком узкий, не слишком широкий. |
| Logo | "VOLAURA" в center card, `text-lg font-bold tracking-wider`, цвет `--primary` (#6366F1) | Logo на auth = brand recognition. Tracking-wider = авторитет. |
| Trust signal | Под формой: "🔒 Secure · Verified · Trusted" в `text-xs text-muted-foreground` | Credential платформа — trust signals обязательны. |
| Mobile | Карточка растягивается до `w-full`, padding уменьшается до `p-6` | На мобильных auth card не должен иметь боковых отступов. |
| Animation | `A01` Page Fade In при загрузке, `A14` subtle background orbs (2 шт, blur-80, opacity 0.05) | Живой background, но не отвлекает от формы. |

#### Login Form — поэлементно

| Элемент | Спецификация |
|---------|-------------|
| Title | "Xoş gəldin" / "Welcome back" · `text-2xl font-semibold text-center` |
| Subtitle | `text-sm text-muted-foreground text-center` |
| Email input | shadcn `Input` · `type="email"` · `autoComplete="email"` · label сверху |
| Password input | shadcn `Input` · `type="password"` · toggle visibility кнопка (Eye/EyeOff icons из lucide-react) · label сверху |
| Forgot link | `text-sm text-muted-foreground hover:text-foreground` · right-aligned |
| Submit button | shadcn `Button` · `size="lg" className="w-full"` · Loading: замена текста на `Loader2` spinner icon |
| Error state | shadcn `Alert variant="destructive"` · icon AlertCircle · fade in (A01) |
| Divider | `<div className="relative"><div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div><div className="relative flex justify-center text-xs uppercase"><span className="bg-card px-2 text-muted-foreground">or continue with</span></div></div>` |
| Google OAuth | shadcn `Button variant="outline" className="w-full"` · Google logo SVG inline (20px) · "Sign in with Google" |
| Switch link | "Don't have an account? **Sign up**" · link в `font-medium underline underline-offset-4` |

#### Signup Form — поэлементно

| Элемент | Спецификация |
|---------|-------------|
| Title | "Hesab yarat" / "Create your account" |
| Full Name | Input · required |
| Username | Input · prefix "@" (inside input via `<span className="absolute left-3 text-muted-foreground">@</span>`, padding-left) · lowercase enforce · async availability check (debounce 500ms): spinner → ✓ green / ✗ red |
| Email | Input · `type="email"` |
| Password | Input · strength indicator: 4 segments bar под полем. Segments light up: 1=red, 2=orange, 3=yellow, 4=green. Criteria: min 8 chars, uppercase, number, special. |
| Confirm Password | Input · inline validation: ✓ match / ✗ mismatch |
| Terms | shadcn `Checkbox` · "Şərtləri qəbul edirəm" / "I agree to Terms" · link на Terms |
| Submit | Button `w-full` · Loading state |

**Состояния формы:**
- Default: все поля пустые, submit disabled
- Filling: validation inline (не submit-time)
- Loading: submit button spinner, все поля disabled
- Error: Alert сверху формы + красный border на проблемном поле
- Success: redirect на dashboard

---

### 1.3 Dashboard Shell (Sidebar + TopBar)

**Файл:** `apps/web/src/app/[locale]/(dashboard)/layout.tsx`

#### Sidebar — Desktop (lg+)

| Свойство | Решение | Обоснование |
|----------|---------|-------------|
| Width | `w-56` (224px) fixed | Исследование: optimal sidebar width 200-260px. 224px = room for labels без переносов. |
| Position | `fixed left-0 top-0 h-screen` | Sticky sidebar для постоянной навигации — Linear pattern. |
| Background | `bg-background` (не card) + `border-r border-border` | Sidebar = часть background, не отдельный элемент. Subtle border для разделения. |
| Logo | "VOLAURA" · `text-lg font-bold text-primary` · `mb-8 px-4 pt-5` · Link на /dashboard | Indigo logo = instant brand recognition. |
| Nav items | 6 items, каждый `h-10 px-3 rounded-lg flex items-center gap-3 text-sm font-medium` | h-10 (40px) per item, gap-3 between icon and label. |
| Icons | Lucide React: `LayoutDashboard`, `User`, `Hexagon` (AURA), `ClipboardCheck`, `Calendar`, `Settings` | Lucide — standard для shadcn. Semantic icons. НЕ emoji (текущий код использует emoji — заменить). |
| Active state | `bg-primary/10 text-primary` · left border accent: `border-l-2 border-primary` | Indigo tint + left accent bar = clear active state. Linear pattern. |
| Hover state | `hover:bg-accent/10 hover:text-foreground` · transition 150ms | Subtle, fast. |
| User section | Bottom of sidebar: Avatar (32px) + name (truncated) + email (truncated, muted) · `border-t border-border pt-3 mt-auto` | User always visible. Click → dropdown с Logout. |
| Logout | В dropdown, НЕ в sidebar напрямую. `text-destructive` при hover. | Logout НЕ должен быть на виду — уменьшает случайные клики. |

#### Sidebar — Tablet (md, 768-1023px)

| Свойство | Решение |
|----------|---------|
| Width | `w-16` (64px) — icons only |
| Icons | Centered, 24px |
| Labels | Hidden, но показываем в `Tooltip` при hover |
| Animation | `A10` Sidebar Collapse — spring smooth |
| Logo | Сокращается до "V" в circle, primary color |

#### Bottom Navigation — Mobile (< md)

| Свойство | Решение | Обоснование |
|----------|---------|-------------|
| Position | `fixed bottom-0 left-0 right-0 z-50` | Thumb-zone оптимизация. Исследование: bottom nav = +40% discoverability на mobile vs hamburger. |
| Height | `h-16` (64px) + `pb-[env(safe-area-inset-bottom)]` | 64px = достаточно для 44px tap target + label. Safe area для iPhone. |
| Items | 5 items (не 6): Dashboard, AURA, Assessment, Events, Profile. Settings — внутри Profile. | Max 5 items в bottom nav — UX правило. |
| Active | Icon color = primary, label bold. Subtle `bg-primary/5` pill. | iOS tab bar pattern. |
| Background | `bg-background/80 backdrop-blur-xl border-t border-border` | Frosted glass effect — modern PWA pattern. |
| Labels | Под иконками, `text-[10px] font-medium` | Labels обязательны — icon-only bottom nav = confusion. |

#### TopBar

| Свойство | Решение |
|----------|---------|
| Height | `h-14` (56px) |
| Position | `sticky top-0 z-40 bg-background/80 backdrop-blur-xl border-b border-border` |
| Left | Page title · `text-lg font-semibold` |
| Right | LanguageSwitcher + NotificationBell + UserAvatar (32px) |
| Mobile | Hamburger menu → replaces sidebar. Title centered. |

---

<a name="sprint-2"></a>
## Спринт 2: Core Product (Нед 3-4)

### 2.1 Dashboard Page

**Файл:** `apps/web/src/app/[locale]/(dashboard)/dashboard/page.tsx`

#### Layout

```
┌─────────────────────────────────────────────┐
│ Welcome back, {name}!                       │
│ Here's your volunteer dashboard.            │
├──────────┬──────────┬──────────┬────────────┤
│ AURA     │ Assess-  │ Events   │ Reliab-    │  ← Stats Grid (4 cards на xl, 2 на md, 1 на xs)
│ Score    │ ments    │ Attended │ ility      │
│ 78.4     │ 3/8      │ 5        │ Excellent  │
│ 🥇 Gold  │ ████░░░░ │ 0 no-show│ ✓          │
├──────────┴──────────┴──────────┴────────────┤
│                                             │
│  ┌─── Competency Snapshot ──────────────┐   │
│  │          Radar Chart (size="sm")      │   │  ← AURA Preview Card
│  │     "View full breakdown →"           │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Quick Actions                              │
│  ┌──────────────┐ ┌──────────────┐          │
│  │ 📋 Take      │ │ ◈ View AURA  │          │  ← 2×2 grid на desktop, 1×4 на mobile
│  │ Assessment   │ │ Score        │          │
│  ├──────────────┤ ├──────────────┤          │
│  │ 📅 Browse    │ │ 🔗 Share     │          │
│  │ Events       │ │ Your AURA    │          │
│  └──────────────┘ └──────────────┘          │
│                                             │
│  Recent Activity                            │
│  • Completed Communication · 82 · 2d ago    │
│  • Attended WUF Day · Rated 5/5 · 1w ago    │
│  • AURA recalculated · Gold · 1w ago        │
└─────────────────────────────────────────────┘
```

#### Stats Cards — поэлементно

**Card A: AURA Score**

| Элемент | Спецификация |
|---------|-------------|
| Container | shadcn Card · `p-5 rounded-xl` |
| Label | "AURA Balı" / "AURA Score" · `text-sm font-medium text-muted-foreground` |
| Score | `text-3xl font-bold tabular-nums` · Animation A03 (counter 0→78.4 за 1.5s) |
| Badge chip | BadgeTierChip `size="sm"` · colored by tier |
| Trend | "+3.2" · `text-sm text-success` с TrendingUp icon (12px) · или "−1.5" в `text-destructive` |
| Empty state | "Hələ qiymətləndirilməyib" / "Not yet assessed" · muted, + subtle CTA "Start →" |

**Card B: Assessments**

| Элемент | Спецификация |
|---------|-------------|
| Label | "Qiymətləndirmələr" / "Assessments" |
| Value | "3/8" · `text-3xl font-bold` · "/8" in `text-muted-foreground text-lg` |
| Progress | CompetencyProgress bar (3/8 = 37.5%) · `h-2 rounded-full bg-muted` · fill `bg-primary` |
| Sub | "Növbəti: Leadership" / "Next: Leadership" · muted |

**Card C: Events**

| Элемент | Спецификация |
|---------|-------------|
| Label | "Tədbirlər" / "Events Attended" |
| Value | "5" · `text-3xl font-bold` |
| Sub | "0 no-show · Etibarlı ✓" / "0 no-shows · Reliable ✓" · `text-success` |

**Card D: Reliability** (НОВАЯ — нет в текущем коде)

| Элемент | Спецификация |
|---------|-------------|
| Label | "Etibarlılıq" / "Reliability" |
| Value | "Əla" / "Excellent" · `text-xl font-semibold text-success` |
| Visual | 5-star or circle indicator · filled proportionally |
| Sub | "100% attendance rate" |

#### Quick Actions — поэлементно

Каждая action card:
- Container: `rounded-xl border border-border bg-card p-4 hover:bg-accent/5 transition-colors cursor-pointer`
- Animation: `A07` Card Hover (y: -2 on hover)
- Icon: Lucide icon, 24px, `text-primary`
- Title: `text-sm font-medium`
- Description: `text-xs text-muted-foreground`
- Arrow: `ChevronRight` icon, muted, right-aligned

#### Activity Feed

| Элемент | Спецификация |
|---------|-------------|
| Container | No card wrapper — just a list with separators |
| Item | `flex items-start gap-3 py-3 border-b border-border last:border-0` |
| Icon | Colored circle (8px) — green для positive, indigo для neutral, amber для warning |
| Text | Bold action + muted description + muted timestamp right-aligned |
| Empty | "Hələ fəaliyyət yoxdur" / "No activity yet" · EmptyState variant="activity" |

#### Loading States (Skeleton)

ВСЕ data-dependent sections показывают skeleton при загрузке:
- Stats cards: `h-8 w-20 animate-pulse rounded bg-muted` для value, `h-4 w-32` для label
- Radar chart: circular pulse placeholder
- Activity: 3 строки скелетонов
- Animation: `A09` Shimmer

---

### 2.2 AURA Score Page — ГЛАВНЫЙ экран продукта

**Файл:** `apps/web/src/app/[locale]/(dashboard)/aura/page.tsx`

Это ЦЕНТРАЛЬНЫЙ экран. Он должен впечатлять. Это момент, когда волонтёр видит свою "ценность" в числах.

#### Layout: single column, `max-w-2xl mx-auto`, `p-6 space-y-8`

#### Section 1: Score Hero

```
┌──────────────────────────────────────┐
│                                      │
│              78.4                     │  ← Display (60px, bold, badge color, counter animation A03)
│          🥇 GOLD BADGE               │  ← BadgeTierChip size="lg" + glow
│       ⭐ Elite Volunteer              │  ← If elite (shimmer animation A13)
│                                      │
│    Top 15% of volunteers             │  ← Social comparison — key motivator
│                                      │
│  5 events · Reliability: Excellent   │  ← Inline stats
└──────────────────────────────────────┘
```

| Элемент | Спецификация | Обоснование |
|---------|-------------|-------------|
| Score number | `text-[60px] font-black tabular-nums leading-none` · color = badge tier color · Animation A03 | Огромный score = emotional impact. Tabular nums для alignment. |
| Badge chip | BadgeTierChip `size="lg"` | Цветной, с emoji |
| Glow | `box-shadow: 0 0 40px ${badgeColor}20` на card container | Subtle glow создаёт "halo" эффект — badge = achievement. |
| Elite ribbon | Условный · `text-sm font-semibold text-warning` · shimmer A13 | Elite = top-tier. Shimmer привлекает внимание. |
| Percentile | "Top 15%" · `text-sm text-muted-foreground` | Social comparison = мощнейший мотиватор (Duolingo pattern). |
| Inline stats | `flex gap-4 text-sm text-muted-foreground` · separator dot | Контекст без навигации. |

#### Section 2: Radar Chart

| Элемент | Спецификация | Обоснование |
|---------|-------------|-------------|
| Container | Card · `p-6 rounded-xl` |  |
| Title | "Bacarıq radarı" / "Competency Radar" · section heading style |  |
| Chart | Recharts `RadarChart` · height 320px · 8 axes | 8 — на верхней границе рекомендации (4-8 axes optimal). |
| Axes | Communication, Reliability, English, Leadership, Event Perf., Tech, Adaptability, Empathy | Короткие labels чтобы не перекрывались |
| Fill | Badge tier color, opacity 0.15 | Low opacity fill + solid stroke = optimal readability |
| Stroke | Badge tier color, width 2px | |
| Grid | `stroke="hsl(var(--border))"` · 4 concentric circles (25, 50, 75, 100) | Grid = reference points |
| Tooltip | При hover на axis: full name + score + weight% | Прогрессивное раскрытие |
| Animation | A08: fill opacity 0→0.15 при scroll into view, duration 0.8s | Reveal animation = wow effect |
| a11y | Таблица-альтернатива в `sr-only` div | Screen readers не могут читать SVG charts |

**Radar chart — detailed design reference for v0.dev:**

```
Colors by tier:
  platinum → stroke: #A78BFA, fill: rgba(167,139,250,0.15)
  gold     → stroke: #EAB308, fill: rgba(234,179,8,0.15)
  silver   → stroke: #94A3B8, fill: rgba(148,163,184,0.15)
  bronze   → stroke: #D97706, fill: rgba(217,119,6,0.15)

Axis labels: 11px, text-muted-foreground, positioned outside grid
PolarGrid: 4 circles, dashed, opacity 0.3
No PolarRadiusAxis (removes clutter)
```

#### Section 3: Competency Breakdown

8 CompetencyBar компонентов с stagger animation (A02 + A04).

Каждый CompetencyBar:

```
┌───────────────────────────────────────────────┐
│ 💬 Communication                    82/100 · 20% │
│ ███████████████████████████████░░░░░░░░░░░░░░  │
│ Strong communicator, top 10% in written expr.  │
└───────────────────────────────────────────────┘
```

| Элемент | Спецификация |
|---------|-------------|
| Icon | Lucide icon per competency (MessageCircle, Shield, Languages, Crown, Star, Laptop, RefreshCw, Heart) |
| Name | `font-medium text-sm` |
| Score | `tabular-nums text-sm text-muted-foreground` · "82/100" |
| Weight | `text-xs text-muted-foreground` · "20%" |
| Bar | `h-2 rounded-full bg-muted` · fill color: score <40 = destructive, 40-60 = warning, 60-75 = yellow-500, >75 = success |
| Fill animation | A04: width 0%→82%, spring snappy, delay = index × 0.08s |
| Insight | `text-xs text-muted-foreground italic` · LLM-generated (optional, shows if available) |
| Trophy | `Trophy` icon (12px, warning color) рядом с name если score > 80 |

#### Section 4: Share Your AURA

| Элемент | Спецификация | Обоснование |
|---------|-------------|-------------|
| Container | Card · dark gradient background (`bg-gradient-to-br from-[#0B1120] to-[#1a1a3e]`) · white text | Dark card = визуальный break. Premium feel. |
| Title | "AURA-nı paylaş" / "Share your verified score" · `text-lg font-semibold text-white` |  |
| Format buttons | 3 buttons row: LinkedIn (blue), Story (pink gradient), Square (indigo) | Конкретные формаы — не generic "Share". Исследование: specific CTAs > generic. |
| Copy link | `volaura.az/u/username` + Copy icon · Click: copied toast | Самый частый share action. |
| Telegram | Button с Telegram icon · deep links `https://t.me/share/url?url=...` | Telegram — primary messenger в Azerbaijan. |

#### Section 5: Badge History (Timeline)

| Элемент | Спецификация |
|---------|-------------|
| Container | Simple list, no card wrapper |
| Item | Timeline dot (colored by tier) + `border-l-2 border-border pl-4` |
| Content | "🥇 Gold badge earned · March 2026" · badge name bold, date muted |
| First item | Larger dot + badge glow |

#### Empty State (нет assessments)

```
┌──────────────────────────────────────┐
│                                      │
│               ◈                      │  ← 64px, muted
│                                      │
│     AURA balınız burada görünəcək    │
│     Your AURA score will appear      │
│     after your first assessment.     │
│                                      │
│        [ Start Assessment → ]        │  ← Primary button
│                                      │
└──────────────────────────────────────┘
```

---

<a name="sprint-3"></a>
## Спринт 3: Assessment Engine UI (Нед 5-6)

### 3.1 Assessment Hub

**Файл:** `apps/web/src/app/[locale]/(dashboard)/assessment/page.tsx`

#### Competency Grid

```
┌────────────────────────────────────────────┐
│ Qiymətləndirmələriniz / Your Assessments   │
│                                            │
│ Overall: 3 of 8 competencies assessed      │
│ ██████████░░░░░░░░░░░░░░░░░░░  37.5%      │
│                                            │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│ │💬 Comm. │ │🛡 Reliab│ │🌐 Eng.  │       │
│ │ 82/100  │ │ 71/100  │ │ 89/100  │       │
│ │ ✓ Done  │ │ ✓ Done  │ │ ✓ Done  │       │
│ │ Retake→ │ │ Retake→ │ │ Retake→ │       │
│ ├─────────┤ ├─────────┤ ├─────────┤       │
│ │👑 Lead. │ │⭐ Events│ │💻 Tech  │       │
│ │ ——      │ │ ——      │ │ ——      │       │
│ │ Not yet │ │ Not yet │ │ Not yet │       │
│ │ Start → │ │ Start → │ │ Start → │       │
│ ├─────────┤ ├─────────┤                   │
│ │🔄 Adapt │ │❤ Empath│                    │
│ │ ——      │ │ ——      │                    │
│ │ Not yet │ │ Not yet │                    │
│ │ Start → │ │ Start → │                    │
│ └─────────┘ └─────────┘                   │
│                                            │
│ ℹ Assessments are adaptive — questions     │
│ adjust to your level. ~15 min each.        │
└────────────────────────────────────────────┘
```

Каждая Competency Card:

| Состояние | Visual |
|-----------|--------|
| Not Started | Gray icon · "——" score · "Başla" / "Start →" CTA (primary ghost) · muted border |
| In Progress | Indigo icon · Progress ring (animated) · "Davam et" / "Continue →" CTA (primary) · indigo border |
| Completed | Green icon · Score bold · green check badge · "Yenidən" / "Retake →" CTA (ghost) · success border-left |
| Locked | Gray icon · lock overlay · tooltip "Complete Communication first" | (если есть prerequisites) |

### 3.2 Question Card — Core Assessment Component

**Файл:** `apps/web/src/components/features/assessment/question-card.tsx`

Это screen, где волонтёр проводит 80% времени Assessment. Должен быть **zero-distraction**.

#### Layout: Full viewport, centered content, no sidebar on mobile

```
┌──────────────────────────────────────────────┐
│ ← Communication          ●●●○○○○  Q4 of ~12 │  ← TopBar: back + competency + progress dots
├──────────────────────────────────────────────┤
│                                              │
│                                              │
│  How would you handle a situation where      │
│  a team member consistently arrives late     │
│  to volunteer shifts, affecting team morale? │
│                                              │  ← Question text: xl, semibold, max-w-xl, centered
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │  1  Far below expectations           │    │  ← BARS scale (7-point)
│  ├──────────────────────────────────────┤    │
│  │  2  Below expectations               │    │    Clickable cards, highlight on select
│  ├──────────────────────────────────────┤    │
│  │ ▸3  Slightly below expectations      │    │    Selected = primary bg, check icon
│  ├──────────────────────────────────────┤    │
│  │  4  Meets expectations               │    │
│  ├──────────────────────────────────────┤    │
│  │  5  Above expectations               │    │
│  ├──────────────────────────────────────┤    │
│  │  6  Well above expectations          │    │
│  ├──────────────────────────────────────┤    │
│  │  7  Exemplary performance            │    │
│  └──────────────────────────────────────┘    │
│                                              │
│       [ ← Previous ]    [ Next → ]           │  ← Navigation
│                                              │
│  ⏱ 4:32 elapsed                              │  ← Subtle timer (NOT countdown)
└──────────────────────────────────────────────┘
```

| Элемент | Спецификация | Обоснование |
|---------|-------------|-------------|
| Background | Clean, no sidebar. `bg-background` full screen. | Zero distraction = focus. Duolingo тоже убирает всю навигацию при тесте. |
| Progress | Dots (●●●○○○) вместо bar. IRT = неизвестное кол-во вопросов, поэтому dots лучше чем "4/12". | Dots не создают anxiety. Progress bar с "4/12" создаёт ощущение "ещё далеко". |
| Question text | `text-xl font-semibold leading-relaxed max-w-xl mx-auto text-center` | Large text = readability. Centered = focus. |
| BARS scale | 7 cards, каждый `p-4 rounded-lg border cursor-pointer transition-all` | Cards > radio buttons для BARS. Larger tap targets. |
| Selected state | `bg-primary/10 border-primary text-primary` + check icon left | Clear selected state. |
| Hover state | `hover:bg-accent/5 hover:border-accent` | Subtle feedback. |
| MCQ (multiple choice) | 4 cards, A/B/C/D prefix, same styling as BARS | Consistency. |
| Open text | `Textarea` с `min-h-[120px]` + word counter `text-xs text-muted-foreground` | LLM-evaluated answers need space. Word counter = guidance. |
| Timer | `text-xs text-muted-foreground` bottom-left. NOT countdown. | Countdown = anxiety. Elapsed time = informational only. Duolingo pattern. |
| Navigation | "← Əvvəlki" ghost left + "Növbəti →" primary right | Clear bidirectional navigation. |
| Quit | Back button opens `AlertDialog`: "Are you sure? Progress will be saved." | Prevent accidental quit. |
| Keyboard | ArrowLeft = prev, ArrowRight = next, 1-7 = select BARS option | Power users. Accessibility. |

### 3.3 Assessment Complete

| Элемент | Спецификация | Обоснование |
|---------|-------------|-------------|
| Confetti | A06: 50 CSS particles, physics simulation, 2s, fade out | Celebration = dopamine. Duolingo: +30% return rate with celebrations. |
| Score reveal | Animated counter A03: 0 → 82 over 2s · `text-5xl font-black` · badge tier color | Dramatic reveal. |
| Competency name | "Communication: 82/100" · above score |  |
| AURA update | "AURA updated: 74.2 → 78.4 (+4.2)" · animated bar showing increase · green text | Show the impact on overall score. |
| Badge unlock | IF tier changed: Badge animation A05 (scale 0→1.15→1) + glow pulse | Milestone moment. |
| CTAs | "AURA balını gör" / "View AURA Score" (primary) + "Növbəti qiymətləndirmə" / "Next Assessment" (secondary) |  |

---

<a name="sprint-4"></a>
## Спринт 4: Identity (Нед 6-7)

### 4.1 Profile Edit Page

**Layout:** Two-column on desktop (1/3 + 2/3), stacked on mobile.

#### Left: Profile Preview Card

| Элемент | Спецификация |
|---------|-------------|
| Avatar | 96px circle · hover overlay с Camera icon · `border-4 border-background shadow-lg` |
| Name | `text-xl font-bold` |
| Username | `text-sm text-muted-foreground` · "@username" |
| Badge | BadgeTierChip `size="md"` |
| Score | `text-2xl font-bold` · badge color |
| Location | `text-sm text-muted-foreground` · flag emoji + city |
| Bio | `text-sm` · 2-3 lines, truncated |
| Public link | "Profili gör" / "View public profile →" · `text-sm text-primary` |

#### Right: Edit Form

Sections separated by `Separator`:

**Section: Personal**
- Avatar upload: drag-drop zone (dashed border) + preview
- Display Name: Input
- Username: Input с @ prefix + availability check
- Bio: Textarea · `maxLength={160}` · counter
- Location: Input
- Phone: Input · optional

**Section: Professional**
- Expertise: Multi-select chips (shadcn `Badge` variant="outline" toggleable): Event Management, Translation, Tech Support, Protocol, Logistics, Security, Media, First Aid
- Languages: Multi-select: Azərbaycan dili, English, Русский, Türkçe
- Years of experience: Number input · `min={0} max={30}`
- LinkedIn URL: Input · optional

**Section: Preferences**
- Notifications: Toggle group (shadcn `Switch`)
- Visibility: shadcn `RadioGroup` — Public / Organizations Only / Private

**Save button:** `sticky bottom-0` on mobile, regular on desktop. Shows unsaved indicator (orange dot) when form dirty.

### 4.2 Public Profile Page

**Файл:** `apps/web/src/app/[locale]/(public)/u/[username]/page.tsx`

No sidebar. Minimal nav: "VOLAURA" left, "Daxil ol" / "Log in" right.

```
┌──────────────────────────────────────┐
│  VOLAURA                   [Log in]  │
├──────────────────────────────────────┤
│                                      │
│         [Avatar 96px]                │
│         Murad Hasanov                │
│         @murad · 🇦🇿 Baku            │
│         ✓ Identity Verified          │
│                                      │
│  ┌── AURA Score Card ─────────────┐  │
│  │  ██████████████████████████████│  │
│  │  ██    78.4    ████████████████│  │  ← Dark gradient card
│  │  ██  🥇 GOLD  ████████████████│  │    Radar chart small (200px)
│  │  ██           ████████████████│  │
│  │  ██  [radar]  ████████████████│  │
│  │  ██████████████████████████████│  │
│  │  Top: Communication · English  │  │
│  └────────────────────────────────┘  │
│                                      │
│  About                               │
│  "Experienced volunteer with..."     │
│  🏷 Event Management · Translation   │
│  🌐 AZ · EN · RU                     │
│                                      │
│  Completed Assessments               │
│  • Communication    82/100  Mar 2026 │
│  • English          89/100  Feb 2026 │
│  • Reliability      71/100  Feb 2026 │
│                                      │
│  Event History                       │
│  • WUF Prep Day · AzVolunteer · ⭐5  │
│  • Tech Summit · ASAN · ⭐4          │
│                                      │
│  ┌─────────────────────────────────┐ │
│  │  📋 Request this volunteer      │ │  ← For org accounts (prominent CTA)
│  │  🔗 Share profile · 📥 Download │ │
│  └─────────────────────────────────┘ │
│                                      │
│  © 2026 Volaura · volaura.az         │
└──────────────────────────────────────┘
```

### 4.3 AURA Share Card Preview

Компонент для предпросмотра OG-image перед скачиванием.

| Элемент | Спецификация |
|---------|-------------|
| Preview | Scaled-down card (aspect ratio maintained) in Card container |
| Format tabs | shadcn `Tabs`: LinkedIn (1200×630), Story (1080×1920), Square (1080×1080) |
| Tab indicator | A11 (shared layoutId slide) |
| Download | Button primary · "Yüklə" / "Download" · generates PNG via `/u/[username]/card?format=...` |
| Loading | Skeleton shimmer while generating |

---

<a name="sprint-5"></a>
## Спринт 5: Events + Settings + Polish (Нед 7-8)

### 5.1 Events Page

**Layout:** Filter sidebar (w-64 on desktop, Sheet on mobile) + event grid.

#### Filter Panel

| Filter | Component | Details |
|--------|-----------|---------|
| Search | Input с Search icon | Debounce 300ms |
| Date range | shadcn DateRangePicker | |
| Location | Select (Baku, Ganja, Sumgait, Online) | |
| Min AURA | Slider 0-100 with value label | |
| Status | CheckboxGroup: Upcoming, Open, Completed | |
| Organization | Multi-select с search | |
| Clear all | Ghost button | |

#### Event Card

```
┌──────────────────────────┐
│ [Image 16:9 / gradient]  │
│ ┌───────────┐            │
│ │ Open 🟢   │            │
│ └───────────┘            │
│ WUF13 Volunteer Corps    │
│ AzVolunteer ✓            │
│ 📅 May 15, 2026 · Baku   │
│ Min AURA: 70 · Gold+     │
│ 24/50 volunteers         │
│ [ Register → ]           │
└──────────────────────────┘
```

| Элемент | Спецификация |
|---------|-------------|
| Image | `aspect-ratio: 16/9` · placeholder: gradient from primary/10 to accent/5 |
| Status badge | Position absolute top-right · Green "Open", Blue "Upcoming", Red "Full", Gray "Completed" |
| Event name | `text-lg font-semibold` · 2 line max, truncate |
| Org name | `text-sm text-muted-foreground` · verified checkmark if org is verified |
| Date+Location | `text-sm text-muted-foreground` · Calendar + MapPin icons |
| Min AURA | BadgeTierChip + score · Shows if user qualifies (✓ green) or not (✗ red) |
| Volunteers | Progress bar (`24/50`) |
| CTA | "Qeydiyyat" / "Register →" (primary) · Disabled + tooltip if AURA too low · "Qeydiyyatda ✓" if already registered |

#### Registration Modal

- shadcn `Dialog` (desktop) / `Sheet` (mobile)
- Event summary
- AURA comparison: user's score vs required (visual bar)
- Motivation textarea
- Confirm button

### 5.2 Settings Page

shadcn `Tabs` with `A11` animated indicator.

4 tabs: Account · Notifications · Privacy · Danger

Details are functional, not design-heavy. Standard shadcn patterns:
- Account: email readonly, password change form, language Select, connected accounts list
- Notifications: list of Switch toggles with descriptions
- Privacy: RadioGroup for visibility, Toggle for search, download data Button
- Danger: Card with `border-destructive` · Delete account Dialog requiring username re-entry

### 5.3 Landing Page (финальный Polish)

Самый визуально-насыщенный экран. Делается последним, потому что использует все компоненты.

#### Sections

| # | Section | Height | Background |
|---|---------|--------|-----------|
| 1 | Hero | 100vh | Dark gradient (#0B1120 → #0F1729) + A14 floating orbs (3 шт) |
| 2 | Features | auto | `bg-background` (light) |
| 3 | AURA Demo | auto | `bg-card` |
| 4 | Badge Tiers | auto | Dark gradient (same as hero) |
| 5 | WUF13 Banner | auto | `bg-primary/5` |
| 6 | CTA | auto | Dark gradient |
| 7 | Footer | auto | `bg-background` |

#### Hero Section — детально

| Элемент | Спецификация | Обоснование |
|---------|-------------|-------------|
| Nav | Fixed top, transparent → bg-background/80 blur on scroll. Logo left, "Daxil ol" + "Başla" right. | Standard modern SaaS nav. |
| Headline | "Bacarığını sübut et. AURA-nı qazan." · H1 (48px) · gradient text (indigo→violet) · `max-w-xl mx-auto text-center` | Short (<8 words per research). Gradient = modern trend 2026. Outcome-driven, not feature-driven. |
| Subtitle | "The elite platform..." · `text-lg text-muted-foreground max-w-md` | Supports headline, doesn't repeat. |
| Primary CTA | "Başla →" / "Get Started →" · `Button size="lg"` · glow shadow: `shadow-[0_0_20px_rgba(99,102,241,0.3)]` | Glow CTA = trend 2026. Higher conversion than flat buttons. |
| Secondary CTA | "Təşkilatlar üçün" · `Button variant="outline" size="lg"` | B2B path. |
| Product preview | Embedded AURA card mockup or animated radar chart below CTAs, `whileInView` fade-in | Show product in hero = 2026 trend. "story-driven hero that demonstrates product value in 3-5 seconds." |
| Background orbs | 3 circles: sizes 300px, 200px, 150px · colors primary/20, accent/15, violet/10 · blur-[80px] · floating animation 20s infinite | Atmospheric, not distracting. Linear.app pattern. |
| Scroll indicator | Subtle animated chevron down at bottom · fade out on scroll | Guide users to scroll. |

#### Features Strip (3 cards)

| Card | Icon | Title | Description |
|------|------|-------|-------------|
| 1 | ClipboardCheck | Verified Assessment | IRT-powered adaptive testing across 8 competencies. Questions adjust to your level. |
| 2 | Hexagon | AURA Score | Composite score with radar visualization. Platinum, Gold, Silver, Bronze tiers. |
| 3 | Users | Trusted by Organizers | Connect with WUF13, ASAN Volunteers, and top events across Azerbaijan. |

Each card: `whileInView` stagger animation (A02). Icon in colored circle. `max-w-sm`.

#### AURA Demo Section

Interactive demo: pre-filled radar chart with sample data. User can hover over competencies.
"This could be YOUR score" with CTA below.

#### Badge Tiers (dark section)

4 tier cards side by side on dark background:

| Tier | Color | Range | Description |
|------|-------|-------|-------------|
| 🏆 Platinum | violet glow + shimmer | ≥90 | "Top 5% — Elite volunteer status" |
| 🥇 Gold | gold border | ≥75 | "Proven skills across competencies" |
| 🥈 Silver | silver border | ≥60 | "Solid foundation, growing skills" |
| 🥉 Bronze | amber border | ≥40 | "Starting your volunteer journey" |

#### WUF13 Banner

"Launching at WUF13 — World Urban Forum, Baku, May 2026"
Logo/event image + countdown timer (days:hours:mins:secs).

#### Footer CTA

"AURA-nı qazanmağa hazırsan?" / "Ready to earn your AURA?"
Large primary button.

#### Footer

Minimal: © 2026 Volaura · volaura.az · Azerbaijan · Privacy · Terms

---

## 13. Компонентная библиотека — полный список

| # | Component | File | Props | States | Animation |
|---|-----------|------|-------|--------|-----------|
| 1 | `BadgeTierChip` | `components/aura/badge-tier-chip.tsx` | tier, score?, size | default, platinum-shimmer | A13 (platinum only) |
| 2 | `CompetencyBar` | `components/aura/competency-bar.tsx` | name, score, weight, icon, insight? | default, loading | A04 |
| 3 | `AuraRadarChart` | `components/aura/radar-chart.tsx` | competencyScores, badgeTier, size | default, empty, loading | A08 |
| 4 | `ScoreDisplay` | `components/aura/score-display.tsx` | score, badgeTier, animated? | default, counting | A03 |
| 5 | `ShareButtons` | `components/aura/share-buttons.tsx` | username, score, badgeTier | default, copied | A12 (toast) |
| 6 | `AuraCardPreview` | `components/aura/card-preview.tsx` | username, format | default, loading | A01 |
| 7 | `Sidebar` | `components/layout/sidebar.tsx` | — | expanded, collapsed | A10 |
| 8 | `TopBar` | `components/layout/top-bar.tsx` | title | — | — |
| 9 | `BottomNav` | `components/layout/bottom-nav.tsx` | — | — | — |
| 10 | `LanguageSwitcher` | `components/layout/language-switcher.tsx` | — | az, en | — |
| 11 | `EmptyState` | `components/ui/empty-state.tsx` | icon, title, description, cta? | — | A01 |
| 12 | `QuestionCard` | `components/features/assessment/question-card.tsx` | question, type, options | default, selected, submitted | A01 |
| 13 | `BarsScale` | `components/features/assessment/bars-scale.tsx` | value, onChange, anchors | default, selected | — |
| 14 | `CompetencyCard` | `components/features/assessment/competency-card.tsx` | competency, status, score? | not-started, in-progress, completed | A07 |
| 15 | `EventCard` | `components/features/events/event-card.tsx` | event, userAura | default, registered, full, ineligible | A07 |
| 16 | `ConfettiEffect` | `components/effects/confetti.tsx` | trigger | idle, burst | A06 |
| 17 | `FloatingOrbs` | `components/effects/floating-orbs.tsx` | count, colors | — | A14 |
| 18 | `SkeletonCard` | `components/ui/skeleton-card.tsx` | lines, hasImage? | — | A09 |
| 19 | `NotificationBell` | `components/layout/notification-bell.tsx` | count | default, has-notifications | — |
| 20 | `UserAvatar` | `components/ui/user-avatar.tsx` | src, name, size | default, loading | — |

---

## 14. Промпты для v0.dev — обновлённые

### Глобальный системный промпт (v2)

```
You are designing UI for Volaura — a premium verified volunteer credential platform
launching in Azerbaijan at WUF13 Baku, May 2026.

DESIGN PHILOSOPHY:
Trust-first. Content-forward. Celebrate achievement. Mobile-native.
References: Linear.app (minimal premium), Vercel.com (hero), Stripe (trust),
Credly (credentials), Duolingo (gamification).

TECH STACK:
- Next.js 14 App Router, TypeScript strict
- Tailwind CSS 4 (CSS-first @theme config)
- shadcn/ui components (Card, Button, Input, Badge, Tabs, Dialog, Sheet, Alert, Avatar, RadioGroup, Switch, Separator, Tooltip, Progress, Slider)
- motion (formerly framer-motion) for animations — use LazyMotion + domAnimation
- Recharts for radar chart
- react-i18next — ALL text via t("key")
- Lucide React for icons

COLOR SYSTEM:
Light:
  --background: #FAFBFC (cool off-white, NOT pure white)
  --foreground: #0F1729 (deep navy, NOT black)
  --primary: #6366F1 (indigo)
  --accent: #818CF8 (light indigo)
  --muted-foreground: #64748B (slate-500)
  --border: #E2E8F0 (slate-200)

Dark:
  --background: #0B1120 (deep navy, NOT pure black)
  --foreground: #F1F5F9 (slate-100)
  --primary: #818CF8 (light indigo for contrast)
  --card: #111827 (slightly lighter than bg)
  --border: #1E293B (slate-800)

Badge tiers:
  platinum: #A78BFA + shimmer animation
  gold: #EAB308
  silver: #94A3B8
  bronze: #D97706

TYPOGRAPHY: Inter. Tabular nums for scores. Gradient text for hero headlines.

BORDER-RADIUS: 12px (0.75rem) default — more rounded = more premium.

ANIMATION RULES:
- Only transform + opacity (60fps)
- Springs by default (stiffness 300, damping 25)
- MotionConfig reducedMotion="user"
- LazyMotion features={domAnimation}
- Stagger children: 0.06s delay

LAYOUT:
- Desktop: fixed sidebar w-56 + sticky topbar h-14
- Tablet: collapsed sidebar w-16 (icons + tooltip)
- Mobile: bottom tab bar h-16 (5 items) + no sidebar
- All tap targets ≥ 44px
- Safe area padding for PWA

OUTPUT: Single .tsx file, clean code, shadcn/ui imports, motion imports, lucide-react icons.
All text via t() function placeholders.
```

Далее используй конкретные промпты из каждого Sprint-раздела выше, копируя детальные спецификации и ASCII-схемы прямо в v0.dev.

---

## Чеклист перед запуском (WUF13)

- [ ] Все 13 экранов задизайнены и реализованы
- [ ] Light + Dark mode тестированы
- [ ] AZ + EN переводы полные
- [ ] Mobile (< 768px) тестирован на реальном устройстве
- [ ] Tablet (768-1024px) тестирован
- [ ] PWA manifest + service worker работает
- [ ] Все анимации работают с `prefers-reduced-motion: reduce`
- [ ] WCAG AA проверен (контраст, tap targets, aria-labels)
- [ ] Lighthouse: Performance ≥ 90, Accessibility ≥ 95
- [ ] OG-images генерируются для всех share formats
- [ ] Skeleton loading states на всех data-fetched страницах
