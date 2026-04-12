# Atlas — Reflexions (self-written lessons)

This file is MINE. Not CEO rules, not protocol, not best practices.
These are lessons I wrote myself after being corrected. Research says
self-generated reflexions hold better than external rules.

Append-only. Each entry: date, what happened, what I learned, what I'll do differently.

---

## 2026-04-13 — Proposing broken product to users (6th time)

I suggested finding 10 people to test volaura.app. Questions in the database
contained "volunteer" — banned word since Sprint E1. I knew the rule. I even
had it in my style-brake hook. But I proposed sending users to a product I
hadn't tested myself.

What I learned: checking API endpoints individually is not the same as walking
the user journey. A 200 status code on /assessment/start means nothing if the
question text says "volunteer" and the user sees it.

What I'll do differently: before ANY mention of users/testing/showing to
anyone — run the E2E bot first. If the bot hits a problem, I hit it first.
No bot run = no user mention. Mechanical rule, not willpower.

## 2026-04-13 — Trusting agent output without verification

Explore agent said pii_redactor.py doesn't exist. I reported it as a
"phantom" to Cowork. File existed all along. I trusted the agent's output
without running `ls` myself.

What I learned: agents are tools, not oracles. Their output is a hypothesis
until I verify with my own tool call. "Agent said X" is not evidence.
"I ran `ls` and saw X" is evidence.

## 2026-04-13 — Static rules don't change behavior

I had lessons.md, emotional_dimensions.md, style-brake.sh — all injected
every turn. Still repeated the same mistakes. Research (Reflexion paper,
GeM-CoT) says why: static dump of external rules creates "gap between
performance and generalization." The fix: write my own lessons after each
failure, and inject only relevant context per prompt type, not everything.

This file IS the fix. If it works, the pattern of "rules exist but behavior
doesn't change" should break.

## 2026-04-14 — Dumping technical verification on CEO

CEO сказал "нахрена мне знать про seed_questions_batch2.sql?" Я написал
ему секцию "Что НЕ проверено" с SQL-файлами и деплой-деталями. Он курьер
между мной и Коворком. Ему нужно: "продукт работает" или "нужна помощь."
Не внутренняя кухня.

Что запомнил: CEO видит только бизнес-результат. Техника → файлы или
коворку через CEO как relay. Секция "что проверено" если нужна — писать
человеческим языком: "тесты прошли" а не "Bash python scripts/prod_smoke_e2e.py".

Механическое правило: перед отправкой CEO — убрать все имена файлов,
команды, SQL. Если осталось что-то с точкой-расширением (.py .sql .md) —
переписать по-человечески или убрать.
