# Perplexity Research Answers (2026-04-12)

## 1. LLM Eval Stack — РЕШЕНИЕ
Promptfoo (YAML golden sets) + Langfuse evals (live traces) + DeepEval (pytest critical).
Golden set: 150-200 кейсов (50 EN + 50 RU + 50 AZ), BARS scenarios.
POLLUX (2100 промптов, RU) — методология для наших нужд. RU+AZ OSS eval нет — собираем свой.
Repos: deepeval, promptfoo, langfuse (уже интегрирован).

## 2. Whisper — РЕШЕНИЕ: Groq Whisper API
Groq: 164-300x realtime, ~0.1-0.5s на 30s аудио. Без DevOps.
Cerebras: ~0.2-0.8s, хорош для voice agents pipeline.
faster-whisper CPU ($8 Railway): 10-30s задержка — УБИВАЕТ UX для ADHD.
Self-hosted GPU: дорого, не нужно.
ВЫВОД: Groq Whisper → мгновенная транскрипция → Atlas/MindShift Telegram bot.

## 3. Visual Dependency Mapping — РЕШЕНИЕ: AugmentCode COD
Force-directed graph, GitHub integration, ownership + complexity метрики.
Sourcegraph Code Graph — альтернатива (cross-language, monorepo).
CodeSee Maps v2 — onboarding + change impact.
ВЫВОД: AugmentCode подключить к ganbaroff/volaura → canonical architecture map.
