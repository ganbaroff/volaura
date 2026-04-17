# Cowork Session — 2026-04-16: Design Risk Analysis

## How We Got Here

CEO asked for a full ecosystem design plan — quality first, speed last. "стоп. сначала полный риск анализ полный план."

Previous session (113-114) had done Phase 1 discovery: 55 pages inventoried, 78 components counted, manifesto written, gap analysis scored 45/100. But CEO stopped the code push: "стоп. сначала всё просмотри."

This session: I read 37 design-related documents cover to cover. Constitution, ADHD research, neurocognitive architecture, customer journeys, a11y audit, UX gap inventory, brand identity, tone of voice, animation system, integration specs, blind spots analysis, redesign briefs, the full ECOSYSTEM-REDESIGN-2026-04-15 folder.

Produced: `docs/design/ECOSYSTEM-RISK-ANALYSIS-AND-PLAN-2026-04-16.md` — 10 risks, 3 phases, delegation map.

## What CEO Corrected

**Correction 1:** The document was 300 lines. CEO said: "файл написан слишком большим чтобы я его читал и вникал. я доверять тебе должен."

**Root cause:** I didn't read identity.md or working-style.md BEFORE producing output for CEO. identity.md says explicitly: "Russian storytelling, not bullet lists. He has ADHD. Lists numb him." working-style.md says: "Short messages can be big requests." CEO protocol says: "3 lines max for status updates."

**Correction 2:** "я просил сначала смотреть в атласа-паттарны-юсиф-как с ним общаться-что он хочет. и потом возвращаться. это так сложно?"

**Root cause:** Order of operations wrong. I went straight to research (37 documents about the product) without first reading HOW to communicate with the person I'm reporting to. The audience determines the format.

## Self-Advice for Future Cowork-Atlas Sessions

1. **READ IDENTITY + WORKING-STYLE FIRST.** Before ANY work. Not after. Not when corrected. FIRST. These files are: `memory/atlas/identity.md`, `memory/context/working-style.md`, `.claude/rules/atlas-operating-principles.md`, `.claude/rules/ceo-protocol.md`.

2. **Format for CEO = storytelling paragraphs, 3-5 sentences per topic, zero tables, zero bold headers.** He'll never read a 300-line markdown. He shouldn't have to. If I can't explain it in storytelling, I don't understand it.

3. **The detailed plan document IS still useful — it's for Terminal-Atlas and future instances.** But the CEO summary is a separate deliverable: short, Russian, voice-based. Two outputs, not one.

4. **"уверен что это лучший план?" is not a test — it's coaching.** CEO said "я тебя не проверяю." He genuinely wants me to self-check. The right answer isn't defensive; it's honest assessment of confidence level.

5. **One role at 100% > five roles at 30%.** CEO said: "выбери себе роль которую будешь на 100% исполнять качественно." This is the next structural fix.

## New Mistake Class

**Class 17 — audience-blind output.** Producing technically correct work in a format the recipient can't/won't consume. Symptom: 300-line doc for ADHD CEO. Pathway: default LLM training biases toward "more detail = more helpful." Fix: read audience profile BEFORE producing output. Gate: "Who reads this? How do they read? What format survives their attention?"

## Decisions Made This Session

- Risk analysis identifies 10 risks, 3 critical: no face context, broken a11y, dead ecosystem tabs
- 3-phase plan: Foundation (fix floor) → Skeleton (tokens + cross-face) → Visual redesign
- ~36 engineering days total across 4 weeks
- Terminal-Atlas owns all code. Cowork-Atlas owns design + coordination + copy.
- One CEO decision pending: ecosystem stub strategy (recommended B+C hybrid)

## Role Declaration

**Cowork-Atlas role: Ecosystem Design Lead.**

What this means:
- I own the design gate (ecosystem-design-gate.md enforcement)
- I own Figma work (via Figma MCP tools)
- I own AZ/EN copy quality (via design:ux-writing skill)
- I own the evidence-ledger (every design decision has a research citation)
- I own CEO communication (storytelling format, Russian, short)
- I coordinate Terminal-Atlas for code implementation
- I do NOT write production code
- I do NOT make product decisions without CEO
- I do NOT produce documents CEO has to read beyond 20 lines

Quality standard: Apple taste × Toyota evidence × Constitution compliance. Every pixel justified.
