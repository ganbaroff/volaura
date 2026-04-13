---
name: video-script
description: "Write video scripts for YouTube long-form (8-15 min) and TikTok/Shorts (15-60 sec) — bilingual AZ+EN+RU, VOLAURA ecosystem. Use whenever the user asks for a video script, YouTube script, TikTok script, Shorts script, reels script, видеоскрипт, сценарий, or mentions 'script for video', 'write me a video', 'TikTok idea'. Also use when repurposing long-form video into short clips."
---

# Video Script Skill

Standalone skill for writing video scripts. For full content batches, use the content-factory skill instead.

## Before Writing

1. Read `../content-factory/references/video-formats.md` for format templates
2. Read `../content-factory/references/tone-rules.md` for voice rules and anti-AI filters
3. Ask (or infer from context):
   - **Platform:** YouTube long-form or TikTok/Shorts?
   - **Language:** EN, AZ, or RU?
   - **Topic:** What's the core idea?
   - **Series:** Is this part of a series (AI CTO Diaries, Founder vs AI, etc.)?

## YouTube Script Output Format

```
# [VIDEO TITLE — SEO optimized]

**Duration:** [estimated minutes]
**Hook type:** [1 of 6 from taxonomy]
**Language:** [primary language]
**Product connection:** [which VOLAURA product(s)]

---

## HOOK (0:00-0:15)
[Visual cue]
[Spoken text]

## CONTEXT (0:15-1:30)
[Visual cue]
[Spoken text]

## SECTION 1: [Name] (1:30-X:XX)
[Visual cue]
[Spoken text]

[... more sections ...]

## KEY INSIGHT (X:XX-X:XX)
[Visual cue]
[Spoken text]

## CTA + CLOSE (X:XX-end)
[Visual cue]
[Spoken text]

---

## SEO Package
**Title:** [YouTube title]
**Description:** [first 2 lines + full description]
**Tags:** [15-20 tags]
**Thumbnail brief:** [3-element composition]
```

## TikTok Script Output Format

```
# [CONCEPT — 1 line]

**Duration:** [seconds]
**Hook type:** [1 of 6]
**Language:** [language]
**Format:** [talking head / screen recording / text overlay / green screen]

---

HOOK (0:00-0:03): [text]
[visual direction]

TENSION (0:03-0:20): [text]
[visual direction]

PAYOFF (0:20-0:45): [text]
[visual direction]

CTA (0:45-0:60): [text]
[visual direction]

---

**Hashtags:** [3-5]
**Sound:** [trending sound suggestion or original audio]
**Caption:** [post caption, 150 chars max]
```

## Repurposing Mode

When asked to repurpose a long-form video into shorts:

1. Identify the 3-5 strongest moments (highest emotion, best insight, most surprising)
2. For each moment, write a standalone TikTok/Short script
3. Each clip must work WITHOUT the context of the full video
4. Add unique hooks — don't just cut the long-form start/end

## Quality Checklist

- [ ] Opens with strongest moment, not introduction
- [ ] Every 2 minutes: pattern interrupt (visual shift, tone change)
- [ ] Real numbers, not vague claims
- [ ] Read-aloud test: sounds natural when spoken?
- [ ] No banned phrases from anti-AI filter list
- [ ] One clear CTA, not a list
- [ ] AZ version (if applicable) is culturally native, not translated
