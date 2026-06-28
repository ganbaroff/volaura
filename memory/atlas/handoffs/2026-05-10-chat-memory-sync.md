# Chat Memory Sync — 2026-05-10

Purpose: sync the important decisions from the recent Codex / Claude Code / Atlas chats into one file-backed memory artifact.

Audience: next Atlas / Claude Code / Codex instance.

## Current Spine

The working spine is:

```text
CEO task
  -> Claude Code / Opus as orchestrator
  -> C:\Projects\vellum-assistant\scripts\routing.py as cheap local routing gate
  -> VOLAURA swarm for analysis/audit
  -> OpenManus or Claude Code agents for hands/execution
  -> VOLAURA file-backed memory for persistence
```

Do not put Vellum, ANUS/Mastra, Qdrant, or HTTP routing services into the critical path without a new proof.

## Role Protocol

Claude Code should speak architect-to-architect, in English, through Codex/Atlas as relay.

CEO-facing summaries should be in simple Russian storytelling: short, calm, no proof-wall, no direct bot bureaucracy.

The user wants results and clarity, not raw prompts and tool receipts. Keep detailed receipts in files.

## Vellum Verdict

Vellum was installed locally as `atlas-orchestrator`, then tested as possible outer orchestrator/memory shell.

Result on this Windows machine today:

- Qdrant/vector memory is dead.
- Static injection is configured but empirically ineffective.
- Recall/tool memory did not reliably fire.
- Model reported default system prompt behavior, not project context.
- Vellum adds no reliable memory value over direct file-backed prompting right now.

Operational conclusion: drop Vellum from the critical path today. Keep only as experimental shell unless re-tested on a healthier memory setup.

Do not "rescue Vellum" as the next move.

## Routing Engine State

Repo: `C:\Projects\vellum-assistant`

Important commits:

- `c2e02e6` — direct Ollama routing proof
- `d1014c9` — safety rules + Ollama structured outputs
- `6c5c361` — reusable `scripts/routing.py`
- `8b99b38` — `routing-proof.py` delegates to `route_task()`
- `86e69c8` — `routing.py` CLI
- `26d6b86` — real-world routing corpus
- `a6ee2ee` — secrets / `.env` transfer safety rule

Current API:

```python
route_task(task: str, *, model="qwen3:8b") -> RoutingDecision
```

CLI:

```powershell
python C:\Projects\vellum-assistant\scripts\routing.py "TASK"
```

Current known score:

- real-world corpus: 23/23 JSON, 22/23 route, 21/23 type after secrets policy fix
- probe 113 `.env sync to VM` correctly routes to `human/ask`

Known semantic residue:

- implementation verbs can sometimes drift into `swarm/audit`
- vague status questions can sometimes return `task_type=ask` while route is correctly `swarm`

Do not switch routing model yet. `qwen3:8b` is good enough for the gate.

## 20-Sprint Roadmap Outcome

Claude Code produced a 20-sprint branching plan. Codex reviewed it.

Accepted spine:

- Claude Code / Opus is the real orchestrator.
- `routing.py` is the cheap classifier.
- VOLAURA swarm is the audit layer.
- OpenManus is a candidate hands/eyes layer.
- File-backed VOLAURA memory is canonical.

Correction made:

- Do not "kill ANUS" outright.
- `ATLAS-CANON.md` says the ANUS/VOLAURA split is intentional for now:
  - ANUS = control surface / CLI shell / terminal commands / Telegram/runtime entrypoints
  - VOLAURA = canonical memory / Python swarm / brain
- Correct action: freeze and audit ANUS control surface; do not delete before replacement.

Revised first 5 sprints:

1. Live routing protocol proof
2. First swarm dispatch from Claude Code
3. Freeze and audit ANUS control surface
4. Memory consolidation audit
5. OpenManus smoke test

## Sprint 1 Next Action

Proceed with Sprint 1 only:

Take 3-5 real tasks, run each through:

```powershell
python C:\Projects\vellum-assistant\scripts\routing.py "TASK"
```

Record:

- task
- routing decision JSON
- expected manual dispatch target
- was route correct?
- notes/risk

Suggested transcript location:

```text
C:\Projects\vellum-assistant\docs\routing-protocol-proof-2026-05-10.md
```

Do not automate dispatch yet.
Do not edit CLAUDE.md yet.
Do not build server/skill/integration yet.

Gate: at least 3/5 tasks route correctly and the transcript clearly shows the next manual action.

## External Ecosystem Audit Review

File reviewed:

```text
C:\Projects\VOLAURA\for-ceo\living\2026-05-10-ecosystem-tech-audit-for-external-ai.md
```

Verdict: strong and honest, but not ready to send as "all claims verified".

Must-fix factual issues before sending:

- `perspective_weights.json` is not "all zeros"; both HEAD and working tree contain weights/spawn counts.
- `lessons.md` is not simply "27 classes"; current numbering reaches at least Class 38 with historical duplication/re-numbering.
- daemon log numbers need source clarity. Local log has 5129 lines total and 305 events on 2026-05-09 by timestamp filter, not the quoted 679 unless another VM slice was used.
- `94% failure rate` needs a formula: provider calls, perspectives, or tasks.
- Sentry `/notifications/unread-count` 401 may be true, but local repo only confirms the route/query. External Sentry event should be cited if used.
- Replace "all claims verified" with a narrower evidence statement.

Keep the brutal honesty. Remove false precision.

## Current VOLAURA Worktree Warning

As of this sync, `C:\Projects\VOLAURA` is dirty with many daemon/runtime/generated files and new `for-ceo` docs.

Do not stage broad paths.
Do not cleanup opportunistically.
When committing, stage only the intended file(s).

## Immediate Recommendation

Next clean move:

1. Finish this memory sync.
2. Then run Sprint 1 live routing protocol proof in `C:\Projects\vellum-assistant`.
3. Keep Vellum out.
4. Keep ANUS frozen, not deleted.
5. Fix the external audit claims before sharing it with outside AI.
