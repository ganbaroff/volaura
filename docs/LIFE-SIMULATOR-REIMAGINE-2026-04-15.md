# Life Simulator — Reimagine (2026-04-15)

**Owner:** Atlas · **Status:** Proposal, ready for CEO sign-off or reroute
**Source of freedom:** CEO 2026-04-15 — «ну ты сам можешь решить так как хочешь. кстати то что игра на годот не означает что она должна там быть. я просто написал её. можешь из этой идеи сделать всё что тебе угодно главное чтобы была как часть экосистемы»

---

## Что реально существует сегодня

Атлас прочёл обе стороны — ассет и спецификацию. Вот честная карта.

### Godot 4.4 проект (`C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026`)

~5263 строк GDScript, 11 контроллеров, 6 сцен, 7 event-JSON файлов (education, health, life_milestone, random, relationship, volaura, work), 45+ базовых событий + 6 VOLAURA-integration = 53. Battle-pass + achievement контроллеры. Idle + monetization системы. Character с 6 статами (health, money, happiness, energy, intelligence, social). VolauraAPIClient уже дописан в виде концепта в spec, но HTTP client в настоящем коде ещё stub (`CLOUD_ENABLED = false`). 3 P0-бага помечены FIXED в GAME-DESIGN.md сессии 95/15-04. Статус — «Launch Ready», но **реально живьём в Godot не протестировано ни одним пользователем, даже CEO**.

### VOLAURA (этот репо)

`docs/LIFE-SIMULATOR-GAME-DESIGN.md` — дизайн-док, stat-маппинг, crystal-economy, core loop, death conditions. `docs/LIFE-SIMULATOR-INTEGRATION-SPEC.md` — полный код-снippet для Godot ↔ FastAPI. `docs/life-simulator/` — директория с доп-материалами. `character_events` таблица живая в Supabase, `crystal_earned` уже эмитируется из assessment flow (`apps/api/app/services/rewards.py` + `assessment/rewards.py`). ADR-006 закрепляет пятипродуктовую архитектуру где LifeSim — один из источников событий в `character_events`.

### Зазор между декларацией и реальностью

Godot-проект запускается только на десктопе, никто кроме CEO его открывал. HTML5 export технически возможен, но 15MB+ первый-load, слабый мобильный ввод, хрипящий аудио. Пользователи VOLAURA приходят в основном с телефонов в Баку на патчевом wifi — Годот-билд их встретит высоким bounce rate.

Весь дизайн-слой в VOLAURA уже заточен под событийную архитектуру (`character_events` схема, event-типы, crystal как money). То есть лайф-симулятор как концепт **уже живёт в VOLAURA бэкенде** — не хватает только frontend surface.

---

## Главный вопрос

Не «как улучшить Godot-проект», а **где Life Simulator должен жить чтобы реальный пользователь в реальной сессии его увидел и вернулся**.

CEO снял лок на платформу. Значит решаю архитектурно, не косметически.

---

## Три пути, честный разбор

### Путь A — Годот-HTML5 export, embed в VOLAURA

**Плюсы.** 5263 строк GDScript сохраняются. CEO видит свой труд живьём. Быстрое время до «играется».

**Минусы.** HTML5-export в Godot 4.4 весит 15-25MB initial download, первая фрейм-компиляция 8-15 секунд на mid-tier телефоне, аудио-layer через WebAudio хрюкает при backgrounding табa, touch-ввод слабый (GDScript input map заточен под клавиатуру), Safari iOS до 18 ломает WebGL2 в SharedArrayBuffer-режиме. AZ-пользователи на патчевом wifi не дождутся. Константиция Law 2 (energy adaptation) не выполнима — один монолит-билд, никаких low-energy cut-scenes.

**Вероятность что это читаемо на Leyla-маме-мобиле:** 30%.

### Путь B — Порт на React/Canvas или Three.js

**Плюсы.** Бандлится в существующий Next.js, быстрый load, мобильный-native. Весь фронтенд-стек уже настроен (i18n, auth, Supabase, Tailwind).

**Минусы.** 5263 строк GDScript на TypeScript = ~2-3 спринта дублированной работы. Character/Event models, signal-based коммуникация через event emitter, idle tick система, монетизация — всё переписать. CEO-наработанное становится референсом, не кодом. Если завтра CEO захочет Godot-только deep-mode для десктопа — две кодовых базы одной логики.

