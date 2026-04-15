# Recurring-symptoms watchdog — raw research notes

**Date:** 2026-04-15 · **Analyst:** Atlas · **Cap:** 25 min, 8 WebSearch passes
**Trigger:** INC-017 (Google OAuth silent 11d), Telegram webhook fix-of-fix chain, swarm archive cleanup breaking 5 workflows. Pattern = patches on symptoms, not root-cause removal.

**Constraints:** solo founder, pre-launch, ~1000 AZN cash, free-tier preferred, must coexist with VOLAURA stack (FastAPI + Supabase + Railway + Next.js + existing swarm Python).

---

## Research question 1 — Sentry recurring-exception / regression alerts

- **Sentry built-in regression detection** — fires automatically when a resolved issue sees new events in a *later release*. Prerequisite: every commit associated with a release. If "resolved via commit" lacks release tie, regression never fires. Stack-trace fingerprint is the dedup key. Env leakage can look like regression — fix with env-scoped fingerprint rule.
  - Source: https://develop.sentry.dev/backend/application-domains/grouping/
  - Source: https://sentry.zendesk.com/hc/en-us/articles/23158703560859-Issue-resolved-via-commit-message-is-not-marked-as-regressed
- **Sentry Seer (Autofix)** — AI layer on top. 3-step: root cause → solution → PR. Auto-triggers on issues with ≥10 events + high fixability score. Traces support added Apr 2025 for cross-service recurrences. $40/active-contributor/mo (on top of Team plan). Solo founder = $40/mo minimum → rejects budget.
  - Source: https://blog.sentry.io/sentry-ai-debugger-autofix-superpower-traces/
  - Source: https://docs.sentry.io/product/ai-in-sentry/seer/autofix/
