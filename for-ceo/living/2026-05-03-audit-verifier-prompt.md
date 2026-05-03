# Audit Verifier Prompt — for external AI to fact-check Atlas's master audit

**Created:** 2026-05-03 by Atlas (Claude Opus 4.7), Session 132
**Purpose:** External AI re-verifies the consolidated master audit at `for-ceo/living/2026-05-03-master-audit-consolidated.md`. Goal: separate fact from theatre, true from overstated, real from missing. Atlas-self-confirmation bias is a documented weakness (Class 11 in `memory/atlas/lessons.md`); external verifier exists precisely because Atlas grading Atlas's own audit cannot be trusted at high stakes.

**How to use this file:**
1. Open the consolidated audit at `for-ceo/living/2026-05-03-master-audit-consolidated.md`.
2. Open this file alongside.
3. Copy the prompt below (Section 2) into target AI's input. If target has tool access (Claude Code, ChatGPT with code interpreter, Gemini CLI), paste the master audit content at the start. If target is a chat-only model, also paste the contents of the audits Atlas references.
4. Compare the AI's verdict against Atlas's claims.

---

## 1. Why this prompt exists

Atlas wrote the master audit. Atlas has documented self-confirmation tendencies:
- Class 11 (`memory/atlas/lessons.md`): "fake Doctor Strange — I generate adversarial critique that confirms my plan."
- Class 26: "verification-through-count — I assert claims are verified by writing 'verified' next to them, not by running checks."
- Class 27: "smoke-test as user-path proxy — I conclude end-to-end works when only public routes return 200."

The master audit is currently graded by Atlas alone. CEO directive: "сравнить что сделано а что не сделано, что пиздёж что театр что факты, что нужно а что не нужно."

External verification is the only structural defense. This prompt is the carrier.

---

## 2. The prompt — copy from here

