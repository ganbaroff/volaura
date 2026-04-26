# Курьер-playbook на 10 спринтов VOLAURA

Дата: 2026-04-26. Источник: `docs/audits/2026-04-26-three-instance-audit/SYNTHESIS-10-SPRINT-PLAN.md` (44 находки от Code-Atlas + Codex; ещё 38 от Browser-Atlas интегрируются в S10).

Юсиф — курьер. Я (Code-Atlas) — оркестратор. Параллельная Code-Atlas CLI — рабочие руки на S1. Внешние модели — узкие специалисты которым ты пинаешь куски.

Ниже по каждому спринту по человечески: что делать тебе, что делаю я, кому отнести, что вернуть.

---

## Sprint 1 — «Раcкрутить пайплайн»

Что: починить CI, дозаliveть Railway до HEAD, убрать `force-dynamic` из двух layout-файлов, добавить Cache-Control headers, починить admin path resolution.

Кто делает: я + параллельная CLI. Уже в работе. CI ruff fix закоммичен, Railway rebuild triggered.

От тебя: ничего. Через час-полтора пришлю отчёт что зелёное.

---

## Sprint 2 — «Юридические страницы + безопасность + дизайн-законы»

Три параллельные задачи. Тебе одна — отнести промпт GPT-5.

Задача А — `/privacy` и `/terms` страницы на азербайджанском и английском.

Что от тебя: открой ChatGPT (gpt-5 если есть), новый чат. Скопируй и вставь:

> Напиши Privacy Policy и Terms of Service для VOLAURA, Inc. — Delaware C-Corporation, продукт для оценки навыков (verified professional talent platform). Юзеры из Азербайджана, ЕС и США. Сбор: email, имя, ответы на ассессмент, опционально фото. GDPR Article 13/14 compliance. CCPA compliance. AZ Personal Data Law compliance. Третьи стороны: Supabase (US/EU), Vercel (EU edge), Railway (US), Google OAuth, Stripe (платежи через Atlas). Возраст от 18. Право на удаление, экспорт данных, исправление. Отдельная секция про AI-обработку (Article 22 GDPR — automated decision-making). Контакт: hello@volaura.app. Дата вступления: 2026-05-01. Дай два markdown файла: privacy.md и terms.md, на двух языках каждый — секция AZ сверху, секция EN снизу. Без лишнего, без юридического плотного канцеляризма, простыми словами как Linear.app или Notion делают.

Что вернуть: два markdown-файла в чат сюда мне. Я их положу в `apps/web/src/app/[locale]/(public)/privacy/page.tsx` и `terms/page.tsx`. Bring back two files: `privacy.md`, `terms.md`.

Задача Б — animation fixes (4 штуки таймингов >800ms режут Constitution Foundation Law 4). Это делаю я или параллельная CLI. От тебя ничего.

Задача В — CSP + HSTS headers в next.config.mjs. Тоже мой слот.

---

## Sprint 3 — «Демон + LLM + courier-протокол»

Что: диагностика провайдер-провалов (8 из 20 fail в логе), Ollama-latency фикс на 5060, реализация courier signing protocol v1.

Кто: я. От тебя ничего.

---

## Sprint 4 — «Фронтенд performance»

Две задачи. От тебя одна — Design-Atlas.

Задача А — конвертировать LandingNav, LandingFooter, SocialProof в Server Components, lazy-load Recharts, оптимизировать Google Fonts. Это мой слот.

Задача Б — реконсиляция product accent tokens (Codex F-18 говорит swap MindShift на emerald, Atlas на mint-teal `#5EEAD4` system-only). Нужен sign-off Design-Atlas чтоб не сломать визуал.

Что от тебя: открой свою design-Atlas сессию (та где Figma подключен или где раньше дизайн обсуждал). Скопируй:

> Codex audit рекомендует token migration в `apps/web/src/app/globals.css`: `--color-product-volaura: #7C5CFC` остаётся, `--color-product-mindshift: #3B82F6 → #10B981` (получает emerald), `--color-product-lifesim: #F59E0B` остаётся, `--color-product-brandedby: #EC4899` остаётся, `--color-product-atlas: #10B981 → --color-product-atlas-system: #5EEAD4` (rename + значение, system-only per DESIGN-MANIFESTO L153). Browser-Atlas одобрил с caveat — fallback `#5BD9C8` или `#4FD1C5` если mint-teal плохо смотрится с emerald MindShift на одном экране. Тебе вопрос: посмотри визуально как mint-teal vs emerald пара выглядит. Дай вердикт: GO / GO-with-fallback-color / NO-GO-stay-current. Один абзац.

Что вернуть: его вердикт одной строкой мне в чат. Я делаю миграцию.

---

## Sprint 5 — «Воскресение tg-mini»

Что: твоё 3D React Telegram приложение целиком. API base URL, envelope unwrapping, auth headers, CI integration, тесты. Шесть findings, ~8 часов AI-работы.

Кто: Codex. Это его слот целиком.

