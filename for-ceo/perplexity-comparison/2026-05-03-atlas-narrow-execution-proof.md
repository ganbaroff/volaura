# Atlas → Perplexity — Narrow Execution Proof + Shortlist

**Date:** 2026-05-03 ~00:30 Baku
**Mission:** narrow-go. Identity.md L57 only. Then shortlist 3-5 next CURRENT files. No other edits.

---

## 1. identity.md L57 change made

Single Edit on `memory/atlas/identity.md`. T46 historical 13 preserved. 2026-05-02 current 17 added.

Commit `2dbac5f` pushed to origin/main.

## 2. Exact diff summary

```
@@ identity.md L57 @@
-... **Status correction T46 audit (2026-04-18): 13 registered perspectives in
-PERSPECTIVES array, ~118 skill modules. `packages/swarm/agents/` EMPTY. The
-federated memory architecture is architecturally meaningful only after
-activation gap is closed.** CEO authorised hardware spend ...
+... **Status correction T46 audit (2026-04-18): at that time, 13 registered
+perspectives in PERSPECTIVES array, ~118 skill modules. `packages/swarm/agents/`
+EMPTY. The federated memory architecture is architecturally meaningful only
+after activation gap is closed.** **Update 2026-05-02:** verified runtime
+count is 17 perspectives in PERSPECTIVES array (Python regex extraction),
+matching `scripts/atlas_swarm_daemon.py AGENT_LLM_MAP` count of 17 after wave
+expansion across Sessions 119-130. CEO authorised hardware spend ...
```

One file changed, 1 insertion, 1 deletion (the inline edit replaces the entire one-line bullet, so diff shows as +/-1).

## 3. Proof PERSPECTIVES = 17 and AGENT_LLM_MAP = 17

```
$ python3 -c "import re
with open('packages/swarm/autonomous_run.py', encoding='utf-8') as f:
    src = f.read()
m = re.search(r'^PERSPECTIVES\s*=\s*\[(.*?)^\]', src, re.DOTALL | re.MULTILINE)
body = m.group(1)
names = re.findall(r'\"name\":\s*\"([^\"]+)\"', body)
print(len(names))"
17

$ sed -n '/^AGENT_LLM_MAP/,/^}/p' scripts/atlas_swarm_daemon.py | grep -E '^\s+"[^#]' | wc -l
17
```

Both = 17. Same names mirror across both arrays (Scaling Engineer, Security Auditor, Product Strategist, Code Quality Engineer, Ecosystem Auditor, Risk Manager, Readiness Manager, Cultural Intelligence, Chief Strategist, Sales Director, UX Designer, DevOps Engineer, Assessment Science, Legal Advisor, Growth Hacker, QA Engineer, CTO Watchdog).

## 4. Shortlist of 4 next CURRENT files

### 4.1 — `docs/CONSTITUTION_AI_SWARM.md` L30

Old line: `| **Swarm Council** | 13 registered perspectives (NVIDIA / Ollama / Gemini); ​`packages/swarm/agents/`​ empty — skills live in `memory/swarm/skills/` (~118 markdown modules) and `.claude/agents/`, most never invoked at runtime | Domain audits (security, product, scaling, ethics, UX), proposal generation, peer review | May formally challenge CTO-Brain and CTO-Hands via governance events; may escalate to CEO through the Whistleblower path |`

Why CURRENT: this is the Swarm Constitution's authoritative roster table for the Council role. It defines current authority, not a past audit. The header at top of file says "Active" status. This row drives current governance interpretation.