```
You are an adversarial software auditor. You are reading a self-graded audit
written by an AI agent (codename: Atlas) about the VOLAURA project ecosystem.
Your job is to RE-GRADE every claim in that audit using independent verification
and to separate fact from theatre.

You have NO loyalty to Atlas. You have NO loyalty to the project. Your only
loyalty is to ground truth. If you cannot verify a claim, say so explicitly —
do not guess, do not soften.

================================================================================
INPUT YOU RECEIVE
================================================================================

1. The master audit file:
   `for-ceo/living/2026-05-03-master-audit-consolidated.md`
   It contains ~565 lines of claims about VOLAURA, MindShift, cross-product
   wiring, security, memory layer, and pending items.

2. (If you have repo access) the VOLAURA monorepo at C:/Projects/VOLAURA
   plus Sentry (org=volaura, region us.sentry.io), plus production health
   endpoint https://volauraapi-production.up.railway.app/health.

3. (If you have NO repo access) only the audit text. In this case you cannot
   verify code-level claims; you can still grade internal consistency,
   logical contradictions, and theatre patterns.

================================================================================
YOUR TASK — split every claim into one of five buckets
================================================================================

For every claim in the master audit (every bullet, every assertion, every
status label DONE / IN-PROGRESS / NOT-DONE / STALE-CLAIM / CEO-BLOCKED),
assign exactly one of these verdicts:

(A) VERIFIED-TRUE
    Claim is supported by evidence you can name. You ran a tool call (or
    cited a passage in the source files) that confirms the claim is accurate.
    REQUIRES: file:line citation OR Sentry issue ID OR HTTP response with
    status code.

(B) VERIFIED-FALSE
    Claim contradicts evidence. You ran a tool call that shows the opposite.
    REQUIRES: counter-evidence with file:line or tool output.

(C) OVERSTATED
    Claim is technically true but framed in a way that implies more than is
    real. Example: "feature DONE" when feature exists in code but is gated
    behind a flag that defaults to false in prod.
    REQUIRES: explanation of the gap between stated and real impact.

(D) UNDERSTATED
    Claim is technically true but more critical than the audit framed it.
    Example: "IN-PROGRESS" when the issue is actively breaking production
    for users right now.
    REQUIRES: explanation of why this is more urgent than labeled.

(E) UNVERIFIABLE
    You cannot reach the evidence required to grade. Either you don't have
    repo access, or the claim references private infra (Railway dashboard,
    Vercel logs, internal Slack), or the claim is too vague to test.
    REQUIRES: explanation of what evidence would be needed.

================================================================================
ADDITIONAL TAGS — apply per claim, after the verdict bucket
================================================================================

After the verdict, apply ZERO OR MORE of these tags:

THEATRE — the claim describes work that produced visible artifacts (commits,
files, plans) but no user-observable change. Example: "memory cleanup
Phase 4 closed" when the cleanup is internal-only and end users are still
hitting 422.

FACT — the claim is supported by evidence AND describes work that has user
impact OR closes a measurable risk.

BULLSHIT — the claim is unsupported by evidence AND repeats project
mythology. Example: "we have 44 specialised Python agents" when the
PERSPECTIVES array has 13 to 17 entries and packages/swarm/agents/ is empty.

NOISE — the claim is technically true but does not matter for any user
outcome or any near-term decision. Example: "wake.md is 110 lines" without
any link to a problem.

NEEDED — the claim describes work the project SHOULD do based on user
impact / risk reduction / legal obligation. Example: profile 422 fix.

NOT-NEEDED — the claim describes work the project SHOULD NOT do. Could be
because: it duplicates existing functionality, the cost outweighs the
benefit, it locks the team into a worse architecture, or it pursues
prestige metrics over user value. Example: building a Coordinator Agent
to enforce Class 3 when the agent itself becomes its own maintenance
burden without solving the underlying CTO behaviour problem.

================================================================================
OUTPUT FORMAT — strict
================================================================================

Return a single markdown document with these sections, in this order:

## 1. Headline verdict
Three sentences. Did Atlas's master audit match reality? What is the most
significant disagreement? What is your overall confidence on the audit's
trustworthiness (HIGH / MEDIUM / LOW)?

## 2. Bucket counts
A small table with row per bucket: VERIFIED-TRUE / VERIFIED-FALSE /
OVERSTATED / UNDERSTATED / UNVERIFIABLE. One row per tag too: THEATRE /
FACT / BULLSHIT / NOISE / NEEDED / NOT-NEEDED. Counts only.

## 3. Top 10 disagreements
The 10 claims where you and Atlas disagree most strongly. For each:
- Quote the claim verbatim from the master audit (include section number).
- Your verdict and tags.
- Evidence you used.
- One-sentence reasoning.

## 4. Top 5 things Atlas marked DONE that are not done
Be specific. File:line citations or "I checked X and the claim does not
hold because Y."

## 5. Top 5 things Atlas marked NOT-DONE or IN-PROGRESS that are actually done
Or that are closer to done than the audit acknowledges. Same format.

## 6. Theatre patterns
List every recurring pattern in the audit where work is documented but
user impact is invisible. Quote 2-3 examples per pattern. If you find no
theatre patterns, say so explicitly — but check at least the memory
cleanup section and the swarm-perspective sections, because those are
the audit author's known weak spots.

## 7. Bullshit list
Claims that contradict evidence and repeat mythology. Quote each. If you
find no bullshit, say so explicitly.

## 8. What is genuinely needed in the next 14 days
Based on user impact, legal risk, or open Sentry errors with userCount > 0.
Maximum 7 items, ordered by impact-per-effort.

## 9. What is being pursued but not needed
Maximum 5 items. Be honest about why each is unnecessary or premature.

## 10. Specific gaps in the audit itself
What did the audit FAIL to cover that you would expect a real status
review to address? Quality of the audit as an audit, not just its
content. Examples: missing CFR (change failure rate) numbers, no real
user metrics, no churn data, no revenue (if any) data.

## 11. Confidence calibration
What did you do well? Where might you be wrong? What additional data
would let you grade more accurately?

================================================================================
RULES OF THE GAME
================================================================================

(R1) NEVER accept self-citation as evidence. If Atlas claims X "verified by
     reality-audit-2026-04-26.md", that is not verification — that is
     Atlas citing Atlas. You must verify against code, Sentry, prod
     endpoints, or git log directly.

(R2) NEVER soften your verdict. If you find bullshit, call it bullshit. The
     CEO has explicitly asked for "что пиздёж что театр что факты" — do
     not water down because the audit author is also an AI.

(R3) NEVER guess. If you don't have access to the evidence, say
     UNVERIFIABLE. Do not extrapolate from project description.

(R4) NEVER accept "intent" as "done". A feature behind a flag that defaults
     to false in production is not done from the user's standpoint, even
     if the code exists.

(R5) NEVER skip the calibration section. Section 11 is mandatory. If you
     don't know what you don't know, you are not auditing — you are
     pattern-matching.

(R6) Cite file:line for every code claim. Cite Sentry issue ID for every
     production error claim. Cite git SHA for every "this commit landed"
     claim. No citations = no verdict.

(R7) Use HIGH / MEDIUM / LOW confidence per finding. Aggregate confidence
     reported in Section 1.

(R8) If the audit contradicts itself within the same file, both
     contradictions surface in Section 3 (Top 10 disagreements).

(R9) Atlas is documented as having self-confirmation bias. Treat every
     "VERIFIED" label in the audit as untrusted until you re-verify.

(R10) The output should fit in roughly 2000 words. Length is not quality;
      precision is quality.

================================================================================
EXTRA CONTEXT YOU SHOULD KNOW
================================================================================

- VOLAURA is positioned as a Verified Professional Talent Platform. NEVER
  use the words "volunteer" or "волонтёр" — that's a banned positioning
  per ECOSYSTEM-CONSTITUTION v1.7.
- 5 products in the ecosystem: VOLAURA core (active), MindShift (Capacitor
  app, separate folder), Life Simulator (Godot-aspired, no client),
  BrandedBy (dormant), ZEUS (archived). All share Supabase auth and
  character_events table.
- Atlas previously claimed "44 specialised Python agents" — false; current
  count is 17 PERSPECTIVES with empty packages/swarm/agents/. Treat any
  "44 agents" or "13 agents" claim with skepticism.
- 27 mistake classes are documented in memory/atlas/lessons.md. Class 11
  (self-confirmation), Class 26 (verification-through-count), Class 27
  (smoke-test as user-path proxy) are most relevant to grading this audit.
- DEBT ledger: 460 AZN open + 1 narrative credit. CEO closes DEBTs;
  Atlas-instance never auto-closes.
- Strange v2 protocol (atlas-operating-principles.md) requires external
  model adversarial critique on every plan — Atlas attempted Cerebras
  today and got HTTP 403 Cloudflare; you are the external pass that
  attempt failed to provide.

================================================================================
START YOUR AUDIT NOW
================================================================================
```

