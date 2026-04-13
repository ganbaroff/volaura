---
name: content-factory
description: "Content factory: one idea becomes 10+ content units across YouTube, TikTok, LinkedIn, and social media — bilingual AZ+EN, for the entire VOLAURA ecosystem (5 products). Runs a 6-step agent chain: Strategist brief → Cultural audit → Content generation → Formatting → Quality gate → Delivery. Use this skill whenever the user wants to generate content from an idea, create a content batch, write video scripts, produce social media posts, plan a content calendar, or mentions 'content factory', 'content batch', 'контент завод', 'контент фабрика', or asks 'what should I post'. Also triggers on: script writing, hook generation, content repurposing, or any request to turn one idea into multiple formats."
---

# Content Factory — Agent Chain Architecture

One idea in → 6-step agent chain → 10+ production-ready content units out.

This skill orchestrates content creation by running through VOLAURA's existing agent team in the correct order. Each step has a defined input, output, and quality gate. No step is skipped. No agent works in isolation.

## The Chain (6 Steps — Sequential, Not Parallel)

```
STEP 1: COMMUNICATIONS STRATEGIST → Strategic Brief
STEP 2: CULTURAL INTELLIGENCE → AZ/CIS Audit
STEP 3: CONTENT GENERATION → Draft All Pieces
STEP 4: CONTENT FORMATTER → 5 Output Blocks Per Piece
STEP 5: QUALITY GATE → Constitution + Anti-AI + Tinkoff Check
STEP 6: DELIVERY PACKAGE → Ready for Telegram/Copy-Paste
```

Each step reads the output of the previous step. If any step fails its gate, go back and fix before proceeding.

---

## STEP 1: Communications Strategist Brief

**Agent:** Communications Strategist (memory/swarm/skills/communications-strategist.md)
**Input:** Raw idea from CEO
**Output:** Strategic Brief document

Before writing any content, create a brief:

```
BRIEF ID: CF-[date]-[seq]
SERIES: [Series 1: Claude / Series 2: Yusif / Standalone]
STRATEGIC GOAL: [What business outcome does this serve?]

NARRATIVE DECISION:
  Theme: [1 sentence — the core message]
  Proof Point: [Real number, real event, real code — no fabrication]
  Why Now: [What makes this timely?]

AUDIENCE TARGETING:
  Primary: [Leyla/Nigar/Kamal/Rauf/Aynur — pick ONE]
  Secondary: [pick ONE or none]
  Engagement Goal: [comments / shares / DMs / profile visits]

PLATFORM ASSIGNMENTS:
  [List which formats to generate — refer to Batch Plan below]

HOOK TYPE: [1 of 6 — check rotation against last batch]

CONSTRAINTS:
  Tone: [Tinkoff benchmark — would they publish this?]
  AZ Notes: [Cultural sensitivities from Cultural Intel]
  Forbidden: [Any topic-specific banned phrases]
  Series Arc: [Position in current series — post X of Y]

COPYWRITER: [CORTEX for long/nuanced, SPARK for punchy/quick]
```

**Gate:** Brief must have a real proof point (number, event, code). No brief = no content.

---

## STEP 2: Cultural Intelligence Audit

**Agent:** Cultural Intelligence Strategist (memory/swarm/skills/cultural-intelligence-strategist.md)
**Input:** Strategic Brief from Step 1
**Output:** Annotated Brief with cultural notes

Run these checks on the brief:

**Professional Identity Check:**
- Does the framing use collective ("our team") or individual ("I achieved")?
- For AZ audience: collective framing mandatory. "An objective system verified what peers already know."
- For EN audience: individual framing acceptable but not boastful.

**Language Check:**
- AZ text will be 20-30% longer — does the format allow it?
- Special characters (ə ğ ı ö ü ş ç) — will they render correctly?
- Formal "Siz" used, not informal "sən"?

**Competency Framing Check:**
- "I drive teams" → "Teams trust my guidance"
- "I present well" → "I build bridges between people"
- "I pivot fast" → "I find solutions under any conditions"

**Trust Signal Check:**
- If mentioning AI verification: include explanation of how it works
- If mentioning scores: frame as "objective assessment" not "competition"
- If mentioning organizations: their reputation adds trust

**Invisible Exclusion Check:**
- Photo requirements? → make optional
- Name field assumptions? → full name, not first/last split
- Competitive language? → reframe as achievement, not ranking
- Low score handling? → never public without consent

**Output:** Brief with [CULTURAL NOTE] annotations on anything that needs adjustment.

**Gate:** Zero exclusion risks. If found → fix in brief before proceeding.

---

## STEP 3: Content Generation

**Input:** Culturally-audited Brief from Step 2
**Output:** Draft content pieces

### Batch Plan (default — adjust per brief)

| # | Format | Platform | Language | Series |
|---|--------|----------|----------|--------|
| 1 | Long-form script | YouTube | RU/EN | — |
| 2 | Short-form script | TikTok/Shorts | AZ | — |
| 3 | Short-form script | TikTok/Shorts | EN | — |
| 4 | LinkedIn post | LinkedIn | EN | From brief |
| 5 | LinkedIn post | LinkedIn | AZ | Series 2 (NOT translation) |
| 6 | Carousel outline | LinkedIn/IG | EN | — |
| 7 | Thumbnail brief | YouTube | — | — |
| 8 | Description + tags | YouTube | EN+AZ | SEO |
| 9 | Thread/caption | Telegram/X | RU | — |
| 10 | Email snippet | Newsletter | EN | — |

CEO picks which to generate from this table. Then produce each piece.

