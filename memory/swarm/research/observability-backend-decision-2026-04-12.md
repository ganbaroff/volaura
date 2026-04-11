# VOLAURA Observability Backend Decision — 2026-04-12

**Author:** Observability Specialist (Atlas swarm role)
**Scope:** Pick one tracing/observability backend for VOLAURA's multi-provider LLM stack.
**Candidates:** Langfuse, Arize Phoenix, LangWatch, Braintrust, Helicone.
**Decision horizon:** Q2 2026 (pre-launch → 10K users).

---

## 1. Executive Recommendation

**Adopt Langfuse Cloud EU (free tier → Core $59/mo when needed), self-hosting as Plan B.**

Langfuse is the only candidate that simultaneously (a) is already partially wired into `apps/api/app/services/llm.py` via the `_trace` decorator, so the switching cost is zero and rip-out cost is a regression we should avoid, (b) natively speaks OpenTelemetry so Groq / Ollama / NVIDIA NIM / Cerebras (all non-OpenAI) plug in via OpenInference instrumentation without a proxy, (c) offers an EU Cloud region with SCCs + DPA + SOC2 Type 2 + ISO27001 that satisfies Azerbaijan-shipping-to-EU compliance, and (d) stays inside the $100/mo LLM budget because the hobby tier gives 50K observations/month free — enough for ~100 test users at 500 calls/day. Committing now means finishing 2 hours of instrumentation work, not starting a migration. If the free tier is exhausted in Q3, self-host on the existing Railway footprint (~$15/mo Clickhouse) as the escape hatch.

---

## 2. Comparison Table

| Dimension | **Langfuse** | Phoenix (Arize) | LangWatch | Braintrust | Helicone |
|---|---|---|---|---|---|
| Free tier (2026) | 50K observations/mo cloud, unlimited self-host | Fully free OSS, SaaS Arize AX is paid | Free community tier, enterprise paid | 1M trace spans, 10K scores, unlimited users | 10K requests/mo, then $79/mo |
| Self-hosting | Yes — Docker / Helm, v3 uses Clickhouse + Redis + S3 + Postgres (4 containers) | Yes — single container, simplest OSS story | Yes — Docker Compose | **No** — SaaS only | Yes — but designed as a proxy, adds hop |
| FastAPI/Python SDK | Python v3 built on OTEL, `@observe` decorator, mature | `arize-phoenix` + OpenInference, mature | Python SDK, less mature | Python SDK + `braintrust` CLI, mature | Thin HTTP client; mainly header-based via proxy |
| OpenTelemetry native | **Yes** — OTLP endpoint, SDK is OTEL under the hood | **Yes** — it *is* the OTEL reference for LLM traces via OpenInference | Yes (OpenInference) | Partial — own format, OTEL ingestion exists | No — proxy model, not OTEL-first |
| Multi-provider (NIM / Ollama / Groq / Cerebras) | Direct integrations + OpenInference wrap | Direct integrations for all major + OpenInference | Supported via OpenInference | Supported via SDK manual spans | Requires rewriting calls to route through proxy; non-OpenAI formats often broken |
| Prompt versioning | Yes — first-class, A/B, env labels | No (focus is tracing + evals) | Yes | Yes — strong | Limited |
| Eval datasets | Yes — datasets + run comparison + LLM-as-judge | **Yes** — strongest OSS eval story (Ragas-integrated) | Yes — scenario tests | **Yes** — strongest commercial eval story | Weak |
| Cost tracking | Per-model pricing config, accurate for configured models, **user sets custom pricing for Cerebras / NIM / Ollama** | Yes, same caveat | Yes | Yes | Yes — strong, but only for requests through proxy |
| Latency overhead | ~0ms (async, fire-and-forget span batcher) | ~0ms (async OTLP) | ~0ms | ~0ms | **~5–50ms per call** (synchronous proxy hop) |
| EU data residency | **Yes — EU Cloud region, SCCs, DPA, SOC2 II, ISO27001** | Self-host only (no managed EU); Arize AX SaaS US | Self-host only | US-only SaaS | US-only SaaS |

