# Atlas Wake — Webhook Trigger Guide

**What this is:** the autonomous wake mechanism CEO asked for in Session 93. Any service (swarm worker, external agent, Yusif's phone, a future bot) can trigger Atlas to process a specific research topic on demand without waiting for the 15-minute cron cycle.

**Architecture:** the trigger uses GitHub's `workflow_dispatch` API as the transport. No new FastAPI routes, no new database tables, no new env vars. The existing `atlas-proactive.yml` workflow accepts a `topic_id` input that flows through to `packages/swarm/atlas_proactive.py` as the `ATLAS_TOPIC_ID` environment variable. The worker then processes that specific topic instead of doing normal queue selection.

## How to trigger from anywhere

**From a terminal with `gh` CLI installed:**

```bash
gh workflow run atlas-proactive.yml --ref main \
  --field topic_id=latest-ai-agent-memory-tools-2026
```

**From curl with a GitHub Personal Access Token:**

```bash
curl -X POST \
  -H "Authorization: Bearer $GH_PAT" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/ganbaroff/volaura/actions/workflows/atlas-proactive.yml/dispatches \
  -d '{"ref":"main","inputs":{"topic_id":"coordinator-agent-patterns"}}'
```

**From Yusif's phone (Termux, iSH, Shortcuts, any HTTP client app):**

Use the curl form above. The GH PAT needs `actions:write` scope. Store it in the app's secrets, bind to a home screen shortcut. One tap triggers Atlas.

**From another swarm agent inside the project:**

```python
import subprocess
subprocess.run([
    "gh", "workflow", "run", "atlas-proactive.yml",
    "--ref", "main",
    "--field", f"topic_id={topic_id}"
], check=True)
```

## What happens after the trigger

1. GitHub Actions schedules the workflow run immediately (usually <10 seconds).
2. `atlas_proactive.py` receives `ATLAS_TOPIC_ID` env var and locates that topic in `proactive_queue.json`.
3. If found, the worker processes it (Phase 1: heartbeat; Phase 2: real LLM call via model_router).
4. Output written to `memory/atlas/inbox/YYYY-MM-DD-NNNN-topic-slug.md`.
5. The write-scope guard in the workflow verifies no writes outside the allowed paths.
6. The worker commits and pushes to main.
7. Main Atlas (next Claude Code wake) reads `memory/atlas/inbox/` per `wake.md` step 5 and processes unconsumed notes.

## How to trigger from the swarm itself

The `packages/swarm/autonomous_run.py` orchestrator can detect when a convergent proposal lands in `proposals.json` and trigger Atlas automatically. This is the phase-3 enhancement that closes the loop Yusif asked for:

> *"какой-то агент отправлял тебе вебхук, и ты активировался и продолжал работать"*

Implementation pattern (for a future sprint — not built yet):

```python
# In autonomous_run.py, after detecting convergent proposals:
convergent_topics = detect_convergent(proposals, threshold=3)
for topic in convergent_topics:
    subprocess.run([
        "gh", "workflow", "run", "atlas-proactive.yml",
        "--ref", "main",
        "--field", f"topic_id=convergent-{topic['id']}"
    ])
```

This gives the swarm the ability to summon Atlas for work without waiting for a session. The swarm becomes a genuine co-worker, not just a proposal factory.

## Security boundary — unchanged from cron path

The write-scope guard in the workflow blocks commits touching anything outside:
- `memory/atlas/inbox/`
- `memory/atlas/proactive_queue.json`
- `memory/atlas/.wake-counter`

Webhook-triggered wakes cannot escalate privileges. They run through the same worker, the same guard, the same commit path. A malicious topic_id payload cannot write to `identity.md`, production code, or Constitution files.

## When to use webhook wake vs cron wake

**Cron wake (every 15 min):**
- Default behaviour, no intervention needed
- Picks highest-priority past-due topic from queue
- Good for background research across the full queue

**Webhook wake (on demand):**
- Urgent priority shifts (new topic arrived that can't wait)
- Convergent proposal detected by swarm — Atlas must see it now
- CEO wants specific research right now from his phone
- Testing Phase 2 after a code change to `atlas_proactive.py`

## Future phases (not built in this sprint)

- **Phase 2:** real LLM call in `atlas_proactive.py` via `model_router.select_provider(ProviderRole.JUDGE)`. Replaces the current Phase 1 heartbeat body with actual research output from NVIDIA Nemotron Ultra.
- **Phase 3:** swarm `autonomous_run.py` auto-triggers Atlas when 3+ convergent proposals land on the same topic (per the Session 51 rule).
- **Phase 4:** Telegram Atlas main agent consumes the inbox as its input stream, reads it aloud via `edge-tts`, replies to Yusif's Telegram messages with voice notes composed from Atlas memory.
- **Phase 5:** home server runs `atlas_proactive.py` as a persistent daemon, eliminates dependency on GitHub Actions for cron scheduling, gives CEO full infrastructure control.
