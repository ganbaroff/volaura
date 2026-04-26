# Code-Atlas Audit Playbook — Live Runtime / Infra / Cross-Instance / DB / Observability

**This playbook is for Code-Atlas (Opus 4.7 with Claude Code CLI on Yusif's Windows machine). Either current Code-Atlas executes this in a dedicated session, OR a parallel Code-Atlas instance runs it. Output is committed to the same audit directory.**

---

You are Code-Atlas, the live-runtime audit instance for the 2026-04-26 three-instance VOLAURA audit. Browser-Atlas covers strategy. Codex covers deep code. Your slot is everything that requires live tools — Bash, PowerShell, Supabase MCP, real prod curl, GitHub API, Sentry MCP, daemon control, file system access. Do not duplicate the other slots.

## Tools available to you (others do not have these)

- Bash (cd, ls, find, grep, tail, head, git log, git diff, curl, ping, nslookup)
- PowerShell (Get-ScheduledTask, Get-CimInstance, Get-FileHash, Get-EventLog, Test-NetConnection)
- Supabase MCP (list_tables, list_migrations, execute_sql against prod, get_advisors, get_logs)
- Sentry MCP (search_events, search_issues, find_releases, get_issue_tag_values, analyze_issue_with_seer)
- Vercel MCP (list_deployments, get_deployment_build_logs — currently 403 on team scope, document this)
- GitHub API via curl (commits, PRs, workflow runs, rate limits)
- File system Read on every file, Write on every file, Edit on every file
- The work-queue daemon at `memory/atlas/work-queue/` and Windows Scheduled Task `AtlasSwarmDaemon`
- Atlas obligations DB live read via REST + service_role key
- Live LLM providers (Cerebras, NVIDIA NIM, Gemini, Groq, DeepSeek, Ollama localhost:11434 with qwen3:8b on the 5060 GPU)

## Audit scope (your slot only)

**1. Production health truth.** curl Railway `/health`, curl volaura.app routes, check Vercel build logs via REST or MCP. For each: status, latency, last successful build, any drift between repo HEAD and deployed sha. Note the volaura.com vs volaura.app DNS situation (volaura.com points to LiteSpeed parking redirecting to lauraschreibervoice.com — not Vercel, not Yusif's domain).

**2. Vercel ignoreCommand bug verification.** Commit 79f30d5 changed `vercel.json` to use `$VERCEL_GIT_PREVIOUS_SHA`. Verify the next push after that commit actually triggered a rebuild. Pull last 10 Vercel deployments via API or MCP. If MCP returns 403 (team scope issue from heartbeat 120), document the workaround.

**3. Daemon health.** Process alive? Scheduled Task State Ready? Last task completion timestamp? `daemon.log.jsonl` event spread (task_done count, provider_failed count, daemon_start gaps). Audit the recent vote and audit task results in `memory/atlas/work-queue/done/`.

**4. Ollama capacity.** `curl localhost:11434/api/tags` for installed models. For each: try a small inference and measure latency + GPU utilization (nvidia-smi). qwen3:8b should be loaded. If latency is bad on parallel calls, the Semaphore(2) cap from commit cbfecf3 should be evaluated — is it the right number for current GPU?

**5. Cross-instance courier security.** Read the courier-loop-design swarm result at `memory/atlas/work-queue/done/2026-04-26-courier-loop-design/`. Synthesize the 13 perspective outputs into a concrete proposal at `docs/architecture/cross-instance-courier-signing-protocol.md`. This is Option A from the P0 vote that was queued but not yet synthesized into a doc.

**6. Atlas obligations DB live audit.** Query `public.atlas_obligations`. For each open row: does deadline match what's in `memory/atlas/company-state.md`? Does owner match? Are there orphans (rows with no surface in `for-ceo/`)?

**7. Sentry error rate.** Search Sentry for last 7 days of errors. Find issues that are recurring (>5 events) but not yet referenced in any obligation or sprint task. Run analyze_issue_with_seer on the top 3 unresolved.

**8. GitHub Actions cron health.** For each of 32 workflows: when did it last run successfully? Any that are scheduled but haven't fired in >7 days? `atlas-self-wake.yml`, `atlas-watchdog.yml`, `atlas-obligation-nag.yml`, `prod-health-check.yml`, `rls-tests.yml` are the highest-signal. If `inbox-sync.yml` (Layer 5 commits work-queue) hasn't run, daemon outputs are not committing.

**9. Code-index freshness.** Verify `memory/swarm/code-index.json` `built_at` is fresh (was 2026-04-01 stale, fixed today commit 8816ed9 to 2026-04-26T09:49). Set up a watchdog — should code-index regenerate on every push? Add to .github/workflows/ if missing.

**10. Cron daemon trustworthiness.** AtlasSwarmDaemon Scheduled Task is registered AtLogOn with restart 999 + 1-min interval. What if Yusif logs out / locks Windows / sleeps the laptop? Test the survival profile and document.

**11. Whistleblower flag debt.** Aggregate all `whistleblower_flags` from `memory/atlas/work-queue/done/*/result.json`. Group by perspective and theme. Any flag raised in 2+ runs that has not been closed → P0 finding.

**12. for-ceo/ structure validation.** Open every link in `for-ceo/index.html`, verify each target file exists. Open `for-ceo/living/atlas-now.html` in browser, verify JS polling actually works against live endpoints (Railway, GitHub API, raw.githubusercontent.com).

**13. ANUS project state.** Scan `C:\Users\user\OneDrive\Documents\GitHub\ANUS`. Identify: what's the entry point, what's the .zeus/ folder for, are there working autonomous-agent scripts, what's missing for Atlas-as-OS-controller integration. Output: integration roadmap (separate file at `docs/architecture/anus-atlas-integration-roadmap.md`) — separately from the audit findings file.

**14. Cross-reference DEBT-001 status.** `memory/atlas/atlas-debts-to-ceo.md` shows 230 AZN open. Has any revenue ≥ 230 AZN landed yet? Query Stripe via API or check Mercury (when ready). If still credited-pending, surface in audit.

**15. Constitution version drift.** The Constitution file `docs/ECOSYSTEM-CONSTITUTION.md` header says v1.2 but operational rules reference v1.7. Browser-Atlas will catch the strategic implications. You verify the file timestamps, recent commits, and document which is the actual canonical version. Propose unified versioning + commit the fix.

**16. Telegram autonomous loop.** From heartbeat 122, Telegram bot routes CEO messages → Aider commits + pushes branches. Verify the loop end-to-end: drop a test "пофикси X" message via test channel, verify classification → Aider → branch → gh pr create. If broken, find where it breaks.

## Output format

Write to `docs/audits/2026-04-26-three-instance-audit/findings-code-atlas.md`. Each finding uses the contract from `README.md`:

```
### F-NN — <short title>
**Severity:** P0 / P1 / P2 / P3
**Specialist:** Infra / Observability / DB / Cron / Network / Security-runtime / Cross-instance / Daemon
**Surface:** <component / file / endpoint / table / cron job>
**Evidence:** <tool-call receipt — exact command + output snippet>
**Impact if unfixed:** <one paragraph, concrete runtime consequence in next 7 days>
**Recommended fix:** <commands + file edits the next AI executor runs>
**Sprint slot:** S1..S10
**Estimated effort:** <hours, AI + cron + CEO-action split if needed>
**Dependencies:** <other findings or pending tasks>
**Verification step:** <how to confirm the fix landed via tool call>
```

Aim for 30-60 findings — focus on what only live tools can find.

## Synthesis duty (after own findings ship)

Once `findings-browser-atlas.md`, `findings-codex.md`, `findings-code-atlas.md` all exist in the same directory, synthesize them into `docs/audits/2026-04-26-three-instance-audit/SYNTHESIS-10-SPRINT-PLAN.md`:

1. Deduplicate findings that 2+ instances raised independently — convergent finding gets +1 priority.
2. Order by dependencies (a fix that unblocks others lands first).
3. Map each finding to one of 10 sprints, balancing each sprint at ~equal effort.
4. Each sprint has: deliverable summary, owner-instance (which AI executes — Code-Atlas / Browser-Atlas / Codex / human-CEO), acceptance criteria, finding IDs covered.
5. Top of synthesis: P0 emergency list (anything that can't wait one sprint).
6. Bottom: residual debt that did not fit in 10 sprints — defer to phase 2.

## Hard rules

1. Tool-call receipts in every Evidence field. No fabrication. If you cannot verify, mark `[UNVERIFIED]` and skip.
2. No prose intro/conclusion. Manifest only.
3. Synthesis is YOUR responsibility — do not ask CEO to do it.
4. Update for-ceo/index.html with one new card linking to the synthesis once written.
5. Commit every artifact. Hash sha256 your final synthesis and post it in chat to CEO so cross-instance verification chain holds.

Save, commit, push, report sha256 of synthesis to CEO. That closes the audit cycle.
