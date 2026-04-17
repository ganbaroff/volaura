---
name: VidVow project context — crowdfunding platform
description: VidVow is Yusif's second project — crowdfunding with video promises. Built via Perplexity conversations. Separate from VOLAURA ecosystem. Has reusable payment code.
type: project
originSessionId: 15299306-4582-4c3f-b635-40127687fa18
---
# VidVow — Краудфандинговая Платформа

**Repo:** `C:\Users\user\Downloads\vidvow`
**Stack:** React 19 + Hono + Cloudflare Workers + D1
**Status:** Production-grade, orphaned (built, not deployed)

## Что это

VidVow = краудфандинг с video promises (авторы записывают видео-обещание что сделают при достижении цели).
Разработана в диалоге с Perplexity — большая история обсуждений: Destek Ol → TheStackable → AzFund → VidVow.

**Main slogan:** "Your Video Promise, Funded."
**Domain:** vidvow.com (был свободен на момент обсуждения)

## Funding models
- Reward-based (как Kickstarter)
- Donation-based (как GoFundMe)
- Flexible funding (как Indiegogo)
- Subscriptions (как Patreon) — планировалось

## Категории
Стартапы, личные мечты, творчество, социальное, малый бизнес, путешествия

## Платёжный код (РЕАЛЬНО РЕАЛИЗОВАН)

**Файл:** `src/worker/payment-providers.ts`

| Провайдер | Валюта | Статус |
|-----------|--------|--------|
| Stripe | USD | ✅ Реальная интеграция |
| Cryptomus | USDT | ✅ Реальная интеграция — `api.cryptomus.com/v1/payment` |
| GoldenPay | AZN | ⚠️ TODO stub — генерирует фейковый ID, API не вызывает |

**Cryptomus код портируем в VOLAURA** — реальный рабочий fetch + webhook + callback URL.

## Комиссионная модель (из кода)
- Free tier: 5% (`feePercentage = 0.05`)
- Premium tier: 3% (`feePercentage = 0.03`)

## Что можно взять в VOLAURA

1. **Cryptomus USDT интеграция** — копируй `createCryptomusPayment()` в FastAPI
2. **Fee calculation logic** — `calculatePlatformFee()` чистая утилита
3. **Escrow refund pattern** — для "all-or-nothing" механики
4. **GoldenPay** — нужно реализовать с нуля (VidVow = TODO)

## Связь с VOLAURA ecosystem

VidVow → ОТДЕЛЬНЫЙ продукт, не часть 5-продуктовой экосистемы.
Не подключён к Supabase dwdgzfusjsobnixgyzjk, нет crystal economy.

**Why:** Решает другую задачу — сбор денег. VOLAURA — верификация навыков.
Возможная интеграция: VOLAURA AURA score → VidVow trust score (будущее).

## Perplexity история

Длинная переписка где Юсиф разрабатывал VidVow через Perplexity:
- Destek Ol (социальный проект) → Destekol (краудфандинг AZ) → TheStackable (видео-фокус) → AzFund → VidVow
- Bubble.io был выбран для no-code MVP
- Mixboard для визуалов и презентации
- Продуктовые решения: reward/donation only (без equity), видео обязательно

**Why to apply:** Когда Юсиф упоминает VidVow, Destek Ol, AzFund, TheStackable, vidvow.com — это всё один проект.
Не путать с VOLAURA.
