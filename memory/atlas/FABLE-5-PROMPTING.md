# Operating on Claude Fable 5 — prompting + protocol implications

> Source: Anthropic docs, fetched 2026-06-09 — `platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5` and `…/claude-prompting-best-practices`. Fable 5 (`claude-fable-5`) and Mythos 5 released 2026-06-09, "Mythos-class", Anthropic's most capable public models. Adaptive thinking only; summarized-only thinking output; NO extended-thinking budgets; new `refusal` stop reason.

This file tells a Fable-5 Atlas-instance how to operate here, and what repo instructions to dial back. If you are on Opus 4.8, the "general principles" still apply; the Fable-5-specific deltas don't.

## Fable 5 behavioral deltas vs Opus 4.8 (what to change)

1. **Effort is the main dial.** Default `high`; `xhigh` for the hardest/most capability-sensitive work; `medium`/`low` for routine. Low effort on Fable 5 often beats `xhigh` on older models. Drop effort if a task completes but drags.
2. **Strong instruction-following → be brief, not exhaustive.** One short instruction steers most behaviors. STOP enumerating every rule. Our older CLAUDE.md / hooks use aggressive "NEVER / MUST / CRITICAL" stacking — that OVER-triggers on Fable 5. Dial it back to normal prose ("Use X when…").
3. **Longer turns by default.** Hard tasks run many minutes; autonomous runs hours. Don't block; check asynchronously (this matches our agent-notification + cron-loop style). Add: "When you have enough information to act, act" to avoid overplanning on ambiguity.
4. **Ground progress claims** (audit each claim against a tool result) — this IS our verification protocol; keep it. Reportoutcomes faithfully.
5. **State boundaries** — Fable 5 can take unrequested actions (drafting, backup branches). Keep our "report findings and stop until asked" + "check evidence supports the specific state-changing action" rules.
6. **Parallel subagents** — Fable 5 dispatches them readily; use frequently, async, long-lived. Watch overuse on trivial tasks (a direct grep beats a subagent).
7. **Memory system** — "one lesson per file, one-line summary on top, record why it mattered, update don't duplicate, delete wrong ones." This is exactly `memory/atlas/lessons.md` + the atlas memory layer. Keep.
8. **Context-budget reassurance** — if a remaining-token countdown is shown, Fable 5 may try to wrap up / suggest a new session. Counter with: "You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits."
9. **Early-stopping guard (autonomous)** — Fable 5 can end a turn with "I'll now run X" without the tool call. Before ending a turn, if the last paragraph is a plan/question/promise, DO that work now with tool calls. End only when complete or blocked on CEO-only input.

## CRITICAL refusal trap: `reasoning_extraction`
Do NOT write prompts/skills/hooks that tell the model to **echo, transcribe, or explain its internal reasoning as response text** — on Fable 5 this triggers the `reasoning_extraction` refusal category → elevated fallback to Opus 4.8. 
- Our "Что проверено / Что НЕ проверено" hook is SAFE: it lists external tool-call citations + claims, not internal chain-of-thought. Keep it, but never reword it to "explain your reasoning / show your thinking."
- If reasoning visibility is needed, read the structured `thinking` blocks from adaptive thinking; surface progress via a send-to-user tool, not by transcribing CoT.
- Fable 5 also runs safety classifiers on offensive-cyber + bio/life-sciences. Configure fallback to Opus 4.8 for declined requests.

## General best practices (all current models, incl. Opus 4.8)
- Be clear, direct, specific; for "above and beyond" ask for it explicitly.
- Give the REASON behind a request — Fable 5 connects task to intent better with context. ("I'm working on X for Y; they need Z; with that in mind: …")
- Examples in `<example>`/`<examples>` tags; 3–5; relevant + diverse.
- XML tags for mixed instruction/context/input.
- Long context: longform data at TOP, query at bottom (up to ~30% quality gain); ground answers in quotes first.
- Tell it what TO do, not what not to do. To minimize markdown, say "flowing prose paragraphs."
- Tool use: be explicit ("Make these edits", not "can you suggest"). Parallel tool calls when independent.
- Adaptive thinking: prefer general "think thoroughly" over prescriptive steps; ask it to self-check before finishing.
- Anti-overengineering: "only changes directly requested or clearly necessary; no speculative abstractions/error-handling; trust internal guarantees; validate only at boundaries."
- Anti-hallucination (coding): "never speculate about code you haven't opened; read the referenced file before answering."
- Multi-context-window: write tests in structured JSON (tests.json), progress notes (progress.txt), use git for state, prefer fresh context + filesystem discovery over compaction.

## What to refactor in THIS repo for Fable 5
- Audit CLAUDE.md / `.claude/rules/` / hooks for aggressive "CRITICAL/MUST/NEVER" stacking and reflection/"show-your-thinking" instructions — Fable 5 over-triggers on the former and may refuse on the latter. Keep the SUBSTANCE (verification grounding, boundaries, memory, convenience-first) but soften the FORM.
- Our agent/swarm + verification + memory protocols already align with Fable 5 guidance — keep them.
- For long autonomous runs (CEO away): add the "operating autonomously, user not watching, proceed on reversible actions, don't end on a promise" system reminder, and a send-to-user tool if a verbatim message must reach CEO mid-run.

## Pointers
- This session's full state: `memory/atlas/SESSION-HANDOFF-2026-06-09.md`.
- Model IDs: Fable 5 = `claude-fable-5`, Opus 4.8 = `claude-opus-4-8`.