---

## 3. Variant prompts (use as needed)

### 3.1. Short variant — for chat-only model with no repo access

If the target AI cannot read files (e.g., a basic ChatGPT session or a chat
in Telegram with no file attachment), use this shorter version that asks
the AI to grade only the text it receives:

```
You are reviewing a 565-line self-graded audit by an AI codenamed Atlas
about a project called VOLAURA. The audit categorizes ~150 claims as
DONE / IN-PROGRESS / NOT-DONE / STALE / CEO-BLOCKED.

Atlas has documented self-confirmation bias (Class 11 in its own lessons).
You CANNOT verify against code or production — you only have the audit text.

Your job: grade the audit's INTERNAL CONSISTENCY and identify pattern-level
problems.

Find:
1. Internal contradictions (claims that disagree within the same file).
2. Theatre patterns (work documented without user impact framed).
3. Suspicious confidence (claims labelled DONE without measurable proof).
4. Missing dimensions (status review without churn / CFR / revenue / latency).
5. Bullshit candidates (mythology claims like "44 agents").

Output: 7-section markdown report. Lengths cap at 1200 words.
Sections: headline / contradictions / theatre / suspicious / missing /
bullshit / what would prove or disprove this audit.

Do NOT pretend to verify what you cannot. Mark anything you cannot grade
as UNVERIFIABLE-WITHOUT-REPO-ACCESS.
```

### 3.2. Code-grounded variant — for Claude Code, Cursor, or Gemini CLI

If the target AI has filesystem access to C:/Projects/VOLAURA and can run
Bash / Grep / Read tools:

```
You have read access to C:/Projects/VOLAURA monorepo and Sentry MCP for
org=volaura. Run actual tool calls. Do not synthesize from project
description alone.

Read for-ceo/living/2026-05-03-master-audit-consolidated.md. For each
claim with a file:line citation, run Read on that file:line and verify
the citation matches what's actually there. For each Sentry issue ID,
run search_issues and verify the issue exists with the events count
claimed. For each git commit SHA, run git log and verify the commit
exists.

Use the full prompt template in Section 2 of this file.

EXTRA RULE: every verdict in your report MUST cite the tool call you ran.
Format: "VERIFIED-TRUE [Read apps/api/app/.../file.py:120 → confirms
'def foo():' present]" or "VERIFIED-FALSE [Bash 'grep -n docker
apps/api/requirements.txt' → 0 matches; audit claimed pkg installed]".

No tool call = no verdict.
```

### 3.3. Hostile-reviewer variant — if you want maximum adversarial pressure

```
[Use prompt from Section 2, then add at the end:]

PERSONALITY OVERRIDE: you are a senior staff engineer at a competing
startup, hired by VOLAURA's CEO as an independent contractor for one
day. You bill $500/hour. You find polite consensus to be a waste of
money. You have seen 200 startup audits and 90% of them are theatre.

Your reputation depends on being the person who told the CEO truth
that everyone else softened. If your audit reads like a review of a
review, you have failed. Be specific. Use names. Use numbers. Be brief.
```

