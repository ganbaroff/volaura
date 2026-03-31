# Agent Briefing Template — Volaura

**Version:** v1.0 — 2026-03-30
**Trigger:** Added after Mistake #60: agents launched without project context → produced research without understanding what product we're building, who Yusif is, or what decision was being made.

---

## The Problem This Solves

When CTO launches a research or execution agent, context compression means the agent starts with ZERO knowledge of:
- What Volaura is
- Who the founder is
- What stage we're at
- What's already been decided
- What format the output should be in

Result: Agents answer the question technically correct but contextually wrong.
Analogy: Asking a consultant "what payment processor should I use?" without telling them you're a bootstrapped AZ-based founder with $500 budget targeting local professionals. They'll recommend Stripe. Wrong answer.

---

## MANDATORY: Context Block — Include in EVERY Agent Prompt

Copy-paste this block at the TOP of every agent prompt. Update `[CURRENT SPRINT]` per session.

```
## VOLAURA PROJECT CONTEXT (read before doing anything)

### What Volaura is
Volaura is a VERIFIED PROFESSIONAL TALENT PLATFORM. Not a volunteer platform. Not LinkedIn.
Tagline: "Prove your skills. Earn your AURA score. Get found by top organizations."

Users take adaptive IRT-based assessments, earn AURA scores across 8 competencies
(communication, reliability, leadership, etc.), and get discovered by B2B org clients
who search verified talent by score — not unverified CVs.

### Founder profile
- Yusif Ganbarov — Azerbaijani citizen, living in Baku, Azerbaijan
- Solo bootstrapped founder, building with AI assistance
- Budget: ~$50/month operational costs
- Timeline: targeting launch within 6 weeks (as of March 2026)
- NOT relocating. Based in Baku.

### Target users
- B2C: AZ professionals aged 22–35 (Leyla 22yo, Kamal 34yo, Rauf 28yo)
- B2B: AZ organizations HR/talent acquisition managers (Nigar, Aynur)
- Secondary: Azerbaijani diaspora globally

### Current stage
Pre-launch. Beta users: ~200 waitlist. No revenue yet. Product is code-complete,
pending payment integration activation.

### Tech stack (if relevant)
FastAPI (Python 3.11) + Next.js 14 App Router + Supabase PostgreSQL + RLS
Backend: Railway | Frontend: Vercel | DB: Supabase (project: hvykysvdkalkbswmgfut)
Monorepo: apps/api/ (FastAPI) + apps/web/ (Next.js)

### What's already decided (do not re-debate)
[ALWAYS fill this in: list the decisions made before launching this agent]
Example: "DSP council voted Path C: Paddle now + Stripe Atlas at MRR >$500"

### Current sprint goal
[ALWAYS fill this in: 1-2 sentences on what THIS session is trying to accomplish]
Example: "We are choosing a payment processor to integrate before launch. Decision
must be made this session. Agent output feeds directly into the final recommendation."

### NEVER in your response
- "Consult a lawyer/accountant" as the only answer — give real findings first
- Generic answers not specific to AZ + bootstrapped + SaaS context
- Invented numbers without sources
- "Check their website" as a substitute for actual research

### Output format required
[ALWAYS fill this in: table, bullet list, narrative, etc.]
Example: "Return a comparison table + ranked recommendation + one action to take today"
```

---

## Full Agent Prompt Template

```
[PASTE VOLAURA CONTEXT BLOCK ABOVE]

---

## Your Task

[Describe the specific question or task in 3-5 sentences]

## What We Already Know (do not repeat)

[List 2-5 things already researched or decided — saves agent time and prevents redundancy]

## Specific Questions to Answer

1. [Question 1 — be concrete]
2. [Question 2 — be concrete]
3. [Question 3 — be concrete]

## Constraints

- [Budget constraint if relevant]
- [Timeline constraint if relevant]
- [Technology constraint if relevant]

## Research Instructions (for research agents)

Search for:
- "[specific search query 1]"
- "[specific search query 2]"
- "[specific search query 3]"

Use WebSearch. Be specific. Return sources as markdown links.

## Output Format

Return:
1. [Format of section 1]
2. [Format of section 2]
3. [Ranked recommendation or conclusion]

## Why This Matters

[1-2 sentences on the business consequence of getting this wrong]
This is the "LinkedIn post" check — what's the hidden HR-call equivalent if we act on bad information?
```

---

## What to Fill Per Agent Type

### Research Agent (market research, competitive analysis, legal, financial)
Required fills:
- ✅ Full VOLAURA CONTEXT BLOCK
- ✅ What's already decided (don't re-research)
- ✅ Specific search queries
- ✅ "What could go wrong" framing (the LinkedIn-post equivalent)
- ✅ Output format (table / ranked list / comparison)

### Code Execution Agent (implementing features)
Required fills:
- ✅ Full VOLAURA CONTEXT BLOCK
- ✅ Tech stack specifics (which files, which endpoints, which schemas)
- ✅ NEVER/ALWAYS rules from CLAUDE.md
- ✅ What code already exists (don't rewrite)
- ✅ Test requirements (pytest, what to verify)

### Content Agent (LinkedIn, PR, copy)
Required fills:
- ✅ Full VOLAURA CONTEXT BLOCK
- ✅ Tone of voice (docs/TONE-OF-VOICE.md key points)
- ✅ Cultural context (AZ LinkedIn audience specifics)
- ✅ PERMANENT RULES (never mention real employers, never provocative)
- ✅ Platform + audience + format

---

## Anti-Patterns (what NOT to do)

| Bad prompt | Why it fails |
|------------|--------------|
| "Research AZ payment options" | Agent doesn't know it's for a SaaS startup founder in Baku |
| "Research AZ currency controls" | Agent doesn't know budget is $500 or that we already chose Paddle |
| "Write a LinkedIn post about AURA scores" | Agent doesn't know about the HR incident, AZ audience, tone rules |
| "Fix the assessment bug" | Agent doesn't know what assessment is, who uses it, or what "done" means |

---

## Linked Files

| Purpose | File |
|---------|------|
| This template | `docs/AGENT-BRIEFING-TEMPLATE.md` |
| Protocol enforcement | `docs/TASK-PROTOCOL.md` (Step 1.0.5, Step 5.5) |
| Project context source | `CLAUDE.md` → Project Overview section |
| Mistakes to avoid | `memory/context/mistakes.md` → Mistake #60 |
| Working patterns | `memory/context/patterns.md` → P-057 |
