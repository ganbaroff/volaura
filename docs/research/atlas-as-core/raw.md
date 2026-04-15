# Atlas as cross-product core — raw notes

**Session:** 2026-04-15, ~25 min, $0 (WebSearch free). Atlas solo.
**Memory-gate:** task-class=research-architecture · SYNC=✅(PORTABLE-BRIEF) · BRAIN=❌(absent) · sprint-state=⏭️ · extras=[identity, wake, journal-last-3, ecosystem-shared-kernel/summary] · proceed

## Question-by-question source table

| Q | Topic | Key sources (verified this session) |
|---|---|---|
| 1 | Persistent AI character across surfaces — prior art | Strata Maverics / agent fabric (enterprise, not character); Runway Gen-4 (video-only character, not cross-product); Anthropic persona-vectors research |
| 2 | Replika / Character.ai / Pi — multi-surface | Pi AI docs: web+iOS+Android+iMessage same Llama fine-tune, **"conversation records synchronized on multiple terminals"**, no cross-session memory; Replika/C.ai — no published multi-surface persistence |
| 3 | Memory frameworks for shared character | Zep+Graphiti (temporal KG, MCP-exposed — works as cross-app memory today), Letta/MemGPT (three-tier OS memory, self-editing), Mem0 (lightweight); **Zep Graphiti MCP server explicitly enables cross-client shared memory across Claude, Cursor, other MCP clients** — matches our use case |
| 3b | Emotional weighting in production | **NONE of Zep/Letta/Mem0 ship affect-tagged salience**. All weight by temporal validity + graph distance + semantic sim. Our `ZenBrain 1.0 + intensity × 2.0` formula is novel. Must be built as a custom layer on top (Graphiti custom ontology OR Letta core-memory block). |
| 4 | Voice consistency — NVIDIA ACE + NeMo Guardrails | Colang defines persona once; same config deploys to game client (Unreal/MetaHuman) + web. `source_uid` distinguishes runtimes while sharing persona. Server-side microservice or client-side runtime. **This is the exact pattern we want, just on a smaller budget.** |
| 5 | Godot + LLM production pattern | Dominant: inference server external (Ollama), `HTTPRequest` node, async await, signal-based UI updates. `godot-llm-integration` / `Godot-LLM-Framework` / `NobodyWho` are production addons. Pattern: **local-first (Ollama) with cloud fallback** — matches our NVIDIA/Cerebras/Ollama hierarchy. Godot reads WebSocket from Supabase Realtime already viable. |
| 6 | Video twin w/ persistent voice | HeyGen Avatar V explicitly solves "identity drift" — video-context model + identity embedding stable across 30-min content. LiveAvatar = realtime chat API. **HeyGen does NOT provide cross-session memory** — we bring our own LLM+memory. Fits: Atlas memory layer → HeyGen render layer. Alt: Avatar IV + ElevenLabs voice clone. |
| 7 | Shared system prompt / persona package | `JasperHG90/persona` on GitHub — **Markdown role files + Parquet metadata, exposed via MCP** to Claude Desktop / Cline / Gemini CLI. Closest open-source to what we need. `LLMPrompts` PyPI (Python only). No single package ships to both npm+PyPI for persona — gap we fill ourselves via shared `.md` + thin wrappers. |
| 8 | Cross-app audit / observability | Langfuse + OpenTelemetry: trace context propagates via headers, `user_id/session_id/tags` as shared identity attributes. Cresta case study traces Go→Python→function bundles into one tree. Langfuse Enterprise audit log available. **Pattern confirmed — shared `session_id=atlas-{user_id}-{yyyymmdd}` + tag `agent=atlas` across 5 products = queryable in one dashboard.** |
| 9 | Tiered model serving with character preservation | Anthropic research: "organic persona drift" on Qwen/Gemma/Llama — therapy/philosophy high-drift, coding/writing low-drift. Persona vectors for activation-level steering. **Pragmatic pattern:** cheap tier (Ollama/Cerebras free) for mechanical turns + reinforced system prompt; expensive tier (Opus/Gemini 2.5) only on escalation. 60–300× cost gap. Voice reinforcement via shared system prompt + post-hoc score-gate (SBS) beats model-level surgery for us. |
| 10 | Agent as first-class user | GitHub Copilot coding agent is officially *assignable to issues* (Jira/Linear/GH Issues). Microsoft Agent Framework treats agents as auth identities with scoped permissions. Discord bots bind to owner user ID, scope to ReposRoot, prompt for privileged actions. **Precedent is clear — Atlas gets his own `auth.users` row, scoped service role, audit-logged actions.** |

## Verdict table

