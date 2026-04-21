# Atlas Handoffs — CEO-courier protocol

## Purpose
Self-contained prompts that Atlas-Cowork writes for execution by:
- **Claude Code CLI** (Terminal-Atlas on Windows/WSL, same filesystem as Cowork)
- **Terminal-Atlas Ollama** (local model, no Anthropic tokens)
- **NotebookLM** (research, no code execution)

CEO reads the handoff file and pastes into the target tool. Cowork-Atlas stays the coordinator.

## File naming
`YYYY-MM-DD-<slug>.md`

One handoff = one destination tool = one goal. No mixed prompts.

## Required sections
1. **TARGET TOOL** — which CLI/model receives this
2. **GOAL** — one sentence, outcome-oriented
3. **CONTEXT** — everything the target tool needs that is NOT in its training data (paths, prior decisions, constraints)
4. **NON-GOALS** — what NOT to touch (existing files, behaviors, skills)
5. **ACCEPTANCE** — how to verify it worked (file list, grep result, test output)
6. **RETURN CONTRACT** — what Atlas-Cowork needs back (commit hash, diff summary, errors if any)

## Why this exists
Session 120 audit found: Cowork-Atlas was burning Opus tokens on hands-work (WebSearch loops, file writes) that Sonnet or Claude Code CLI ships identically for a fraction of the cost. The delegation-first gate requires a handoff file, not a verbal "please run this for me" — because words evaporate and CEO loses the receipt.

## Close the loop
After CEO runs the handoff and returns the result, Atlas-Cowork:
1. Reads the returned artifact (commit, file diff, log)
2. Reviews for correctness
3. Appends CLOSED section to the handoff file with date + outcome
4. Updates the relevant TASK via TaskUpdate
5. Moves handoff file to `memory/atlas/handoffs/closed/` if the directory exists, else leaves in place with CLOSED marker