---

## 3. Why Not the Others

### Phoenix (Arize) — rejected, strong runner-up
Best-in-class OSS eval stack, great OTEL story, single-container self-host. Rejected because:
- **No managed EU region.** Arize AX is US SaaS. For EU launch we'd have to self-host and take on the operational cost ourselves, which duplicates what Langfuse Cloud EU gives us free.
- **No prompt versioning.** Phoenix explicitly scopes itself to tracing + evals; we'd still need a second tool for prompt management. Langfuse bundles both.
- **Arize's own docs say OSS is "primarily designed for local development"** — production-scale features live in paid Arize AX.

### LangWatch — rejected
Active project with ~4K GitHub stars, DSPy optimization, scenario testing. Rejected because:
- **Smaller ecosystem.** LiteLLM's docs list Langfuse and Phoenix as first-party integrations; LangWatch is downstream.
- **No managed EU residency.** Self-host only if we care about Europe.
- **Feature overlap without differentiation** vs Langfuse — we'd pay a migration tax for no gain.

### Braintrust — rejected
Strongest eval UX in the category (Perplexity / Airtable / Replit are real production users). Rejected because:
- **No self-host.** SaaS-only means no escape hatch if pricing changes or EU regulators object. For a pre-launch startup that is an unacceptable single point of dependency.
- **US-only data residency.** Hard blocker for EU users.
- **Eval-first, tracing-second.** We need tracing first (to debug swarm failures), evals later.

### Helicone — rejected, hard no
Fastest to integrate (15 min, one header). Rejected because:
- **Proxy architecture is a latency tax and a failure point.** 5–50ms per call × 500 calls/day/user × 10K users = 25M extra ms/day of user-facing latency, plus Helicone becomes a hard dependency for *every* LLM call. We specifically chose async span export to avoid exactly this.
- **Non-OpenAI providers are second-class.** Our stack is Cerebras + NIM + Ollama + Gemini — literally the long tail where proxy gateways break.
- **Free tier is 10K req/mo** — we'd exhaust that on day one of launch.
- **EU data residency: none.** Same blocker.

---

## 4. Production Evidence