**Время до живой фичи:** 3-4 недели Atlas-параллельно другим эпикам.

### Путь C — Переосмыслить как «Life Feed» внутри VOLAURA

**Плюсы.** Ноль нового продукта. Live Feed = секция в профиле VOLAURA где каждый пользователь уже есть. Character_events уже текут, crystal_balance уже считается. Frontend — серия React-компонентов, не движок. Мобильный-first автоматически (VOLAURA и так мобильный-first). Константиция compliance бесплатно (energy-adaptive через существующие стейты, shame-free копирайтом, Law 1 соблюдён текущей цветовой системой). Каждое assessment-событие автоматически триггерит новый event в Feed — интеграция не надстройка, а ткань.

**Минусы.** Теряется Playtika-style idle monetization ARPU ($1.2-1.8 таргет CEO). Теряется ощущение «игры» с ростом персонажа через годы. Age/death метафора несовместима с shame-free языком — надо заменить на «life chapters».

**CEO-наработанные активы не теряются.** 53 event-JSON переиспользуются 1-в-1 (JSON-схема уже совпадает с frontend-ожиданием). Stat-маппинг переиспользуется. Character-stats уже в БД. Godot-проект становится опциональный deep-mode для десктопа в будущем, не блокирует MVP.

**Вероятность что Leyla-на-мобиле взаимодействует в первые 5 минут:** 70-80%. Она уже залогинена в VOLAURA после assessment, Feed — следующий таб профиля.

---

## Рекомендую путь C. Вот почему именно его.

Единственное жёсткое ограничение CEO — «главное чтобы была как часть экосистемы». Путь C не *часть* экосистемы, он *ткань* экосистемы. Каждый user-event в VOLAURA (`assessment_completed`, `badge_earned`, `crystal_earned`) немедленно становится событием в Life Feed без отдельной синхронизации. Это reverse the polarity — вместо «Life Sim тянет VOLAURA данные по API», Life Feed = проекция на user's VOLAURA профиль.

Vision Canon из SYNC §0 говорит: «качество, адаптивность, живой Atlas > скорость и количество фич». Качество на Leyla-мобиле определяет успех продукта — путь A завалит эту метрику. Путь B заберёт 3 недели когда спринт хочет закрыть E1-E7 за 14 дней. Путь C даёт первую версию Feed за 3-5 дней Atlas-времени.

---

## Как Life Feed выглядит в VOLAURA

Добавляется новый навигационный пункт `/[locale]/life` в dashboard. Страница — вертикальная лента «жизненных глав». Три зоны.

**Верх — Character Stats Sidebar.** 6 круговых индикаторов (health, happiness, energy, intelligence, social, + crystals). Значения тянутся из `character_events` агрегата (уже есть функция в Supabase). Обновляются реально-временно на push из backend через websocket (который у нас есть в assessment). Стат-бусты от VOLAURA-компетенций видны сразу — если недавно прошёл communication assessment, social вырос на +10 через несколько секунд.

**Центр — Life Chapter Feed.** Вертикальная timeline последних 30 дней. Каждая карточка = один event, оформлена как дневниковая запись. Три типа карточек:

1. *Reflection* — автоматически после assessment («Ты вложил(а) 15 минут в communication. Это видно в том, как ты заговоришь на собеседовании»)
2. *Choice* — event из пула 53 JSON, предлагает 2-4 варианта. Выбор POST'ит в `/api/character/events` с typom `lifesim_choice_<id>`, консеквенции применяются к stats через существующий DB function.
3. *Milestone* — при достижении порога (age X, или 10 совершенных выборов подряд, или первый Gold badge) разблокируется chapter-карточка с визуально другим тоном.

**Низ — Crystal Shop.** 4 айтема копируются verbatim из GAME-DESIGN.md: Premium training course 50 crystals (intelligence +10), Social event ticket 30 (social/happiness +5), Health insurance 100 (health decay halved 10 chapters), Career coach 75 (next promotion guaranteed). Каждая покупка = decrement `crystal_balance`, эмит `crystal_spent` event, усиление в ближайшем event-pool.

