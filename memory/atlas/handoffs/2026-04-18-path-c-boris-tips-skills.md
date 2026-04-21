# Handoff — Path C: Boris 6 tips + awesome-claude-code skills install

## TARGET TOOL
Claude Code CLI (Terminal-Atlas on Windows/WSL). Same filesystem as Cowork. Run inside `C:/Projects/VOLAURA` or wherever the working copy sits locally.

## GOAL
Install Boris Cherny's 6 tips (session config + slash commands) and curate a small set of ready-made skills/commands from the awesome-claude-code ecosystem — without touching the 7 existing skills in `.claude/skills/`.

## CONTEXT

### Repo state (verified 2026-04-18 by Cowork-Atlas)
- `.claude/skills/` has 7 skills: `accelerator-grant-searcher`, `content-factory`, `product-strategy`, `promotion-agency`, `social-post`, `startup-registration-finder`, `video-script`. **DO NOT MODIFY OR DELETE any of them.**
- `.claude/commands/` directory does NOT exist. Greenfield.
- `.claude/agents/` has a large existing inventory (atlas.md, code-reviewer.md, security-auditor.md, etc.). **DO NOT MODIFY or overwrite any agent file.**
- `.claude/rules/` is the authoritative constitution. Do NOT modify existing rule files; only APPEND new ones if strictly necessary.

### Decision context
- Doctor Strange v2 protocol, 2026-04-18, chose this path FIRST over Beehave audit (blocked on Godot repo access) and LiteLLM migration (high refactor risk).
- External model validation: Cerebras Qwen3-235B ranked C > A > B on zero-risk + force-multiplier grounds.
- External model adversarial (DeepSeek) raised "auto-mode overwrites skills" as failure mode 1 — refuted by inspection (Boris tips are session/CLI config, not filesystem mutations). This handoff MUST preserve that invariant.

### Ecosystem constraints (overriding)
- **5 Foundation Laws** (see `docs/ECOSYSTEM-CONSTITUTION.md` v1.7): no red, energy adaptation, shame-free language, animation safety, one primary CTA.
- **Atlas Operating Principles** (see `.claude/rules/atlas-operating-principles.md`): update-don't-create, sonnet-for-hands, delegation-first, root-cause-over-symptom, proactive-scan gate.
- Any new skill/command must NOT violate these.

## TASKS

### T1. Verify source of Boris 6 tips (re-fetch, don't trust memory)
- Primary URL candidate: `https://github.com/shanraisshan/claude-code-best-practice/blob/main/tips/claude-boris-6-tips-16-apr-26.md`
- Fetch the raw markdown (`raw.githubusercontent.com` path) and save to `docs/research/claude-code/boris-6-tips-raw.md` with a header `source: <url>, fetched: <date>`.
- If URL is 404 or content differs from the summary below, STOP and report. Do not guess.
- Expected summary (for comparison only, authoritative source is the raw file):
  1. Auto-mode permissions — session-scoped allowlist of safe operations
  2. `/focus` slash command — context-window scoping
  3. Effort tuning — `low | medium | high | xhigh | max` runtime flag
  4. Verification multiplier — run tests/builds 2–3× for stability
  5. Skill invocation pattern — read-only skill calls
  6. Plan-mode — explicit approval before execute

### T2. Create `.claude/commands/` directory with 4 curated slash commands
Do NOT copy blindly from awesome-claude-code. Pick commands that are (a) general-purpose, (b) non-destructive, (c) align with ecosystem-design-gate and guardrails.

Suggested 4 (choose based on what Boris's raw file actually specifies):
- `/focus` — scope context to a specified feature/directory (read-only, informational)
- `/verify` — run `tsc -b && pytest -q && playwright test --project=chromium` — STOP and report on any failure; do not auto-fix
- `/adr` — prompt for ADR creation using `engineering:architecture` skill
- `/strange` — invoke Doctor Strange v2 sequence (min 2 external-model calls before any recommendation) with template scaffold

Each command file: `.claude/commands/<name>.md`. Header must include `description:` frontmatter (shown in slash-command autocomplete). Body is the system prompt appended when the command is invoked.

### T3. Review awesome-claude-code for skill overlap (curation, not bulk install)
Catalogs to skim (do NOT clone into repo):
- `hesreallyhim/awesome-claude-code`
- `ccplugins/awesome-claude-code-plugins`
- `ComposioHQ/awesome-claude-plugins`

Identify skills that genuinely fill gaps vs. our 7 existing + 30+ agents + 8 engineering/design plugin skills. Report the gap list with rationale. **Do NOT install anything yet** — produce a shortlist (≤5 items) with one-line justification each, and wait for Atlas-Cowork review.

### T4. Append one rule (if and only if Boris's raw file introduces a genuinely new protocol)
If Boris's file contains a protocol not covered by existing `.claude/rules/`, append it to `.claude/rules/atlas-operating-principles.md` under a new section. **Do NOT create a new rule file.** This honors the update-don't-create directive.

### T5. Produce verification output
Run in order and capture output:
```bash
ls .claude/commands/
ls .claude/skills/
wc -l .claude/rules/atlas-operating-principles.md
git status
git diff --stat
```

## NON-GOALS
- Do NOT touch `.claude/skills/*` files (7 existing must survive untouched).
- Do NOT touch `.claude/agents/*` files.
- Do NOT modify `.claude/rules/atlas-operating-principles.md` unless T4 condition is met (genuinely new protocol from Boris raw).
- Do NOT install any package to `package.json` or `pyproject.toml`.
- Do NOT run `npm install`, `pip install`, or any package manager action.
- Do NOT push to `origin/main`. Local commit only.
- Do NOT enable any auto-mode permission that grants write access to untrusted paths.

## ACCEPTANCE
All of the following must be true:
1. `docs/research/claude-code/boris-6-tips-raw.md` exists with source URL + fetch timestamp.
2. `.claude/commands/` exists with exactly 4 new `.md` files, each with frontmatter `description:` field.
3. `.claude/skills/` still contains exactly 7 directories, unchanged (compare `git diff --stat .claude/skills/` — should be empty).
4. `git status` shows only additions under `docs/research/claude-code/` and `.claude/commands/` (and possibly one appended section in `.claude/rules/atlas-operating-principles.md`).
5. A single local commit with message `feat(claude-code): path C — boris tips + commands scaffold`.

## RETURN CONTRACT
Reply in this exact format:

```
COMMIT: <sha>
FILES ADDED: <count>
FILES MODIFIED: <count>
BORIS RAW FETCHED: <yes | no, with reason>
COMMANDS CREATED: <list>
AWESOME SHORTLIST: <≤5 items, one line each>
RULE APPENDED: <yes | no, with heading>
VERIFICATION OUTPUT: <paste>
BLOCKERS: <list, or "none">
```

## BLOCKER ESCALATION
If ANY of the below happens, STOP and write `memory/atlas/inbox/<date>-path-c-blocked.md` with details, then reply with `BLOCKED: <reason>`:
- Boris URL 404s or returns different content
- `.claude/skills/` would be modified by any step
- `git status` shows unexpected modifications
- Any external install is prompted for