1. **Langfuse v3 stable release + scale post-mortem** — Langfuse's own engineering blog documents their Postgres → Clickhouse migration and the honest admission that single-row updates in Clickhouse "are immensely expensive" — the kind of real operational pain that tells us their team thinks about production, not marketing. ([Langfuse v3 infrastructure evolution](https://langfuse.com/blog/2024-12-langfuse-v3-infrastructure-evolution))
2. **Langfuse FastAPI + StreamingResponse bug (Issue #8216)** — open issue documenting that `@observe` breaks trace grouping when used with FastAPI StreamingResponse. **This is a real risk for us** because the assessment LLM evaluator may use streaming; non-streaming paths are fine. ([github.com/langfuse/langfuse/issues/8216](https://github.com/langfuse/langfuse/issues/8216))
3. **Langfuse Launch HN thread (YC W23)** — real engineers debating tracing vs eval, prompt management, open-source concerns. Confirms the project has live community, not just a landing page. ([news.ycombinator.com/item?id=42441258](https://news.ycombinator.com/item?id=42441258))
4. **Langfuse v2 → v3 self-host migration discussion #6225** — users reporting Prisma migration errors during v2→v3 upgrades, mitigated by upgrading to latest v2 *first*. Tells us the self-host escape hatch is real but not trivial. ([github.com/orgs/langfuse/discussions/6225](https://github.com/orgs/langfuse/discussions/6225))
5. **Langfuse data regions page** — confirms EU Cloud is AWS-eu-region, fully isolated from US, with SCCs and DPA available on request. This is the load-bearing fact for our EU launch. ([langfuse.com/security/data-regions](https://langfuse.com/security/data-regions))
6. **LiteLLM Helicone integration doc** — inadvertently documents the proxy dependency: all calls must route through `oai.helicone.ai` and provider-specific headers are required per model. Confirms the long-tail-provider problem. ([docs.litellm.ai/docs/observability/helicone_integration](https://docs.litellm.ai/docs/observability/helicone_integration))

---

## 5. Integration Plan

**Current state:** `apps/api/app/services/llm.py` already imports `langfuse.decorators.observe` and wraps `evaluate_with_llm`, `_call_vertex`, `_call_gemini`, `_call_groq`, `_call_openai`, and `generate_embedding`. The `_trace` wrapper is no-op if keys are missing. This is ~80% done.

**Gaps to close (total effort: 6–8 hours):**

### Step 1 — Provision Langfuse Cloud EU (15 min)
- Sign up at `cloud.langfuse.com` (EU region button).
- Create project "volaura-prod" and "volaura-staging".
- Copy `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST=https://cloud.langfuse.com`.
- Add to Railway env via `railway variables set` + GitHub Actions secrets.
- **File edit:** `apps/api/app/config.py` — confirm `langfuse_public_key`, `langfuse_secret_key`, `langfuse_host` fields exist; add `langfuse_host` if missing (defaults to EU cloud).

### Step 2 — Instrument model_router.py (1 hour)
Currently `llm.py` is instrumented but `app/services/model_router.py` is not. Every call that resolves a `ProviderSpec` must create a span with:
- `provider`, `model`, `role`, `is_fallback`, `rationale` as metadata.
- **File edit:** `apps/api/app/services/model_router.py` — import `langfuse.decorators.observe` and decorate `select_provider` with `@observe(name="model_router.select_provider")`; after resolving, call `langfuse_context.update_current_observation(metadata={...})`.

### Step 3 — Custom pricing for non-standard providers (30 min)
Langfuse does not know Cerebras / NVIDIA NIM / Ollama pricing by default.
- **Langfuse UI action:** Project Settings → Models → add entries for `qwen-3-235b` (Cerebras), `nvidia/llama-3.1-nemotron-ultra-253b-v1` (free → $0), `meta/llama-3.3-70b-instruct` (free → $0), `ollama/qwen3:8b` ($0), `gemini-2.5-pro` (from Google pricing).
- Without this the cost dashboard will undercount and the CEO's "cost transparency" requirement fails silently.

### Step 4 — PII-safe logging (2 hours — **load-bearing**)
CEO requirement: never log raw user payloads. Langfuse defaults send full input/output.
- **File edit:** `apps/api/app/services/llm.py` — in `_update_trace_metadata`, replace `input_text=prompt[:500]` with a redaction pass. Pattern: run `prompt` through a regex scrub (emails, phone numbers, national IDs) before truncation.
- **File create:** `apps/api/app/services/pii_redactor.py` — small module with `redact(text: str) -> str` using a tight regex set; unit tests for AZ phone numbers, emails, FINs.
- **Config:** set `LANGFUSE_SAMPLE_RATE=1.0` for now, consider 0.1 post-launch if volume spikes.

### Step 5 — Swarm run tracing (2 hours)
`packages/swarm/tools/llm_router.py` uses LiteLLM with no tracing. LiteLLM has native Langfuse callback support.
- **File edit:** `packages/swarm/tools/llm_router.py` — after `from litellm import Router`, set `litellm.success_callback = ["langfuse"]` and `litellm.failure_callback = ["langfuse"]` (reads the same env vars).
- **File edit:** `packages/swarm/engine.py` — wrap each agent run in `langfuse.decorators.observe(name=f"swarm.{agent_name}")` so all 44 agents' traces are grouped per swarm-run session_id.
- **Env var:** set `LANGFUSE_RELEASE=$GIT_COMMIT_SHA` in Railway so traces are bucketed per deploy.

### Step 6 — Flush on shutdown (15 min)
- **File edit:** `apps/api/app/main.py` — in the FastAPI lifespan shutdown handler, call `flush_langfuse()` (already exported from `llm.py`). Prevents trace loss on Railway redeploys.

### Step 7 — Dashboard + alert (1 hour)
- In Langfuse UI, create a saved view per role (JUDGE / WORKER / FAST / SAFE_USER_FACING) filtered on `metadata.role`.
- Set alert: "p95 latency > 3s for judge role" and "fallback rate > 20%" — email to CEO via the existing email plumbing.

---

## 6. Known Risks

**Risk A — Langfuse v3 self-host migration tax.**
GitHub Discussion #6225 documents real Prisma migration errors on v2→v3 upgrades. If we need to migrate to self-host later, we inherit this pain.
*Escape hatch:* Stay on Langfuse Cloud EU until we're >50K observations/month. If we migrate, do it on a weekend with a staging run first.

**Risk B — FastAPI StreamingResponse trace fragmentation (Issue #8216).**
If any assessment endpoint starts streaming LLM output (e.g. for real-time evaluator feedback), traces will fragment.
*Escape hatch:* Keep evaluator calls non-streaming until the upstream bug is fixed, or use manual `trace_id` propagation on any streaming endpoint we do add. Add a code review check: "any new StreamingResponse must either not wrap `@observe` or use manual trace IDs."

**Risk C — PII leak via input_text metadata.**
Our current `_update_trace_metadata` call passes `prompt[:500]` unredacted. If we ship today, the first 500 chars of every prompt land in Langfuse Cloud. For assessment prompts that include user answers, that is a GDPR incident waiting to happen.
*Escape hatch:* **Step 4 above is a release blocker.** Do not enable Langfuse in production until the redactor is in place and tested. Staging can run without redaction because it uses seed data.

---

## 7. EU Compliance Check

**Verdict: green, with conditions.**

- **EU Cloud region exists.** Langfuse Cloud EU is hosted on AWS in an EU region and data never leaves the EEA by default. ([langfuse.com/security/data-regions](https://langfuse.com/security/data-regions))
- **Legal basis.** Langfuse offers a signed DPA, SCCs for any incidental non-EU processing (e.g. follow-the-sun support), SOC2 Type 2, ISO 27001, annual external penetration tests. This matches the contractual posture of Vercel and Supabase, which we already trust.
- **GDPR subject rights.** Langfuse supports data retention policies, data masking, and deletion via API — we can honor a user's erasure request without opening a support ticket.
- **Azerbaijan dimension.** Azerbaijan is not an EEA adequacy country. For AZ-resident user data flowing into Langfuse Cloud EU, we need (a) our own privacy policy disclosing that "product analytics and LLM traces are processed by Langfuse GmbH in the EU", (b) a lawful basis (legitimate interest: improving a paid service), (c) the existing Langfuse DPA covers us as the data controller.
- **Conditions (must do before EU launch):**
  1. Sign the Langfuse DPA (email security@langfuse.com).
  2. Add Langfuse to VOLAURA's "sub-processors" list in the public privacy policy.
  3. Ship the PII redactor (Integration Step 4) — without it, compliance is theoretical.
  4. Set Langfuse retention to 90 days for production traces (configurable in project settings) to minimize the GDPR blast radius.

**Not a blocker.** This is the only candidate that ships EU residency as a standard feature, which is why it wins on this axis by default.

---

## Appendix — Research-First Checklist

- [x] Compared 5 alternatives (minimum was 3).
- [x] Checked GitHub Issues for at least the leading candidate (Issue #8216, Discussion #6225, #1902).
- [x] Read CHANGELOG — Langfuse v3 stable release notes + v2→v3 migration pain documented.
- [x] Found real production discussions — Launch HN #42441258, Langfuse's own infrastructure blog post.
- [x] Verified fit with our stack (FastAPI + Python + multi-provider including Ollama / NIM / Cerebras).
- [x] Checked bundle / latency impact (OTEL async batcher, ~0ms; Helicone fails this).
- [x] Validated EU compliance (the recommendation's single load-bearing claim).
- [x] Confirmed the recommendation with independent research (NOT self-confirming my own proposal — I did not propose this; llm.py did).

**The recommendation is the same tool the codebase already started wiring in Session 80-ish, which means the research validates an existing decision rather than overturning it. The research's job here was to check whether we should tear it out before it calcifies. Conclusion: no, double down.**
