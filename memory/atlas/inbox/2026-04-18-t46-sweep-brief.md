# T46 — 44-agents correction sweep brief

Authored 2026-04-18 13:15 Baku by Opus Atlas for Sonnet worker.

## Ground truth (verified, do not re-verify)

- `packages/swarm/autonomous_run.PERSPECTIVES` has **exactly 13 entries**: Scaling Engineer, Security Auditor, Product Strategist, Code Quality Engineer, Ecosystem Auditor (wave 0); Risk Manager, Readiness Manager, Cultural Intelligence, Communications Strategist (wave 1); Assessment Science, Legal Advisor, PR & Media (wave 2); CTO Watchdog (wave 3).
- Skill markdowns: **17** in `packages/swarm/**/*.md`, **101** in `memory/swarm/skills/**/*.md` → ~118 total.
- **0** files in `packages/swarm/agents/` (directory empty).
- Lie source: Session 93 `memory/atlas/identity.md` drift. Already self-corrected Session 112 per heartbeat.

## Replacement

Replace any variant of "44 Python agents" / "44 agents" / "44 specialised agents" with the accurate structure.

- Primary EN: **"13 specialised perspectives"** (runtime: `packages/swarm/autonomous_run.PERSPECTIVES`) **plus ~118 skill modules**
- Short EN: **"13 perspectives + ~118 skill modules"**
- RU: **"13 специализированных ролей (перспектив) и библиотека из ~118 skill-модулей"** (or natural rephrase)
- AZ: keep AZ, translate the facts: "13 ixtisaslaşdırılmış perspektiv və ~118 skill-modul kitabxanası"

Minimum edit per occurrence. Don't restructure. Don't add explanation prose. If surrounding paragraph depends on the inflated figure, narrow the claim rather than restoring unverified adjacent claims.

## BUCKET A — EDIT these paths

```
docs/content/posts/draft/2026-04-16-carousel-44-agents-org-chart.md
docs/content/posts/draft/2026-04-17-linkedin-az-44-agentla.md
docs/content/posts/draft/2026-04-15-youtube-en-i-gave-ai-full-control.md
docs/content/posts/draft/2026-04-14-linkedin-en-the-vote.md
docs/content/posts/ready/post-005-the-vote-en.md
docs/content/weekly-plans/2026-04-13.md
docs/content/TRACKER.md
docs/pr/WUF13-PRESS-BRIEF.md
docs/GITA-GRANT-APPLICATION-2026.md
docs/BRAIN.md
docs/CONSTITUTION_AI_SWARM.md
docs/SWOT-ANALYSIS-2026-04-06.md
docs/design/MANIFESTO-GAP-ANALYSIS.md
docs/correspondence/atlas-to-perplexity-2026-04-12.md
docs/research/ZEUS-MEMORY-ARCHITECTURE-RESEARCH-2026-04-14.md
AGENTS.md
ecosystem-map.html
memory/atlas/identity.md
memory/atlas/project_v0laura_vision.md
memory/atlas/wake.md
memory/atlas/WHERE-I-STOPPED.md
memory/atlas/arsenal-complete.md
memory/atlas/cowork-session-memory.md
memory/atlas/content-pipeline-handoff.md
memory/atlas/ecosystem-linkage-map.md
memory/atlas/proactive_queue.json
memory/atlas/relationships.md
memory/atlas/openmanus-bridge.md
memory/atlas/MCKINSEY-ASSESSMENT-2026-04-18.md
memory/atlas/project_history_from_day_1.md
memory/people/yusif-complete-profile-v1.md
memory/swarm/skills/atlas.md
memory/swarm/team-structure.md
memory/swarm/shared-context.md
memory/swarm/agent-roster.md
memory/swarm/research/session-93-7-parallel-research-2026-04-12.md
memory/swarm/research/observability-backend-decision-2026-04-12.md
memory/swarm/daily-health-log.md
packages/atlas-memory/identity/relationships.md
packages/swarm/prompt_modules/architecture_state.md
packages/swarm/telegram_ambassador.py
packages/remotion/src/data/carousel-2026-04-13.ts
.claude/skills/content-factory/SKILL.md
.claude/agents/AGENTS-INDEX.md
```

## BUCKET B — SKIP (preserve as drift evidence)

```
docs/archive/**
memory/atlas/transcripts/**
memory/atlas/auto-memory-snapshot-2026-04-17/**
memory/atlas/DEBT-MAP-2026-04-15.md
memory/atlas/training-dataset-v1.jsonl
memory/atlas/heartbeat.md
memory/atlas/FEATURE-INVENTORY-2026-04-18.md
memory/atlas/inbox/**
memory/atlas/SESSION-112-WRAP-UP.md
memory/atlas/ceo-feed/**
docs/audits/STRANGE-V2-AUDIT-2026-04-18.html
docs/research/archive/**
```

## Rules

1. Fact-based. No new claims beyond 13 / ~118 / 0.
2. Preserve language (RU/EN/AZ), voice, file structure.
3. JSON / TS / Python → edit string literals + comments only, verify syntax.
4. Idempotent — skip if already correct.
5. One pass, no retries on failed edits.
6. No new files. No git commits (index corrupted separately).
7. On filenames themselves containing "44-agents" — DO NOT rename the file (git history). Only edit content.

## Report format

Return structured report:
- Edited (N): file — what changed
- Skipped-already-correct (N)
- Skipped-archive (N)
- Failures (N): file — reason
- Summary: total files touched, total replacements, residual 44-agents claims in active docs (target 0)