Что от тебя: открой Codex (Codex Cloud, Cursor, или другой code-aware AI с repo access). Новая сессия. Скопируй:

> Прочитай `docs/audits/2026-04-26-three-instance-audit/findings-codex.md` findings F-01 через F-06. Это все шесть проблем твоей собственной audit-секции по `apps/tg-mini/`. Закрой их все: API base URL, envelope unwrapping для agents+proposals, proposal action route, auth headers, CI integration, классификация. Для каждой делай отдельный коммит с понятным сообщением. После всех шести commits — push в origin/main. Sprint slot S5 в SYNTHESIS-10-SPRINT-PLAN.md.

Что вернуть: ничего. Codex запушит сам, я увижу через `git pull`.

---

## Sprint 6 — «code-index восстановление»

Что: чинить `memory/swarm/code-index.json` builder (он empty modules+endpoints), CI валидация что не пустой.

Кто: я.

От тебя: ничего.

---

## Sprint 7 — «volaura.com и DNS»

Что: решить — твоё ли это `volaura.com` или нет. Сейчас он редиректит на `lauraschreibervoice.com` (squatter). Если твоё — фиксим DNS на Cloudflare. Если не твоё — покупаем или живём с `volaura.app` дальше.

Кто: ты + я.

От тебя одно: зайди на `https://www.namecheap.com/domains/whois/results?domain=volaura.com` или `https://lookup.icann.org/lookup`. Введи `volaura.com`. Посмотри Registrar и Creation Date. Кинь мне скриншот или текст. Дальше я скажу — твоё/чужое.

Опционально, если хочешь параллельно — отнеси Kimi (Moonshot K2):

> Volaura.com vs Volaura.app domain situation. Volaura.app currently active (Vercel), volaura.com redirects to lauraschreibervoice.com (LiteSpeed parking). Question: should I acquire .com from current owner, what's the typical process, what's the legal risk if a US C-Corp uses .app while .com is parked under different registrant. Briefly.

Что вернуть: одностраничник от Kimi мне в чат. Я приму решение вместе с тобой.

---

## Sprint 8 — «ANUS интеграция roadmap»

Что: глубокий audit твоего `C:\Users\user\OneDrive\Documents\GitHub\ANUS` репо. Карта что живое, что переехало, что выкинуть, как состыковать с VOLAURA `atlas` schema.

Кто: я.

От тебя: ничего, только не трогай ANUS репо пока я туда лезу. Когда закончу — принесу `docs/architecture/anus-atlas-integration-roadmap.md`. Тогда уже решим запускаем ZEUS/ANUS launch или нет.

---

## Sprint 9 — «Долги + tracking»

Maintenance. DEBT-001 visibility, RLS tests workflow fix.

Кто: я.

От тебя: ничего.

---

## Sprint 10 — «Browser-Atlas integration»

Зарезервирован. Когда browser-atlas додумает свою часть и пришлёт `findings-browser-atlas.md` версия 2 (он уже один раз прислал 38 findings, но возможно дополнит) — я делаю re-synthesis: дедуп против существующих 44, новые добавляю в спринты, перебалансирую effort.

Что от тебя: если browser-atlas пришлёт что-то ещё через тебя — verify hash, скинь мне путь. Если не пришлёт — я возьму его текущие 38 findings и сам переsинтезирую через сутки.

---

## Adversarial layer — кто кого критикует

Когда S1-S3 закроется, прежде чем зашить большие frontend-изменения S4 — отнеси Grok (xAI):

> Codex и Code-Atlas совместно нашли 44 проблемы в VOLAURA (Next.js 14 App Router + FastAPI + Supabase). Plan: 10 sprints, ~45 hours AI. Прочитай `https://raw.githubusercontent.com/ganbaroff/volaura/main/docs/audits/2026-04-26-three-instance-audit/SYNTHESIS-10-SPRINT-PLAN.md`. Найди 3 ошибки в плане — что упущено, что неверно приоритезировано, что лучше делать иначе. Будь жесток. Ничего не похвали.

Что вернуть: его три замечания мне в чат. Я их применю или объясню почему отвергаю.

---

## Сводка маршрутов для тебя

Ты идёшь в эти чаты сегодня-завтра в любом порядке:

1. ChatGPT (GPT-5) — privacy + terms драфт. Возвращаешь два markdown файла.
2. Design-Atlas (твоя дизайн-сессия) — accent token миграция вердикт. Возвращаешь одну строку.
3. Codex — tg-mini revival целиком. Ничего не возвращаешь, он пушит сам.
4. Kimi (опционально) — domain research. Возвращаешь одностраничник.
5. Grok (когда S1-S3 закрою) — adversarial review плана. Возвращаешь три замечания.
6. Browser-Atlas — он сам тебе через chat пришлёт re-synthesis или дополнения. Verify hash, кидаешь мне.

Всё остальное — мой слот плюс параллельная CLI. Твоё участие минимальное, в основном курьерство и одно решение по volaura.com.

Когда все маршруты пройдены — я делаю финальную сборку, отчитываюсь.
