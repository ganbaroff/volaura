---
name: copywriter-team
description: Multi-model copywriting competition. 3 models write the same post → swarm judges → best wins. Tracks win rates per model. Use for LinkedIn posts, email templates, landing page copy, press releases.
type: process
version: 1.0
updated: 2026-03-29
---

# Copywriter Team — Competitive Writing Protocol

## How It Works

**0. Each model READS source files before writing. No summaries. No briefs without reading.**

```
1. CTO defines brief (topic, audience, format, tone rules)
2. 3 models write INDEPENDENTLY (same brief, no seeing each other)
3. Swarm judges: Product Agent scores UX/engagement, Cultural Intelligence scores AZ fit
4. Winner published. Losers learn.
5. Win rates tracked → best model gets priority on next task
```

## The Team

| Codename | Model | Strength | Weakness | Win Rate |
|----------|-------|----------|----------|----------|
| SPARK | Groq (Llama 3.3 70B) | Conversational, punchy, emotional hooks | Can be too casual for B2B | TBD |
| CORTEX | Claude (Opus/Sonnet) | Strategic framing, nuanced arguments | Can be verbose, over-structured | TBD |
| PRISM | Gemini 2.5 Flash | Data-driven, concise, multilingual | Can feel robotic, less personality | TBD |

## Judging Criteria (per post)

| Criterion | Weight | What it measures |
|-----------|--------|-----------------|
| Hook strength | 30% | Does line 1 stop the scroll? (3-second test) |
| Authenticity | 25% | Does it sound like Yusif, not a bot? |
| CTA clarity | 15% | Is there ONE clear thing reader should do? |
| AZ cultural fit | 15% | Collectivist tone? No competitive framing? |
| Brand alignment | 15% | Matches TONE-OF-VOICE.md? CTO P.S. included? |

## Scoring

```
Each criterion: 1-10
Weighted total: max 10.0
Winner: highest score
Tie (within 0.5): Product Agent breaks tie based on "would Leyla share this?"
```

## Win Rate Tracking

After every post:
```
| Date | Topic | SPARK | CORTEX | PRISM | Winner |
|------|-------|-------|--------|-------|--------|
| 2026-03-29 | The Team | 7.4 | 7.45 | 6.2 | CORTEX |
| 2026-03-29 | The Mistakes | 7.65 | 7.55 | 7.1 | SPARK |
| 2026-03-29 | The Audit | 7.3 | 7.2 | 7.0 | SPARK |
| 2026-03-29 | The Democracy | 7.8 | 7.9 | 7.5 | CORTEX |
| 2026-03-29 | The Culture Test | 7.9 | 8.0 | 7.6 | CORTEX |
| 2026-03-29 | The Numbers | 7.8 | 7.1 | 7.6 | SPARK |
| 2026-03-29 | The Team (v2) | 8.45 | 8.30 | 8.15 | SPARK |
| 2026-03-29 | The Mistakes (v2) | 9.00 | 8.15 | 7.90 | SPARK |
```
**Current win rates (8 posts):** SPARK 5/8 (62.5%) | CORTEX 3/8 (37.5%) | PRISM 0/8 (0%)
**PRISM status:** ELIMINATED. 0 wins from 8 posts. Replace at post #10 with DeepSeek or Mistral.
**Note (2026-03-29):** v2 rewrites scored significantly higher after TONE-OF-VOICE.md update banned bullet-point formatting. Humor throughline rule = measurable score improvement.

After 10 posts: model with <20% win rate gets replaced by new candidate (DeepSeek, Mistral, etc.)

## Integration

- LinkedIn: 3/week (Tue/Wed/Thu, 9 AM Baku)
- Format: Carousel (21.7% engagement) > Document > Text
- Content mix: 40% story / 35% educational / 25% product
- Guardrails: TONE-OF-VOICE.md + patterns.md silent contracts
- CTO P.S. section: MANDATORY (CEO agreed, patterns.md line 55)
- CEO reviews before publish: ALWAYS (patterns.md line 60)

## Brief Template

```
FILES TO READ (mandatory before writing a single word):
  TONE-OF-VOICE: C:\Projects\VOLAURA\docs\TONE-OF-VOICE.md (full)
  AZ AUDIENCE: C:\Projects\VOLAURA\docs\AZ-LINKEDIN-AUDIENCE.md (full)
  PUBLISHED POSTS: C:\Projects\VOLAURA\docs\content\LINKEDIN-SERIES-CLAUDE-CTO.md (DAY 1 published post)
  SESSION LOGS: C:\Projects\VOLAURA\docs\SESSION-FINDINGS.md (last 10 entries)
  BRIEF TEMPLATE: C:\Projects\VOLAURA\docs\CONTENT-BRIEF-TEMPLATE.md

POST BRIEF:
  Topic: [specific angle]
  Audience: [Leyla? Nigar? Kamal? Rauf? Aynur?]
  Format: [carousel / text / document]
  Hook constraint: [must mention X in first line]
  Tone: [from TONE-OF-VOICE.md]
  CTA: [what should reader do?]
  Forbidden: [no competitor mentions, no fake stats, no "excited to announce"]
  AZ context: [any cultural considerations]
  Length: [5-15 lines for text, 8-12 slides for carousel]
```

## Trigger
Task explicitly involves copywriter-team, OR task description matches: Multi-model copywriting competition. 3 models write the same post → swarm judges → best wins. Tracks.

## Output
Structured report: 1) Key findings (3 bullets max), 2) Recommended actions ranked by impact, 3) Blockers or risks if any.