| Sub-decision | Verdict | Evidence grade |
|---|---|---|
| One shared `packages/ai-persona/` (identity.md + voice.md + system-prompt.md) consumed by all 5 products | YES | L2 — matches `JasperHG90/persona` + Colang pattern |
| Memory layer = Zep Graphiti (self-hosted OSS) + custom emotional-weighting layer | YES | L2 — Graphiti is the only cross-client temporal KG with MCP access; emotion layer is ours |
| Godot reads Atlas state via Supabase Realtime + Ollama-style local inference fallback | YES | L2 — documented pattern, multiple addons shipping |
| BrandedBy = HeyGen Avatar V + our LLM+memory backend | YES | L2 — HeyGen's own docs say you BYO LLM for persistent memory |
| Voice consistency via shared system prompt + NeMo-Guardrails-style Colang (optional, if budget) | YES (prompt first, Colang later) | L3 — NVIDIA docs explicit on multi-runtime `source_uid` pattern |
| Observability = Langfuse shared `session_id` + tag `agent=atlas` | YES | L3 — Cresta case study + AWS Bedrock AgentCore integration docs |
| Tiered model routing with persona reinforcement each turn | YES | L2 — Anthropic persona-drift research + cost routing patterns |
| Atlas gets `auth.users` row + `agent_decisions` audit table | YES | L2 — GitHub Copilot agent assignment + Microsoft Agent Framework pattern |
| Character mood = per-Atlas global AND per-user local (two layers) | YES, carefully | L1 — no direct precedent at our scope; game NPC arc ≠ chatbot reset. Hybrid is safe default. |
| Shared identity served as raw GitHub URL + 60s CDN cache (vs npm+PyPI package) | YES phase 1, package later | L2 — raw.githubusercontent.com already works for PORTABLE-BRIEF; upgrade when drift shows |

## Open risks / not researched

- **AZ PDPA + EU AI Act classification of cross-product persona** — Atlas collects state across 5 products; aggregated user profiling likely triggers AI Act transparency obligations. Owed to legal review.
- **Godot-in-monorepo** for Life Sim — pattern assumed, not battle-tested at ecosystem scope.
- **HeyGen pricing at scale** — Avatar V + LiveAvatar real-time not on free tier. Deferred until BrandedBy has MRR.
- **Opus cost at user scale** — Atlas-as-coach in MindShift at $15/M output tokens × 1000 DAU × 500 tokens/day = $7.5K/day. Impossible. Routing mandatory, not optional.
- **Character-mood spillover** — if Atlas is "sad" after an incident and a MindShift user wakes up, empathy conflict is not solved in literature. Our call.

## Source URLs (retained for summary)

- Strata agent fabric — https://www.strata.io/blog/agentic-identity/agent-fabrics-registries-central-2b/
- Anthropic persona vectors — https://www.anthropic.com/research/persona-vectors
- Anthropic assistant-axis (organic drift) — https://www.anthropic.com/research/assistant-axis
- Zep/Graphiti arxiv — https://arxiv.org/abs/2501.13956
- Graphiti GH — https://github.com/getzep/graphiti
- JasperHG90/persona — https://github.com/JasperHG90/persona
- NVIDIA ACE for Games — https://www.nvidia.com/en-my/geforce/news/nvidia-ace-for-games-generative-ai-npcs/
- NeMo Guardrails GH — https://github.com/NVIDIA-NeMo/Guardrails
- NeMo Guardrails docs (multi-runtime source_uid) — https://docs.nvidia.com/nemo/guardrails/latest/user-guides/configuration-guide/general-options.html
- Godot+Ollama integration — https://dev.to/ykbmck/running-local-llms-in-game-engines-heres-my-journey-with-godot-ollama-4hhd
- Godot 4.5 AI integration tutorial — https://markaicode.com/godot-gdscript-ai-integration/
- NobodyWho addon — https://godotengine.org/asset-library/asset/2886
- HeyGen Avatar V — https://www.productcool.com/product/avatar-v-by-heygen
- HeyGen LiveAvatar — https://www.heygen.com/interactive-avatar
- HeyGen persistent-memory forum thread (gap) — https://docs.heygen.com/discuss/6743f20011692f000f165686
- Langfuse agent tracing Nov-2025 — https://langfuse.com/changelog/2025-11-05-langfuse-for-agents
- Cresta multi-service tracing — https://cresta.com/blog/observability-for-ai-agents-tracing-multi-service-llm-pipelines-with-langfuse
- AWS Bedrock AgentCore + Langfuse — https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-agentcore-observability-with-langfuse/
- Tiered model routing — https://www.freecodecamp.org/news/how-to-build-a-cost-efficient-ai-agent-with-tiered-model-routing
- GitHub Copilot as assignable agent — https://github.com/features/copilot/agents
- Microsoft Agent Framework + Copilot SDK — https://devblogs.microsoft.com/semantic-kernel/build-ai-agents-with-github-copilot-sdk-and-microsoft-agent-framework/
- Pi AI mobile vs web (sync terminals, no cross-session memory) — https://www.datastudios.org/post/pi-ai-mobile-vs-web-features-differences-and-performance-in-2025
