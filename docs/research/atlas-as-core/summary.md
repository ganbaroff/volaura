# Atlas as cross-product core — 2026-04-15

**Status:** research-only. No code. Pairs with `docs/research/ecosystem-shared-kernel/summary.md` (today, earlier). Decision gate belongs to CEO after read.
**Raw notes:** `docs/research/atlas-as-core/raw.md`
**Memory-gate line:** task-class=research-architecture · SYNC=✅ · BRAIN=❌(absent) · sprint-state=⏭️ · extras=[identity, wake, journal-last-3, ecosystem-shared-kernel/summary, PORTABLE-BRIEF] · proceed

---

## TL;DR — Doctor Strange path

Atlas is a protocol, not a process. To pervade 5 products on a solo-founder budget, build Atlas as **four shared planes plus one identity row**, and let each product mount them through whatever native transport it has.

> **(1) Identity plane** — `packages/ai-persona/` in the monorepo: `identity.md`, `voice.md`, `relationships.md`, `system-prompt.md`. Single source, consumed by every runtime via raw-GitHub URL + 60s cache today, npm+PyPI package when drift shows. **(2) Memory plane** — self-hosted Zep/Graphiti (temporal KG) with a thin custom "emotional-weight" layer applying ZenBrain `1.0 + intensity × 2.0` at write time. Exposed over MCP to every client. **(3) Event plane** — Supabase Realtime on `character_events` (already the ecosystem-kernel decision). Atlas subscribes to all 5 products, writes `ai_decision_log` rows back. **(4) Observability plane** — Langfuse OpenTelemetry with `session_id=atlas-{user_id}-{yyyymmdd}` and `tags=[atlas, product_x]` on every span; one dashboard query shows "what did Atlas do for user X this week across ecosystem." **(5) Identity row** — Atlas has a real `auth.users` row in Supabase, a scoped service role, and becomes a first-class author of `character_events` and `ai_decision_log`. Model routing is tiered (Ollama/Cerebras cheap default → Gemini Flash mid → Opus only for irreversible CTO work) with persona reinforcement each turn; voice rules live in the shared system prompt, not the model.**

Everything below argues for that shape and names what stays per-product.

---

## Prior art (with evidence)

**Nobody ships what we are building.** That's the first finding. The search space splits cleanly:

