# Volaura Swarm — Model Roster v1.0
*Team directory: know your team members, their strengths, weaknesses, and how to work with them.*
*Updated: 2026-03-24 | Source: discovered_models.json + past evaluation results*

---

## How to Use This Document

Before launching any swarm task, check this roster:
- Which models are ACTIVE right now?
- Which ones are best for THIS domain?
- Which ones are blacklisted (don't waste API calls)?
- How do you prompt each one to get the best output?

This is NOT static. Update after every significant swarm run where model performance differs from expectations.

---

## Active Team Members

### gemini-2.5-pro — Gemini / Google
**Role in swarm:** Strategic synthesizer, deep reasoner
**Response time:** ~2760ms (slowest active model)
**Best at:** Complex multi-step reasoning, synthesis across many inputs, nuanced business analysis
**Weak at:** Fast responses (use others for latency-sensitive tasks), sometimes returns 0 confidence when overloaded
**How to prompt:** Give full context. This model benefits from longer prompts. Don't compress.
**Don't ask it to:** Be fast. Accept dropped responses (0 confidence) as "it's thinking" — if it consistently fails, check quota.
**Current status:** ACTIVE — but frequently returns 0-confidence results in high-concurrency runs. Use as synthesis model, not first-pass evaluator.

---

### gemini-2.0-flash — Gemini / Google
**Role in swarm:** Reliable generalist, volume agent
**Response time:** ~852ms
**Best at:** Business analysis, content evaluation, balanced reasoning. Consistent JSON. Good at seeing multiple sides of a decision.
**Weak at:** Deep technical code reasoning (prefers business/content domains). Can be too "balanced" — may not take a strong position.
**How to prompt:** Give specific scenarios. Works well with examples. Responds well to structured format requests.
**Don't ask it to:** Make final security judgments alone. It will list all risks equally weighted — needs a human or deeper model to prioritize.
**Current status:** ACTIVE — high performer, consistent 0.7-0.9 confidence, excellent JSON compliance.

---

### gemini-2.5-flash-lite — Gemini / Google
**Role in swarm:** Fast volume agent, content specialist
**Response time:** ~795ms
**Best at:** Content review, LinkedIn post analysis, UX copy feedback. Very fast with good quality.
**Weak at:** Highly technical architecture decisions. Sometimes misses edge cases that slower models catch.
**How to prompt:** Standard prompts work well. No special formatting needed. Keep prompts focused.
**Don't ask it to:** Make security architecture decisions without verification from deeper model.
**Current status:** ACTIVE — strong performer. Frequently used in parallel batches. Good signal-to-noise ratio.

---

### gemini-flash-lite-latest — Gemini / Google
**Role in swarm:** Speed champion, parallel evaluator
**Response time:** ~590ms (fastest Gemini)
**Best at:** Quick first-pass evaluations, high-volume parallel runs, catching obvious issues fast.
**Weak at:** Nuanced domain-specific analysis. Hive exam results: weak in architecture, general, business domains.
**How to prompt:** Short, focused prompts. This model degrades with prompt length. Use for yes/no, score/evaluate, or rank tasks.
**Don't ask it to:** Lead synthesis. Its speed makes it great for volume, but synthesis needs a slower model.
**Current status:** ACTIVE — high volume usage, but failed hive exam (weak: architecture, general, business). Watch for over-reliance.

---

### gemini-3.1-flash-lite-preview — Gemini / Google
**Role in swarm:** Preview model, tactical evaluator
**Response time:** ~1007ms
**Best at:** Pragmatic business decisions, risk assessment with clear priorities (doesn't hedge equally — takes positions).
**Weak at:** Still in preview — may have inconsistent behavior. Don't use for irreversible critical decisions.
**How to prompt:** Works well with structured paths. Good at "pick one and defend it" format.
**Don't ask it to:** Handle production-critical decisions until out of preview.
**Current status:** ACTIVE (PREVIEW) — shows good confidence levels (0.8) in business domain tasks.

---

### deepseek-chat — DeepSeek
**Role in swarm:** The contrarian. Hardest critic. Most specific concerns.
**Response time:** ~2204ms
**Best at:** Finding the specific failure in a plan. Where Gemini models list risks equally, DeepSeek identifies THE risk. In Post #2 simulation: "they will 100% recognize themselves in the critique." Most honest output.
**Weak at:** Speed. It's the slowest non-Gemini model. Don't use for latency-critical decisions.
**How to prompt:** Ask it to be critical. It responds to "find the flaw" much better than "evaluate this." Give it permission to be harsh.
**Don't ask it to:** Generate creative content (not its strength). Use it for red-teaming, not brainstorming.
**Current status:** ACTIVE — 1 paid model in the pool ($0.0001/run). Use intentionally. Best value: adversarial review of plans before execution.
**Cost note:** Only paid model currently active. Budget ~$0.0001 per run.

---

## Dead Weight (Do Not Use)

These models have been automatically removed from the active pool. Do not attempt to re-add without re-running discovery.

| Model | Provider | Reason | Last seen |
|-------|---------|--------|-----------|
| llama-3.1-8b-instant | Groq | 0/3 hive exams passed | 2026-03-24 |
| meta-llama/llama-4-scout-17b-16e-instruct | Groq | 0/3 hive exams passed | 2026-03-24 |
| allam-2-7b | Groq | Blacklisted: never produces valid JSON | 2026-03-24 |
| llama-3.3-70b-versatile | Groq | 0/3 hive exams passed | 2026-03-24 |
| openai/gpt-oss-120b | Groq | 0/3 hive exams passed | 2026-03-24 |
| groq/compound-mini | Groq | JSON compliance 17% (threshold: 50%) | 2026-03-24 |
| moonshotai/kimi-k2-instruct-0905 | Groq | Blacklisted: never produces valid JSON | 2026-03-24 |
| moonshotai/kimi-k2-instruct | Groq | Blacklisted: never produces valid JSON | 2026-03-24 |

**Note on Kimi:** Kimi was called "the contrarian" in earlier sessions. Real performance: consistently fails JSON schema. Until Moonshot fixes their Groq API integration, Kimi is not usable. DeepSeek has taken the contrarian role effectively.

---

## Delegation Guide by Domain

### For CONTENT / LINKEDIN / TOV tasks
**Lead:** gemini-2.5-flash-lite or gemini-2.0-flash
**Volume:** gemini-flash-lite-latest (parallel evaluation)
**Contrarian check:** deepseek-chat (ask: "what's wrong with this post?")
**Avoid:** gemini-3.1-flash-lite-preview (still preview, inconsistent for creative)

### For BUSINESS / STRATEGY / PRICING tasks
**Lead:** gemini-2.0-flash or gemini-2.5-pro (if time allows)
**Volume:** gemini-2.5-flash-lite, gemini-flash-lite-latest
**Contrarian check:** deepseek-chat
**Avoid:** gemini-flash-lite-latest as lead (weak in business domain per hive exam)

### For SECURITY / RISK ASSESSMENT tasks
**Lead:** deepseek-chat (most specific risk identification)
**Support:** gemini-2.5-pro (deep reasoning on implications)
**Volume:** gemini-2.0-flash
**Avoid:** gemini-flash-lite-latest (weak in security domain)

### For ARCHITECTURE / CODE REVIEW tasks
**Lead:** gemini-2.5-pro (slowest but deepest)
**Support:** deepseek-chat (finds specific code flaws)
**Avoid:** gemini-flash-lite-latest (failed architecture exam)

### For SPEED-CRITICAL / QUICK DECISIONS
**Lead:** gemini-flash-lite-latest + gemini-2.5-flash-lite in parallel
**Skip:** gemini-2.5-pro, deepseek-chat (too slow for <10s response budget)

---

## How to Update This Roster

After any swarm run where a model behaves unexpectedly:
1. Note the model name, domain, and what went wrong/right
2. Update the relevant section in this document
3. If a model consistently excels in a new domain → update "Best at"
4. If a model fails 2+ runs in a domain → add to "Weak at" or "Don't ask it to"
5. If a model's JSON compliance drops below 50% in 3 consecutive runs → move to Dead Weight table + blacklist in `engine.py`

The hive system (`agent_hive.py`) automatically tracks exam results. Cross-reference with this document after each weekly swarm run.

---

## Team Size by Task Stakes

| StakesLevel | Models called | Expected cost | Use when |
|-------------|--------------|---------------|---------|
| LOW | 3-5 | ~$0.00001 | Quick check, obvious decision |
| MEDIUM | 7-10 | ~$0.00005 | Standard decisions, content review |
| HIGH | 10-15 | ~$0.0001 | Career/business implications, architecture |
| CRITICAL | 15+ | ~$0.0002 | Irreversible decisions, security changes |

---

*This roster is the CTO's team directory. Read it before every swarm launch.*
*Rule: if you don't know who to call for a task — check this document first.*
