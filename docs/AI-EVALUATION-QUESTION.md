# Вопрос для оценки ИИ-генераторов

> Отправь этот промпт каждому ИИ (v0, Genspark, Perplexity, Kimi 2.5, K2Think).
> Собери ответы, сравни по таблице внизу.

---

## Промпт (копируй целиком):

```
Мне нужно оценить твои реальные возможности для крупного проекта. Ответь честно по каждому пункту: что умеешь, что нет, что частично.

Проект: full-stack веб-платформа для верификации волонтёров.
Стек: Next.js 14 (App Router) + TypeScript strict + Tailwind CSS 4 + shadcn/ui + Framer Motion + Recharts + react-i18next | FastAPI (Python) + Supabase (PostgreSQL + Auth + RLS + pgvector) + Gemini 2.5 Flash API

Оцени себя по каждому пункту (шкала: ✅ могу полностью / ⚠️ частично / ❌ не могу):

ФРОНТЕНД:
1. Next.js 14 App Router с `app/[locale]/` — серверные и клиентские компоненты
2. Tailwind CSS 4 (новый формат: @import "tailwindcss", @theme {} блок, БЕЗ tailwind.config.js)
3. shadcn/ui компоненты с кастомизацией (cn(), variant props)
4. Framer Motion: spring-анимации, stagger, layout animations, AnimatePresence
5. Recharts: radar chart с 8 осями, кастомные tooltip, responsive
6. react-i18next: namespace-based переводы, серверная инициализация, языковое переключение
7. Zustand для глобального состояния + TanStack Query для серверного
8. React Hook Form + Zod валидация
9. PWA (service worker, offline кеширование, install prompt)
10. OG-image генерация через @vercel/og (Satori)

БЭКЕНД:
11. FastAPI с async/await, Depends() для DI
12. Supabase Python SDK (async): CRUD через SDK, НЕ через ORM
13. Pydantic v2 (ConfigDict, field_validator — НЕ v1 синтаксис)
14. Row Level Security (RLS) политики в SQL
15. pgvector: vector(768), cosine similarity через RPC функции
16. Gemini 2.5 Flash API (google-genai SDK) для оценки текстовых ответов
17. Алгоритм адаптивного тестирования (IRT/CAT или pseudo-adaptive)
18. JWT верификация, magic link auth, Google OAuth через Supabase Auth
19. Генерация OpenAPI спецификации → @hey-api/openapi-ts для типов
20. Email отправка через Resend API

АРХИТЕКТУРА:
21. Монорепозиторий (Turborepo + pnpm workspaces)
22. SQL миграции с RLS + триггеры + pg_cron
23. Realtime subscriptions (Supabase Realtime)
24. Edge Functions (Supabase или Vercel)
25. CI/CD: автодеплой на Vercel + Railway

ДИЗАЙН/UX:
26. Адаптивный дизайн (mobile-first, 5 breakpoints: 640/768/1024/1280/1536)
27. WCAG 2.1 AA: контраст, aria-labels, focus indicators, prefers-reduced-motion
28. Gamification UI: badge system, progress bars, confetti, score animations
29. Multi-step формы (assessment flow: 25-33 вопроса, 3 типа: BARS шкала, MCQ, открытый текст)
30. Dark/Light mode с oklch цветами

Дополнительно ответь:
- Какой максимальный объём кода ты можешь сгенерировать за один запрос? (строк / файлов)
- Можешь ли ты принять файлы как входные данные и генерировать на их основе?
- Поддерживаешь ли ты итеративную разработку (я даю фидбек, ты дорабатываешь)?
- Можешь ли ты сгенерировать полный проект с правильной файловой структурой?
```

---

## Таблица для сравнения ответов

Заполни после получения ответов от каждого ИИ:

| # | Навык | v0 | Genspark | Kimi 2.5 | K2Think | Perplexity |
|---|-------|----|----------|----------|---------|------------|
| 1 | Next.js 14 App Router | | | | | |
| 2 | Tailwind CSS 4 | | | | | |
| 3 | shadcn/ui | | | | | |
| 4 | Framer Motion | | | | | |
| 5 | Recharts radar | | | | | |
| 6 | react-i18next | | | | | |
| 7 | Zustand + TanStack Query | | | | | |
| 8 | RHF + Zod | | | | | |
| 9 | PWA | | | | | |
| 10 | OG Image gen | | | | | |
| 11 | FastAPI async | | | | | |
| 12 | Supabase SDK | | | | | |
| 13 | Pydantic v2 | | | | | |
| 14 | RLS policies | | | | | |
| 15 | pgvector | | | | | |
| 16 | Gemini API | | | | | |
| 17 | Adaptive testing algo | | | | | |
| 18 | Auth (magic link + OAuth) | | | | | |
| 19 | OpenAPI → TS types | | | | | |
| 20 | Resend email | | | | | |
| 21 | Turborepo monorepo | | | | | |
| 22 | SQL migrations + RLS | | | | | |
| 23 | Realtime subscriptions | | | | | |
| 24 | Edge Functions | | | | | |
| 25 | CI/CD | | | | | |
| 26 | Responsive design | | | | | |
| 27 | WCAG 2.1 AA | | | | | |
| 28 | Gamification UI | | | | | |
| 29 | Multi-step assessment | | | | | |
| 30 | Dark/Light oklch | | | | | |
| — | Max code per request | | | | | |
| — | File input support | | | | | |
| — | Iterative development | | | | | |
| — | Full project structure | | | | | |
| **TOTAL** | **Score (✅=1, ⚠️=0.5, ❌=0)** | | | | | |

## Как интерпретировать

- **25+ из 30**: Может взять на себя целый модуль (фронт или бэк)
- **18-24**: Может генерить отдельные страницы/компоненты, нужен контроль
- **12-17**: Только для отдельных компонентов или UI-элементов
- **<12**: Не подходит для этого проекта

## Рекомендация по распределению

После оценки распредели так:
- **Лучший по фронтенду (1-10)** → получает фронтенд-модули
- **Лучший по бэкенду (11-20)** → получает бэкенд-модули
- **Лучший по архитектуре (21-25)** → получает инфра/настройку
- **Если один ИИ лидирует везде** → он делает всё, остальные ревьюят