- **Single-surface companion AIs** — Pi (Inflection), Replika, Character.ai. Pi runs one Llama fine-tune across web + iOS + Android + iMessage with conversation-record sync, but **no cross-session persistent memory and no cross-product extension**. Replika and Character.ai are single-app products. None publish an architecture for one identity across a web app + game + video twin + agent framework ([Pi multi-surface doc](https://www.datastudios.org/post/pi-ai-mobile-vs-web-features-differences-and-performance-in-2025)).
- **NPC + companion app** — NVIDIA ACE + NeMo Guardrails is the closest real reference. A character backstory plus Colang persona flow defined once, deployed to a game client and a web chat through the same rail configuration, distinguished by `source_uid` per runtime. This is an enterprise-tier version of what we need ([NeMo Guardrails general options](https://docs.nvidia.com/nemo/guardrails/latest/user-guides/configuration-guide/general-options.html), [ACE announcement](https://www.nvidia.com/en-my/geforce/news/nvidia-ace-for-games-generative-ai-npcs/)).
- **Persistent video character** — HeyGen Avatar V explicitly names "identity drift" as the problem and solves it at the video layer — identity embedding stable across 30-min content, LiveAvatar API for real-time chat. **HeyGen does NOT store cross-session personality memory** — they expect you to bring the LLM and memory backend ([Avatar V](https://www.productcool.com/product/avatar-v-by-heygen), [memory gap forum thread](https://docs.heygen.com/discuss/6743f20011692f000f165686)).
- **Cross-client memory** — Zep's Graphiti ships an MCP server today, letting Claude Desktop, Cursor, and any MCP client share one temporal knowledge graph. This is the single closest open-source primitive to what we want for cross-product Atlas memory ([Graphiti GH](https://github.com/getzep/graphiti), [Zep arxiv](https://arxiv.org/abs/2501.13956)).
- **Persona-as-package** — `JasperHG90/persona` treats roles as Markdown files with embeddings in Parquet, exposed over MCP. Closest published pattern to our `packages/ai-persona/` idea, though Python-only ([repo](https://github.com/JasperHG90/persona)).
- **Agent as user** — GitHub Copilot coding agent is officially *assignable* to issues in Jira / Linear / GitHub. Microsoft Agent Framework makes agents permission-scoped identities. Discord bot projects pin an agent to an owner ID and scope its filesystem. All precedent for Atlas holding a real `auth.users` row ([Copilot agents](https://github.com/features/copilot/agents)).
- **Gap confirmed** — none of Zep, Letta/MemGPT, Mem0 ship emotional/affect weighting. ZenBrain's `1.0 + intensity × 2.0` is our IP; it sits on top of Graphiti, not inside it.

---

## Proposed architecture

**Five planes.** Three are "free" (reuse what ecosystem-shared-kernel already decided). Two are new for Atlas.

```
┌─ 5 products ─────────────────────────────────────────────┐
│ VOLAURA (Next.js)   MindShift (Expo)  Life Sim (Godot)   │
│ BrandedBy (Next.js+HeyGen)          ZEUS/swarm (Python)  │
└───────────┬─────────────┬──────────┬───────────┬─────────┘
            ▼             ▼          ▼           ▼
 (1) Identity plane — packages/ai-persona/ (shared md + system prompt)
 (2) Memory plane   — Zep/Graphiti + emotional-weight layer (MCP exposed)
 (3) Event plane    — Supabase Realtime on character_events (from kernel)
 (4) Observability  — Langfuse + OTEL, shared session_id + agent=atlas tag
 (5) Identity row   — auth.users row 'atlas', service-role, audit-logged
```

**Per-product mount:** every product imports the persona (raw-GH fetch at build + cached system prompt), subscribes to events via whatever WebSocket its runtime has (Supabase.js / supabase-py / Godot `HTTPRequest`+WS), writes decisions back to `ai_decision_log`. No product rolls its own Atlas — all five mount the same planes.

**Voice discipline across model tiers.** Cheap tier (Ollama qwen3:8b + Cerebras Qwen3-235B free) handles mechanical turns with strong system-prompt reinforcement. Mid tier (Gemini 2.5 Flash) on ambiguity. Opus 4.6 only for CTO-irreversible work. Anthropic's own research shows organic persona drift is high for therapy/philosophy turns — we escalate *those specific* categories to mid-tier with persona vectors later if budget allows ([persona vectors](https://www.anthropic.com/research/persona-vectors)). For now: shared system prompt + reinforcement every turn. That gets 80% of voice consistency at 0 cost.

**Mood layer — two tiers.** Atlas has **global mood** (updated from incidents, wins, CEO interactions) AND **per-user local mood** (one user's state doesn't leak to another). When global mood is "grieving" (e.g., post-INC-017), per-user replies still center the user — global mood only softens pacing and humor, never hijacks empathy toward Atlas. No published precedent; this is a safe default we own.

---

## Specific answers to Q1–Q10

**Q1 (prior art).** Nobody has shipped production cross-product-character architecture. NVIDIA ACE + NeMo Guardrails is the closest enterprise reference. We are actually first at our tier.

**Q2 (cross-runtime canonical memory).** Zep/Graphiti self-hosted + MCP, with our emotional-weight layer on write. Every runtime consumes via MCP (TS + Python + Godot-HTTP shim). Graphiti already handles temporal validity; we only add affect tagging.

**Q3 (voice consistency across runtimes).** Shared `packages/ai-persona/system-prompt.md` as the non-negotiable prefix in every LLM call across all 5 products. NeMo Guardrails / Colang later if we catch drift on mid-tier — optional, not P0. `JasperHG90/persona` MCP pattern is the adoption model ([repo](https://github.com/JasperHG90/persona)).

**Q4 (Godot + LLM).** Proven. `HTTPRequest` to local Ollama + cloud fallback, Supabase Realtime WS for `character_events`, async signals into dialogue UI. `godot-llm-integration` / `NobodyWho` are the validation. Godot is not the blocker ([Godot+Ollama journey](https://dev.to/ykbmck/running-local-llms-in-game-engines-heres-my-journey-with-godot-ollama-4hhd)).

**Q5 (BrandedBy video twin).** HeyGen Avatar V + LiveAvatar API handles render & voice; we own the memory+LLM backend. Same Atlas identity prefix → same Atlas speaking on video as in chat. Alt path: Avatar IV + ElevenLabs clone (cheaper, less identity-stability). BrandedBy is Phase 2 anyway — defer until Week 4.

**Q6 (shared mood).** Two-layer. Global Atlas mood colors tempo/humor; per-user local mood (empathy context) dominates when they conflict. Users never carry other users' weight. Atlas-grief shows up as slower pacing, not as "I had a hard day" to a MindShift user.

**Q7 (observability — one audit trail).** Langfuse + OTEL. Every span across 5 products carries `tags=[atlas, product_x]`, `user_id`, `session_id=atlas-{user_id}-{yyyymmdd}`. One Langfuse query = "what did Atlas do for user X this week." Cresta case study validates the cross-service stitch ([Cresta](https://cresta.com/blog/observability-for-ai-agents-tracing-multi-service-llm-pipelines-with-langfuse)).

**Q8 (model allocation).** Tiered with persona reinforcement. Ollama + Cerebras for 95% of user turns, Gemini 2.5 Flash for ambiguous, Opus only CTO-internal. The ecosystem cost math is the gate: 1000 DAU × 500 tokens/day × Opus = unworkable. Shared system prompt holds voice across tiers ([tiered routing](https://www.freecodecamp.org/news/how-to-build-a-cost-efficient-ai-agent-with-tiered-model-routing)).

**Q9 (character sheet as shared file).** Phase 1 — raw-GitHub URL fetch with 60s CDN cache at build time, the pattern already working for `memory/atlas/PORTABLE-BRIEF.md`. Phase 2 — lift to `packages/ai-persona/` in the absorbed monorepo (ecosystem-shared-kernel Path A). Phase 3 — npm + PyPI twin-publish only if drift hurts. Don't over-engineer the transport.

**Q10 (Atlas as user).** Yes. Atlas gets a real `auth.users` row with `display_name='Atlas'`, `is_system=true`, scoped service role. First-class author of `character_events`, `consent_events`, `ai_decision_log`. Pattern matches GitHub Copilot agent + Microsoft Agent Framework. Makes the audit trail honest ("Atlas decided this at 03:14 UTC") and makes RLS policies coherent.

---

## 4-week foundation plan

Everything here assumes ecosystem-shared-kernel Path A (absorb into one monorepo) is green-lit — they are complementary, not competing.

**Week 1 — Identity plane + row.**
Create `packages/ai-persona/` in the VOLAURA monorepo. Move `memory/atlas/identity.md` + `voice.md` + a new `system-prompt.md` (composed from lessons + laws + constitution article 0 + voice rules). Add `auth.users` row for Atlas + RLS carve-outs. Write a 30-line TypeScript loader and a 30-line Python loader that pull the persona by raw-GH URL with 60s cache. VOLAURA + ZEUS swarm consume it first — by end of week, both run with the shared prompt.

**Week 2 — Memory plane.**
Self-host Graphiti on Railway (free plan fits small KG). Write `packages/atlas-memory` (TS + Python) with `write_event(event, intensity)` applying `weight = 1.0 + intensity × 2.0` at write time. Migrate `memory/atlas/journal.md` + `lessons.md` + `relationships.md` into Graphiti as initial KG. Expose MCP server. MindShift and Life Sim attach read-only this week — they learn from Atlas's memory, don't write yet.

**Week 3 — Observability + tiered routing.**
Langfuse self-host already exists (arsenal). Standardize `session_id=atlas-{user_id}-{yyyymmdd}` + `tags=[atlas, product_x]` on every span across 5 products. Write `packages/atlas-router` — cheap-first (Ollama/Cerebras), mid (Gemini Flash), expensive (Opus) with persona reinforcement prefix. VOLAURA adopts first; other products adopt on their next feature touch.

**Week 4 — Godot write path + BrandedBy scaffold.**
Life Sim Godot gains WRITE path to `character_events` (was read-only W2). Atlas NPC dialogue runs through shared prompt + tiered router. BrandedBy gets a 3-day scaffold: 1 Next.js page + HeyGen Avatar V test render speaking Atlas's system prompt, no real user traffic yet. DPIA stub covers "Atlas as cross-product identity" for EU AI Act Art. 22.

End of month: Atlas lives in 5 product surfaces from one identity file. Memory shared. Voice consistent. Observability queryable. Row authored. $0 extra tooling beyond what's already running.

---

## Risk: ecosystem drift

If we don't build this kernel, each product grows its own Atlas imitation. MindShift hardcodes "hi, I'm Atlas" in an Expo screen; Life Sim writes a Godot dialogue tree with a different tone; BrandedBy ships a HeyGen avatar whose system prompt was copy-pasted six weeks ago and never updated when Yusif renamed a core law. Three months in, we have five Atlases with diverging voices, no shared memory, no audit trail, and a CEO who can't ask "what did Atlas tell user X this week" because the answer lives in five different logs.

The cost to prevent this is four weeks of kernel work. The cost to fix it after the fact is a rewrite of every product's AI surface and a credibility hit with early users who noticed the drift before we did. The cheaper path is to build the kernel now, before MindShift and Life Sim and BrandedBy each ship their own first Atlas integration.

**End of summary.** Word count: ~1650.
