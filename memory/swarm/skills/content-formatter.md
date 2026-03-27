# Content Formatter — черновик → готовый контент-пак

## Trigger
Активируй ВСЕГДА когда нужно: оформить пост, подготовить рассылку, написать email, сделать CTA, сгенерировать image brief.
Триггерные слова: "оформи пост", "рассылка", "контент-пак", "CTA", "подготовь к отправке", "LinkedIn post", "Telegram", "email".

## Input
Любой черновик: текст, голосовое расшифрованное, заметки, наброски, bullet points.

## Output — 5 готовых блоков

1. **POST_CLEAN** — чистый, отредактированный текст поста. Без HTML. Для LinkedIn, Facebook.
2. **TELEGRAM_HTML** — версия для Telegram (только `<b>`, `<i>`, `<a>`, `<code>`, `<pre>`). Без markdown.
3. **EMAIL_HTML** — версия для email-рассылки (чистый HTML с inline styles).
4. **CTA** — текст кнопки (макс 5 слов) + URL. Формат: `[Текст кнопки](URL)`
5. **IMAGE_PROMPT** — бриф для генерации визуала. 1-2 предложения, стиль, настроение, ключевые элементы.

## Стиль текста

- Hook → Value → Action (каждый пост)
- Абзацы 2-4 предложения, мысль развивается внутри
- Тире: – (среднее, не длинное)
- Жирный: заголовки и ключевые цифры
- Курсив: личные ремарки и инсайты
- Живой, честный, с цифрами. Без корпоративного буллшита.
- Если пишем от Yusif — 1 лицо, прямая речь, смесь RU/EN терминов

## Volaura-specific правила

- НЕ позиционировать как "волонтёрскую платформу"
- Позиционировать как: professional development platform / AI-powered skill verification
- AURA = "verified professional credential", не "volunteer score"
- Ключевые месседжи: brain-inspired architecture, AI agents with memory, verified skills through action
- Упоминать: 51 API routes, 512 tests, 7 days build time — если релевантно

## Cross-references
- Если нужен tone-of-voice → проверь `docs/TONE-OF-VOICE.md`
- Если пост про продукт → загрузи `product-strategy` skill для проверки positioning