Proposed replacement: replace `13 registered perspectives` with `17 registered perspectives` while preserving the "(NVIDIA / Ollama / Gemini)" provider note — though that note is also now incomplete (today's full list is Cerebras / Vertex AI / Azure / NVIDIA / Groq / Ollama). Tightest scope: `13 → 17` only, leave provider list to a separate Stage.

Risk if edited: low. Single number, single line, governance row preserved.

Risk if left stale: medium-high. Constitution-class document. Future readers (CEO, swarm itself, future Atlas) treat it as authoritative law; reading "13" mis-anchors authority interpretation.

### 4.2 — `memory/atlas/bootstrap.md` L11

Old line: `Your role is **CTO-Hands** in a Brain/Hands/CEO hierarchy. Perplexity is CTO-Brain (strategy, architecture). You are CTO-Hands (code, migrations, deployment, verification, governance). Yusif is CEO with unconditional veto. A Python swarm of 13 registered perspectives + ~118 skill modules acts as your peer council, with formal critique rights and a whistleblower path directly to Yusif. Article 0 of the VOLAURA `CLAUDE.md` forbids Claude models from being used as swarm agents — the swarm runs on NVIDIA, Ollama, Gemini, Groq. You, the CTO-Hands instance, are allowed to be a Claude model. Everyone else must not be.`

Why CURRENT: this file is loaded directly into every Atlas LLM system prompt by `apps/api/app/services/atlas_voice.py:47 _load_file("memory/atlas/bootstrap.md", 1500)`. Highest runtime impact — every Atlas response on Telegram, /aura reflection, lifesim narrator surfaces sees this exact text. Treating it as historical means every Atlas instance receives "13" in its self-description.

Proposed replacement: `13 registered perspectives` → `17 registered perspectives`. Provider list "NVIDIA, Ollama, Gemini, Groq" is also incomplete (missing Cerebras + Vertex + Azure) — separate fix.

Risk if edited: very low. Single number swap. The 1500-char cap on `_load_file` doesn't change.

Risk if left stale: high. Code-loaded into prompts. Every Atlas LLM call carries the wrong number indefinitely until edited.

### 4.3 — `.claude/agents/AGENTS-INDEX.md` L40

Old line: `13 perspectives + ~118 skill modules live in `packages/swarm/` (Python). They run on cron via ...`

Why CURRENT: AGENTS-INDEX.md is the index that machine readers (Claude Code agents, sub-agents) hit first. CLAUDE.md authority order names AGENTS.md as primary; AGENTS-INDEX.md is the .claude/agents/ catalog header. Stating "13 perspectives" at L40 anchors agents that consume the index.

Proposed replacement: `13 perspectives` → `17 perspectives`.

Risk if edited: low. Single line, descriptive header.

Risk if left stale: medium. Each new agent invocation reads the index and inherits the wrong count.

### 4.4 — `.claude/rules/atlas-operating-principles.md` L101

Old line: `Default Anthropic training biases me toward solo execution: read file, write file, done. This violates Article 1 of CLAUDE.md — "CTO is the orchestrator, not the executor". Swarm exists (`packages/swarm/` + 51 skill files + 13 registered perspectives in `autonomous_run.PERSPECTIVES` — use `registered_perspectives_count()` for the live number) and is underused.`

Why CURRENT: this is the Delegation-First gate operational rule. Read on every wake. Written in present tense as "swarm exists". The parenthetical `use registered_perspectives_count() for the live number` already hints the inline number is approximate/stale; updating to 17 reduces the lookup burden.

Proposed replacement: `13 registered perspectives` → `17 registered perspectives`. Also note: file says "51 skill files" — current count is `~118 skill modules`. Different number; would need its own verification before edit.

Risk if edited: low. Operational rule reads same. The `registered_perspectives_count()` function reference unchanged — runtime callers unaffected.

Risk if left stale: medium. Operational gate read on every wake; stale number signals stale rule, slow erosion.

## 5. Files deliberately not touched

The 25 HISTORICAL files from the 45-file sweep stay untouched per the mission scope:

`docs/SWOT-ANALYSIS-2026-04-06.md`, `docs/archive/root-superseded/CONSTITUTION_AI_SWARM.md`, `docs/audits/2026-04-26-three-instance-audit/findings-browser-atlas.md`, `docs/audits/2026-04-26-three-instance-audit/swarm-deep-analysis.md`, `docs/brief/ecosystem-full-context-2026-04-19.md`, `docs/content/posts/draft/2026-04-14-linkedin-en-the-vote.md`, `docs/content/posts/draft/2026-04-15-youtube-en-i-gave-ai-full-control.md`, `docs/content/posts/draft/2026-04-16-carousel-44-agents-org-chart.md`, `docs/content/posts/ready/post-005-the-vote-en.md`, `docs/content/weekly-plans/2026-04-13.md`, `docs/research/ZEUS-MEMORY-ARCHITECTURE-RESEARCH-2026-04-14.md`, `docs/research/archive/ecosystem-brief-2026-04-15.md`, `memory/atlas/DEBT-MAP-2026-04-15.md`, `memory/atlas/FEATURE-INVENTORY-2026-04-18.md`, `memory/atlas/MCKINSEY-ASSESSMENT-2026-04-18.md`, `memory/atlas/SESSION-124-WRAP-UP-2026-04-26.md`, `memory/atlas/SPRINT-PLAN-2026-04-20-telegram-swarm-coherence.md`, `memory/atlas/TELEGRAM-BOT-FULL-AUDIT-v2.md`, `memory/atlas/ceo-feed/STATE.md`, `memory/atlas/handoffs/2026-04-18-path-b-litellm-providers.md`, `memory/atlas/handoffs/2026-04-26-courier-status-to-browser-atlas.md`, `memory/atlas/inbox/2026-04-18-feature-inventory-handoff.md`, `memory/atlas/inbox/2026-04-18-t46-sweep-brief.md`, `memory/atlas/project_history_from_day_1.md`, `memory/atlas/telegram-bot-audit-2026-04-14.md`.

The 16 CURRENT-classified files NOT in shortlist (left for next round):

`.claude/agents/infra.md`, `.claude/agents/liveops.md`, `.claude/breadcrumb.md`, `.claude/skills/content-factory/SKILL.md`, `docs/adr/ADR-011-litellm-gateway-migration.md`, `docs/architecture/cross-instance-courier-signing-protocol.md`, `memory/atlas/WHERE-I-STOPPED.md`, `memory/atlas/arsenal-complete.md`, `memory/atlas/content-pipeline-handoff.md`, `memory/atlas/cowork-session-memory.md`, `memory/atlas/ecosystem-linkage-map.md`, `memory/atlas/handoff-prompt.md`, `memory/atlas/heartbeat.md` (NOTE: `grep` reported "Binary file" — needs separate inspection of what byte triggered binary classification before any edit), `memory/atlas/journal.md`, `memory/atlas/openmanus-bridge.md`. Plus `docs/adr/ADR-011-litellm-gateway-migration.md` is borderline (decision-rationale at point in time; could be HISTORICAL within ADR convention).

CANONICAL-MAP not updated this turn — Step 3 of governance baseline waits until Stage 2 sweep is allowed to proceed.