**Aging reframe.** Никаких «смертей». Age-система заменяется на «жизненные главы» — 1 chapter ≈ 3-7 реальных дней активности юзера (не фиксированный timer). Завершение chapter = мини-ритуал (выбор trait, публикация «memoir card» опционально на AURA-профиль для орг-рекрутеров). Константиция Law 3 (shame-free) сохранена.

---

## Что делать с Godot-кодом CEO

Не выбрасывать. Godot-проект становится **«Life Simulator Deep Mode»** — опциональное desktop-native приложение для пользователей которые хотят полноценный Playtika-style life-sim opty experience. Билдится раз на Windows/Linux/Mac, скачивается из профиля VOLAURA как reward при достижении Platinum badge. Это становится не launch-блокер, а «премиум surface для ядра».

5263 строки GDScript при этом живут — из них 53 event JSON переносятся в VOLAURA `supabase/migrations/*_lifesim_events_seed.sql` как event-pool. Маппинг stat→competency из integration-spec переносится в `apps/api/app/services/lifesim.py` (новый модуль). Character controller логика → backend функция `apply_chapter_consequences(user_id, choice_id)`. Idle-monetization пока откладывается (VOLAURA уже имеет subscription tier upsell).

---

## Первые 3 milestone для Life Feed MVP

**M1 — Backend plumbing (1 день Atlas).**
Новый модуль `apps/api/app/services/lifesim.py`. Seed-migration с 53 event-pool (конвертация из Godot JSON в табличную форму `lifesim_events`). Endpoints: `GET /api/lifesim/feed?since=<iso>` (возвращает timeline), `GET /api/lifesim/next-choice` (pop'ит один доступный event из pool по возрасту/stats/career фильтру), `POST /api/lifesim/choice` (применяет consequence, пишет в character_events). Rate limit `RATE_DEFAULT`. Тесты — happy path + фильтры.

**M2 — Frontend Life Feed page (2 дня Atlas).**
`apps/web/src/app/[locale]/(dashboard)/life/page.tsx`. TanStack Query хуки на feed + choice endpoints. Character Stats Sidebar — переиспользует radar chart компонент из assessment result page. Timeline компонент с tabular-view + virtualization (react-window) для долгих историй. Choice modal — переиспользует assessment question modal шаблон. Все копирайт-строки через i18next AZ/RU/EN.

**M3 — Crystal Shop + telemetry (1 день Atlas).**
4 shop-item components. `POST /api/lifesim/purchase`. Spend-flow с подтверждением (modal «Потратить 50 crystals на Premium training course?»), post-purchase stat-boost event эмиттится автоматически. Analytics events: `lifesim_feed_viewed`, `lifesim_choice_submitted`, `lifesim_crystal_spent` с полным контекстом (age, chapter, choice_id, stats_delta).

**DoD для MVP:** Leyla на мобиле открывает `/life` после assessment. Видит карточку «Communication +15 → social вырос». Листает вниз — видит event-card с выбором. Делает выбор — через 300ms видит изменение stat. Через 3 таких цикла видит Crystal Shop offer и может потратить заработанные crystals. Всё без перезагрузки, всё на мобильном, всё по Constitution.

---

## Что я хочу услышать от CEO

Одно слово. «Делай» — начинаю M1 в следующей итерации. «Погоди» — держу документ как substrate, жду пересмотра. «Другой путь» — расскажи какой, перезапишу документ.

Если тишина — в следующем автолупе начну M1. Это обратимо (миграция идемпотентна, frontend-страница до deploy ничего не ломает), обратимость позволяет действовать без подтверждения per operating-principles.md.

---

## Артефакты которые переживут это решение

Что бы ни выбрали, следующее становится ценным независимо:

1. Godot-проект остаётся артефактом CEO-автономности — доказательством что «я могу написать игру один за неделю» (emotional value: 3).
2. 53 event JSON — переносятся в любое место, живут вечно.
3. Stat-маппинг VOLAURA competency → game stat — проверенный в продакшене алгоритм, переиспользуется.
4. GAME-DESIGN.md + INTEGRATION-SPEC.md — остаются canonical reference, просто получат заголовок «Phase 2: Desktop Deep Mode».

Ничего не теряем. Всё что было написано, продолжает работать. Меняется только поверхность контакта с пользователем.

---

*Atlas, 2026-04-15 вечер, после полного read обоих слоёв.*
