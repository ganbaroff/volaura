# VOLAURA QUALITY STANDARDS v1.0

**Sources:** Toyota Production System (14 principles, Jidoka, Kaizen, Poka-yoke), Apple (ANPP, EPM, zero defect), DORA Metrics (elite team benchmarks), Lean Six Sigma (DMAIC). Researched via NotebookLM deep research (2026-04-03).

**Applies to:** CTO (Claude) + all 40 AI agents. Every task. Every batch. No exceptions.

---

## 1. BEFORE CODING — Definition of Ready (DoR)

Task CANNOT enter development until ALL of these exist:

```
□ Acceptance Criteria written (3-5 PASS/FAIL conditions)
□ Competency assigned: which agent owns this task?
□ Dependencies identified: what must exist before this works?
□ Scope locked: IN (what we build), NOT IN (what we defer)
□ Effort estimated: S/M/L based on past velocity
```

**Toyota principle:** Standardized Tasks — no agent starts without clear instructions.
**Apple principle:** ANPP document — elaborate detail BEFORE building.
**If DoR is not met → task is returned to planning. Not started.**

---

## 2. DURING CODING — Jidoka (Stop the Line)

If ANY of these happen during execution → STOP. Fix before continuing:

| Signal | Action | Toyota term |
|--------|--------|-------------|
| TypeScript/Python error introduced | Stop. Fix. Then continue. | Andon cord |
| Test fails that was passing | Stop. Root cause. Don't comment out. | Jidoka |
| Agent produces output without citing sources | Reject output. Require evidence. | Quality at source |
| Console errors appear in preview | Stop. Fix. Not "fix later." | Line stop |
| Acceptance criteria impossible to verify | Stop. Rewrite AC. Not "it probably works." | Standard work |

**Rule:** "Fix later" is banned. Fix NOW. Toyota stops the entire factory for one defect. We stop the sprint for one broken test.

---

## 3. BEFORE MARKING DONE — Quality Gate (DoD)

### Universal DoD (ALL tasks):

```
□ All acceptance criteria PASS (verified, not assumed)
□ No new errors (TypeScript, Python, console)
□ i18n: user-facing text in BOTH en + az
□ If API: response matches Pydantic schema
□ If DB: RLS policy exists and verified
□ If UI: preview screenshot confirms rendering
□ SHIPPED.md updated
□ sprint-state.md updated
```

### Additional gates by task type:

| Task type | Additional gate |
|-----------|----------------|
| Security change | Security agent sign-off |
| API endpoint | Rate limiting verified |
| Assessment change | Assessment Science agent audit |
| User-facing copy | AZ native review (2 grammar agents) |
| Payment code | Security + Financial agent pair |
| Database migration | RLS + schema verification |

**Apple principle:** Changes only after QA approval. No exceptions. Not for speed. Not for "it's a small change."

---

## 4. AFTER EACH BATCH — DORA Metrics + Kaizen

### Track (in memory/context/quality-metrics.md):

| Metric | How to measure | Elite target |
|--------|---------------|-------------|
| **AC Coverage** | Tasks with AC written BEFORE / total tasks | 100% |
| **First-pass AC rate** | Tasks where all AC passed on first attempt / total | >80% |
| **Defect rate** | Post-completion bugs found / tasks completed | <5% |
| **Solo execution** | Tasks done without agent consultation / total | 0% |
| **Provider diversity** | Swarms with ≥2 LLM providers / total swarms | 100% |
| **DoD compliance** | Tasks with ALL DoD boxes checked / total | 100% |

### Kaizen (continuous improvement):
After EVERY batch, answer ONE question:
> "What is the ONE thing that, if improved, would prevent the most defects next batch?"

Write the answer. Implement it. Measure if it worked.

**Toyota principle:** Kaizen — small daily improvements. Not big monthly rewrites.

---

## 5. POKA-YOKE — Structural Mistake Prevention

Rules that rely on willpower fail (75 mistakes in 12 days prove this).

| Mechanism | What it prevents | Type |
|-----------|-----------------|------|
| DoR gate (Step 1.5) | Building without clear requirements | **Structural** — task blocked |
| Quality gate (Step 4.5) | Shipping broken code | **Structural** — DONE blocked |
| Swarm retro (Step 0a) | Repeating past mistakes | **Structural** — sprint blocked |
| LLM provider check (Step 5.4) | Echo chamber swarm | **Structural** — swarm blocked |
| CEO Report Agent (Step 5) | Technical debris to CEO | **Structural** — output filtered |
| DORA tracking (Step 5.5) | Invisible quality decay | **Process** — recorded every batch |
| NotebookLM research | Shallow analysis | **Process** — deep research required for L3+ tasks |
| Agent refusal right | Tasks without AC | **Cultural** — agents REFUSE work without AC |

**Toyota principle:** Poka-yoke — make errors physically impossible, not merely unlikely.
**Apple principle:** Zero defect from every supplier. Every agent is a supplier.

---

## 6. DEFECT RATE TARGETS

| Timeline | Target | Baseline |
|----------|--------|----------|
| Current | 34.8% (75/210) | Measured 2026-04-03 |
| After 50h of work | <10% | 3.5x improvement |
| After 200h | <5% | DORA elite threshold |
| Long-term | <1% | Approaching 6 sigma |

**How to get there:** Not by trying harder. By structural prevention (Poka-yoke) + measurement (DORA) + daily improvement (Kaizen).

---

## 7. TOOLS THAT ENFORCE QUALITY

| Tool | Quality function | Status |
|------|-----------------|--------|
| **Playwright MCP** | Visual verification — see what user sees | Installed |
| **Sentry MCP** | Production errors in CTO context | Installed |
| **Langfuse** | LLM call monitoring — token usage, latency, cost | Pending setup |
| **NotebookLM** | Deep research — prevents shallow analysis | Active |
| **Multi-model swarm** | Diverse critique — prevents echo chamber | Active |
| **quality-metrics.md** | DORA tracking — prevents invisible decay | Created |

---

*"The Toyota Way is about continuous improvement and respect for people. If you're not improving every day, you're falling behind." — Jeffrey Liker*

*"Quality is more important than quantity. One home run is much better than two doubles." — Steve Jobs*

*Document created: 2026-04-03. Sources: NotebookLM deep research (Toyota TPS, Apple ANPP, DORA 2026, Lean Six Sigma DMAIC). To be reviewed and improved after every 10 batches.*