- **GlitchTip (MIT, Sentry-API-compatible)** — 512MB RAM, 4 containers, self-hosted free. Has alerts for new issues, regressions, repeat errors (weaker than Sentry; issue #260 — project-level mute silences all). Drop-in SDK compatibility.
  - Source: https://glitchtip.com/
  - Source: https://news.ycombinator.com/item?id=36008564
- **Bugsink** — similar niche; explicitly markets per-project alerts for "new issue, regression, repeat error." Worth noting but less mature than GlitchTip.
  - Source: https://www.bugsink.com/blog/glitchtip-vs-sentry-vs-bugsink/

## Research question 2 — Incident platforms (incident.io / Rootly / FireHydrant / PagerDuty)

- **All three closed-source SaaS.** None has meaningful free tier for solo founder.
  - incident.io: from $15/user/mo, Pro $45/user/mo. AI SRE for RCA.
  - Rootly: ~$18/user/mo. Best AI RCA of the three. Closed-loop action-item tracking (Jira/Asana).
  - FireHydrant: $6,000/yr flat for Pro. AI only on Enterprise. Acquired by Freshworks Dec 2025 → now merging into Freshservice ITSM.
  - Source: https://incident.io/blog/incident-io-vs-firehydrant-vs-pagerduty-automated-postmortems-2025
  - Source: https://rootly.com/sre/choose-the-right-incident-platform-12-solutions-compared
- **OneUptime (open-source)** — blameless-postmortem workflow backed by OpenTelemetry traces. Free self-host. Pulls traces automatically on incident declaration.
  - Source: https://oneuptime.com/blog/post/2026-02-06-blameless-postmortem-opentelemetry-traces/view
- **Aurora by Arvo AI (Apache 2.0)** — AI SRE agent that traverses dependency graph + runbooks + past incidents to produce RCA + postmortem. No on-call, no Teams. Self-host + BYO LLM key.
  - Source: https://www.arvoai.ca/blog/firehydrant-alternative-open-source

## Research question 3 — LLM-over-logs / observability alerting

- **SigNoz (MIT + EE folder)** — OTel-native. Alerts on logs/metrics/traces. Anomaly detection. Exception monitoring auto for Py/Java/Ruby/JS. Operational cost: ClickHouse. Heavier than VOLAURA needs.
  - Source: https://github.com/SigNoz/signoz
- **OpenObserve** — lighter, Rust. Real-time + scheduled alerts, anomaly detection built-in. Early-adopter stage.
  - Source: https://openobserve.ai/docs/user-guide/alerts/alerts/
- **Honeycomb** — SaaS only. BubbleUp anomaly detection strongest in market but no free self-host.
- **Langfuse** — LLM-call observability, not error observability. Off-scope.

## Research question 4 — Culture/process patterns + tools demanding RCA on recurrence

- **Google SRE blameless-postmortem doctrine** — canon. Key clause: "subpar postmortems with incomplete action items make recurrence far more likely." Tool-agnostic.
  - Source: https://sre.google/sre-book/postmortem-culture/
- **Rootly's recurrence feature** — "All postmortems stored in centralized searchable platform → identify systemic patterns, track recurring issues." Useful framing but paid.
  - Source: https://rootly.com/sre/ai-generated-postmortems-rootlys-automated-rca-tool
- **No tool found** that mechanically *forces* RCA gate after N-recurrence threshold. This is a build-it-yourself space or wrap Rootly's action-item API.

## Research question 5 — "Fix-of-fix" detection / code-churn hotspots

- **No packaged GitHub Action exists** named "fix of fix detector." This is the biggest gap — clear green-field opportunity if built small.
- **CodeScene** — commercial hotspot analysis (churn × complexity). Free tier for OSS repos only. Exactly the visualisation we'd need for INC-017 class.
  - Source: https://codescene.io/docs/guides/technical/code-churn.html
- **Code Maat (Adam Tornhill, MIT)** — CodeScene's open-source predecessor. CLI VCS miner. `-a abs-churn`, `-a revisions`, `--temporal-period` for multi-commit patterns.
  - Source: https://github.com/adamtornhill/code-maat
- **PyDriller** — Python lib for git-history mining. Pair with `git log --since --grep=^fix` to detect repeated-fix files.
- **SZZ algorithm** (academic, 2005) — algorithm for identifying bug-introducing commits from bug-fix commits. Multiple open-source implementations exist. This IS the academic framing of "fix-of-fix archaeology."
- **Recipe (DIY, ~1 day build):**
  1. `tj-actions/changed-files` on push/PR → file list.
  2. Filter commit message `^(fix|hotfix|bugfix|INC-)`.
  3. For each changed file: `git log --since="60 days ago" --grep="^fix" --oneline -- <file>` → count.
  4. If count ≥ 3 → post PR comment + write to `memory/atlas/hotspots.jsonl`.
  5. Optional: block merge label "needs-RCA" until linked postmortem file exists.
  - Source: https://github.com/marketplace/actions/changed-files

## Research question 6 — Issue deduplication with root-cause clustering

- **IncidentFox (Apache 2.0)** — 3-layer alert correlation (temporal + topology + semantic), claims 85-95% noise reduction. Prophet-based anomaly detection. Auto-investigates in Slack threads. Most-match to CEO's brief.
  - Source: https://github.com/incidentfox/incidentfox
- **OpenSRE (Tracer-Cloud)** — framework to build your own AI SRE agents. Connects to Sentry/Grafana/Honeycomb/Loki. Scored synthetic RCA test harness.
  - Source: https://github.com/Tracer-Cloud/opensre
- **PyRCA (Salesforce)** — ML library. Metric-based RCA via Bayesian inference + causal graphs. Too heavy for pre-launch.
  - Source: https://github.com/salesforce/PyRCA
- **RCAEval** — benchmark + 15 reproducible baselines. Learn-only for us; useful to validate whatever we build.
  - Source: https://github.com/phamquiluan/RCAEval
- **awesome-failure-diagnosis** — curated reading list, 2024-25 papers (FSE, ASE, WWW, ICLR).
  - Source: https://github.com/phamquiluan/awesome-failure-diagnosis

## HN / Reddit / Dev.to scan

- No "we built recurring-bug watchdog" HN post surfaced. Space is crowded with incident tools, thin on "recurrence governance." Opportunity or irrelevance — leaning opportunity.
- GlitchTip HN thread (2023) still top reference for pragmatic self-hosters. Same advice holds 2025.

## Cost/fit matrix for VOLAURA (solo + ~1000 AZN + pre-launch)

| Tool             | Cost      | Self-host | Regression alert? | Recurrence RCA? | Install cost |
|------------------|-----------|-----------|-------------------|-----------------|--------------|
| Sentry free tier | $0 (5k ev/mo) | No    | Yes (native)      | Manual          | 1 hr         |
| Sentry + Seer    | $40/mo+   | No        | Yes               | AI-assisted     | 1 hr         |
| GlitchTip        | Hosting only | Yes    | Yes (weaker)      | Manual          | 1 day        |
| IncidentFox      | LLM tokens only | Yes | Indirect via alerts | Yes (AI RCA)  | 2-3 days     |
| OneUptime        | Hosting only | Yes    | Via OTel traces   | Blameless PM    | 2 days       |
| Code Maat + DIY  | $0        | Yes (CLI) | N/A               | Hotspot file-level | 1 day    |
| Rootly           | $18/u/mo  | No        | No                | Best commercial | 2 hr         |

## Decision shape

Sentry free tier already in our stack appetite. Gap isn't error capture — it's the *governance layer* that forces root-cause discipline when the same fingerprint/file recurs. That's two tiny pieces, not one tool: (a) "fix-of-fix" detector over git — greenfield DIY, 1 day; (b) Sentry regression → Telegram + auto-create `memory/atlas/incidents.md` stub + block merge label until RCA filed — Sentry webhook + GitHub Action, ~half day.

IncidentFox is the serious candidate if we ever want AI RCA without Sentry lock-in. But for pre-launch, it's over-scoped. LEARN-ONLY now, ABSORB-PARTIAL in 6 months.
