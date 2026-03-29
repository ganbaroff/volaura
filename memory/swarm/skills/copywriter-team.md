---
name: copywriter-team
description: Multi-model copywriting competition. 3 models write the same post → swarm judges → best wins. Tracks win rates per model. Use for LinkedIn posts, email templates, landing page copy, press releases.
type: process
version: 1.0
updated: 2026-03-29
---

# Copywriter Team — Competitive Writing Protocol

## How It Works

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
```

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