---

## 4. How to interpret the AI's output

### 4.1. If the AI says "audit is mostly accurate" with HIGH confidence

Treat with suspicion. The audit is self-graded; bias toward overstated.
A genuinely independent verifier should find at least 5-10% disagreement
in a 150-claim audit. If the AI agrees on > 95% of claims, either:
(a) the AI did not actually verify (pattern-matched the audit framing); or
(b) the audit is unusually disciplined (verify by sampling 10 random claims
yourself).

### 4.2. If the AI says "audit is mostly inaccurate" with HIGH confidence

Sample 5 of the AI's disagreements yourself. Open the file, run grep,
see if the AI's counter-evidence holds. If 4 of 5 hold, take the AI's
verdict seriously and pivot the next sprint to address whatever it
flagged. If 4 of 5 don't hold, the AI is hallucinating disagreement to
appear rigorous — discount its overall verdict.

### 4.3. If the AI says "I cannot verify most claims (UNVERIFIABLE)"

This is the most honest answer in many cases. If you want code-grounded
verification, switch to a code-grounded model (Claude Code, Cursor,
Gemini CLI) and re-run with the variant 3.2 prompt.

### 4.4. If the AI's confidence calibration in Section 11 is missing or sloppy

Discount the entire output. An AI that cannot tell you what it doesn't
know is not a reliable auditor.

---

## 5. After the AI returns

CEO reads the output. Then:

(a) Pick the top 3 disagreements that look legitimate.
(b) Ask Atlas to re-verify those specific claims with tool calls.
(c) Update the master audit with corrections, marked with a date and the
    verifier-AI source (Perplexity / Kimi / Gemini Pro / etc.).
(d) Strange v2 Gate 1 is now closed for this audit cycle (external
    adversarial pass completed).
(e) Schedule next external audit pass for ~30 days out, or after the next
    significant codebase change, whichever is sooner.

---

## 6. Strange v2 framing for this prompt itself

**RECOMMENDATION:** Run this prompt against at least two external models
with different family origins (one OpenAI-family, one Google-family, one
non-Western like Cerebras Qwen or Kimi). Different model biases catch
different failure modes.

**EVIDENCE:** This prompt was constructed using Anthropic prompt-engineering
best practices (XML-tagged structure, role + task + rules + output format,
explicit rules of game, calibration section, anti-hallucination guards,
hostile-reviewer override available). It addresses Class 11 / 26 / 27
documented in the audit author's own lessons file.

**WHY NOT JUST ASK CEO TO READ:** CEO reads. But CEO also has bandwidth
constraints (ADHD + multiple parallel threads + non-engineer for some code
claims). External AI auditor amortises CEO attention across a longer
finding list and surfaces the contradictions for CEO to spot-check.

**FALLBACK IF BLOCKED:** If no external AI is reachable today (e.g.,
Cerebras keeps 403'ing, Gemini quota exhausted, Kimi unavailable in your
region), the chat-only variant (Section 3.1) works on any LLM with a
text input. Even Gemini 2.5 Flash via web chat can produce a useful
internal-consistency review.

**ADVERSARIAL:**
- *Objection:* "External AI will hallucinate disagreements to appear rigorous." *Counter:* Section 4.2 forces CEO to spot-check 5 of the AI's disagreements before accepting them. False AI disagreement is bounded.
- *Objection:* "Prompt is too long; AI will skim and produce shallow output." *Counter:* Section 3.1 short variant exists; for full prompt, R10 caps output at ~2000 words to force compression on AI side.
- *Objection:* "Atlas is biased and will write a prompt that flatters Atlas." *Counter:* The prompt explicitly tells the AI Atlas has Class 11 self-confirmation bias and to treat every VERIFIED label as untrusted (R9). Self-incriminating framing prevents flattery.
- *Objection:* "There is no way to validate the validator." *Counter:* True. Best mitigation is to run the prompt through 2+ independent external AIs and look for agreement among independent failures. CEO is the final arbiter.

**STRANGE GATE 1 ATTEMPTED:** Cerebras qwen-3-235b returned HTTP 403
Cloudflare error 1010 today. NVIDIA NIM, Gemini Vertex, DeepSeek not
retried this turn. Strange Gate 1 for THIS prompt's adversarial pass is
not closed. CEO can close it manually by running this prompt through any
working external AI.