### Generation Rules

**For video scripts:** Read `references/video-formats.md`
**For social posts:** Read `references/social-formats.md`
**For ALL pieces:** Read `references/tone-rules.md`

**Bilingual Strategy (CRITICAL):**
- EN and AZ versions are DIFFERENT pieces sharing the same core idea
- AZ: different opening, different cultural angle, collectivist framing
- EN: global tech audience, can be more direct
- Both must stand completely alone

**Hook Rotation:**
6 types — never repeat consecutive in same batch:
1. Contrarian / Absurd scenario
2. Vulnerability / Self-deprecating
3. Data / Specific number
4. Question / Uncomfortable truth
5. Story / Specific moment
6. Observation / List subversion

Check TRACKER.md for last hook used. Continue rotation.

**Real Data Only:**
- "44 agents" not "many agents"
- "0 users" not "growing user base"
- "419 TypeScript types" not "comprehensive type system"
- "34.8% defect rate" not "we're improving quality"

---

## STEP 4: Content Formatter

**Agent:** Content Formatter (memory/swarm/skills/content-formatter.md)
**Input:** Draft content pieces from Step 3
**Output:** 5 ready blocks per piece

For each content piece, produce:

```
1. POST_CLEAN — final text, no HTML, ready to copy-paste
2. TELEGRAM_HTML — only <b>, <i>, <a>, <code>, <pre> tags
3. EMAIL_HTML — clean HTML with inline styles
4. CTA — button text (max 5 words) + URL: [Button](URL)
5. IMAGE_PROMPT — 1-2 sentence brief for visual (style, mood, elements)
```

**Style Rules (from Content Formatter spec):**
- Hook → Value → Action structure
- Paragraphs: 2-4 sentences
- Bold: headings + key numbers only
- Alive, honest, with numbers. No corporate BS.
- If Yusif's voice: first person, direct, mix RU/EN terms

**Volaura Positioning:**
- NOT "volunteer platform"
- IS: "professional development platform" / "AI-powered skill verification"
- AURA = "verified professional credential"

---

## STEP 5: Quality Gate

Run these checks on EVERY formatted piece:

### Anti-AI Filter (27 patterns — zero tolerance)
Remove: "excited to announce", "leverage", "utilize", "innovative", "passionate about", "ecosystem" (marketing), "streamline", "robust", "scalable", "empower", "disrupt", "holistic", "paradigm", "at the end of the day", "it's worth noting", "let's dive in", "without further ado", "game-changer", "cutting-edge", "state-of-the-art", "synergy", "circle back", "low-hanging fruit"
Replace: "leverage" → "use", "utilize" → "use", "robust" → "reliable", "empower" → "help"

### Constitution (5 Laws)
1. Never Red — no red in visuals, errors = purple
2. Energy Adaptation — match reader's emotional state
3. Shame-Free — zero guilt, zero negative comparison
4. Animation Safety — safe motion only (fade, slide)
5. One Primary Action — ONE CTA per piece

### Tinkoff/Aviasales Benchmark
- Would Tinkoff publish this? Specific, slightly absurd, human, useful?
- Short sentences? Self-aware humor? Reader = equal, not prospect?

### Pre-Publish Checklist (all YES required)
1. Real number present?
2. Would I be embarrassed if TechCrunch quoted this?
3. Can I verify every claim?
4. Does it respect the reader's time?
5. CTA clear?

**Gate:** Any NO → fix and recheck. Do not proceed to Step 6.

---

## STEP 6: Delivery Package

Assemble final output for CEO:

```
═══════════════════════════════════════
📦 CONTENT BATCH: [Brief ID]
   Theme: [1 line]
   Pieces: [N] | Languages: [EN/AZ/RU]
═══════════════════════════════════════

For each piece:
──────────────────────────────────────
[FORMAT] — [PLATFORM] — [LANGUAGE]
Hook: [type] | Series: [1/2/none]
Audience: [primary persona]
──────────────────────────────────────

[POST_CLEAN text — ready to copy]

First comment: [link + UTM]
Hashtags: [3-5]
Best time: [day + time Baku]
Image brief: [1 line]
Quality: ✅ Passed
──────────────────────────────────────
```

### Telegram Delivery Format
When sending via Telegram bot, each piece goes as separate message:
- Text posts: plain text (under 4096 chars)
- Video: attached file
- Links: in reply to the post message

---

## The 5 Products (ecosystem reference)

| Product | Content angle |
|---------|---------------|
| VOLAURA | "We built the GRE for volunteer skills — AI scores what CVs can't" |
| MindShift | "Your brain isn't broken, the apps are — ADHD-first productivity" |
| LifeSimulator | "What if you could test-drive life decisions in a game?" |
| BrandedBy | "Your brand, built from verified data, not self-promotion" |
| ZEUS | "44 agents, 1 human, zero meetings — autonomous AI operations" |

---

## Reference Files

| File | When to read |
|------|-------------|
| `references/video-formats.md` | Step 3: any YouTube or TikTok script |
| `references/social-formats.md` | Step 3: any LinkedIn, Telegram, social post |
| `references/tone-rules.md` | Step 5: EVERY piece goes through quality gate |
| `memory/swarm/skills/communications-strategist.md` | Step 1: full briefing protocol |
| `memory/swarm/skills/cultural-intelligence-strategist.md` | Step 2: AZ/CIS audit |
| `memory/swarm/skills/content-formatter.md` | Step 4: formatting spec |
| `docs/content/TRACKER.md` | Step 3: hook rotation tracking |
