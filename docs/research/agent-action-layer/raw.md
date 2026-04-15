# Agent action-layer — raw research notes (2026-04-15)

Unfiltered dump from 8 parallel searches. Summary lives in `summary.md`.

## Ground-truth audit of VOLAURA webhook (read before comparing to frameworks)

`apps/api/app/routers/telegram_webhook.py` = **2409 lines** (CEO stated ~500 — off by 5×).

Handler inventory (40+ async functions):
- `_transcribe_voice`, `_send_message`, `_save_message`, `_get_recent_context`, `_get_project_stats`
- `_load_atlas_memory`, `_save_atlas_learning`, `_get_ecosystem_context`, `_load_agent_state`
- `_classify_and_respond`, `_handle_status`, `_handle_backlog`, `_handle_proposals`, `_handle_proposal_action`, `_execute_proposal`
- `_handle_agents`, `_handle_agent_task`, `_handle_queue`, `_handle_swarm`, `_handle_ask_agent`, `_handle_ask_proposal`
- `_handle_ecosystem`, `_handle_skills`, `_handle_findings`, `_handle_simulate`
- `_detect_emotional_state`, `_load_atlas_learnings`, `_atlas_extract_learnings`
- `_classify_action_or_chat`, `_write_atlas_inbox_file`, `_create_github_issue`, `_char_similarity`, `_get_last_bot_reply`
- `_edit_message_reply_markup`, `_handle_proposal_card_callback`, `_handle_atlas`, `_handle_help`
- `telegram_webhook`, `setup_webhook`

Only the **bold** 5 handlers below are the "action layer" a framework would replace:
- `_classify_action_or_chat` ~50 LOC — regex verb/keyword classifier
- `_create_github_issue` ~40 LOC — httpx → GitHub REST
- `_write_atlas_inbox_file` ~30 LOC — markdown append
- `_char_similarity` ~15 LOC — char-bigram Jaccard, last-reply-only
- `_handle_proposal_card_callback` ~80 LOC — inline keyboard → JSON patch

Total replaceable: **~215 LOC**. Everything else is Atlas/swarm UX.

---

## Search 1 — LangGraph vs CrewAI vs AutoGen 2026

Key facts harvested:
- LangGraph 90k–126k stars (sources disagree), v1.x GA Sep 2025, v1.1.x Apr 2026.
- Uber, LinkedIn, Klarna, JPMorgan, BlackRock, Cisco, Elastic production.
- Klarna: AI support for 85M users, 80% faster resolution, two-thirds of tickets, $60M saved, equivalent to 853 employees.
- 47M+ invocations at Klarna/Uber/LinkedIn combined. 400 companies on LangGraph Platform.
- AutoGen v0.4 Jan 2026 async-native. Merged with Semantic Kernel → Microsoft Agent Framework GA Q1 2026.
- Cost/task: LangGraph $0.08, CrewAI ~$0.15, AutoGen $0.45 (GPT-4o).
- LLM calls/task: LangGraph 4.2, CrewAI 6.1, AutoGen 20+.
- MCP is the dominant tool-integration standard 2026. LangGraph deepest MCP integration (tools = graph nodes with streaming).
- Quote: "LangGraph for control freaks, CrewAI for fast shippers, AutoGen for research pipelines."
- Quote: "Default to LangGraph unless you have strong reasons not to."
- Hybrid pattern gaining traction: "CrewAI for prototype → LangGraph for prod hardening."

## Search 2 — Telegram bot + agent combos with tool calling

Repos found:
- `ma2za/telegram-llm-bot` — guide, llama2 on Beam Cloud.
- `csRon/telegram-llm-bot` — ChatGPT chat, no tools.
- `innightwolfsleep/llm_telegram_bot` — generic LLM bot.
- `mlloliveira/TelegramBot` — Ollama local, multi-model, no tools.
- `AIXerum/AI-Telegram-Assistant` — LangChain + LangSmith + Google APIs. CLOSEST to action layer.
- `yomazini/telegram-automation-bot-framework` — marketing blueprint, not library.
- `RomanPlusPlus/telegram-llm-bot` — trivial.
- AnythingLLM Telegram channel — native tool calling + MCP agent skills + chart renderer. Heavy hosted platform.
- SirChatalot — Whisper + DALL-E + vector DB + tools.
- Claude Code Telegram bridge (Terminal Live) — monitor AI coding agents via Telegram.

None ship "Telegram → agent with tool → GitHub issue + approve/reject cards" as a template.

## Search 3 — Claude Agent SDK

- `pip install claude-agent-sdk`, v0.1.59 Apr 13 2026.
- Renamed from "Claude Code SDK" Sep 29 2025.
- Built-in tools: Read, Write, Edit, Bash.
- Custom tools via `@tool` decorator + `create_sdk_mcp_server`.
- `ClaudeAgentOptions(allowed_tools=[...], permission_mode="acceptEdits")`.
- `disallowed_tools` to hard-block.
- `can_use_tool` callback for runtime permission decisions.
- Apr 2026 Managed Agents public beta — hosted runtime, sandboxed execution.
- Xcode 26.3 native Claude Agent SDK integration (Feb 3 2026).
- **BLOCKER for VOLAURA:** Constitution #12 says never use Claude as swarm agent. Using Anthropic SDK re-introduces vendor lock-in we routed around via LiteLLM.

## Search 4 — smolagents

- HF/smolagents, ~1000 LOC core, 26k stars, active Mar 29 2026.
- Code-agent paradigm: agent writes Python, not JSON. -30% LLM steps on GAIA benchmark.
- Ranked #1 GAIA validation (44.2%), #2 test (33.3%) with single CodeAgent > Autogen multi-agent.
- Supports any LLM via LiteLLM integration (matches VOLAURA stack).
- Sandboxing required (E2B / Blaxel / Modal / Docker / Pyodide-Deno WASM).
- LocalPythonExecutor explicitly NOT a security boundary.
- No persistence, smaller ecosystem, requires code-capable LLM.
- **Not a Telegram-action-layer tool.** Useful insight: code-as-action pattern.

## Search 5 — HN/Reddit "I replaced my Telegram bot with X"

No hits. Search too specific. The pattern isn't a written narrative yet — VOLAURA would be early.

## Search 6 — Circuit breaker / loop detection / Reflexion

Strongest actionable patterns of the whole research:

- **TTL breaker first in router:** `if state["retry_count"] >= 5: return "fail"` BEFORE goal check.
- **Semantic-oscillation detection via LangSmith traces:** look for fractal planner→tool→critic→planner pattern. Check if state payloads mutate — if not, it's burning compute in a vacuum.
- **Multi-signal breaker config (paperclipai/paperclip#390):**
  - `maxConsecutiveNoProgress: 5`
  - `maxConsecutiveFailures: 3`
  - `tokenVelocityMultiplier: 3.0`
- **Per-tool breaker:** trip after 3 consecutive fails, recovery probe after 5s, close after 2 probe successes.
- **Error-class taxonomy:** towardsdatascience — 90.8% of ReAct retries in 200-task benchmark were WASTED on non-retryable errors. Retryable = {500,502,503,504,429}. Non-retryable = {400,401,403,404,422}.
- **Reflexion 3-node pattern:** Responder → Search Tool → Revisor. Conditional edge `decide_to_finish(state)` with `revision_number` as circuit breaker field.
- **State shape:** `{problem_statement, current_answer, critique_history: List[str], revision_number: int}`.
- **Checkpointing mandatory in prod:** SqliteSaver or PostgresSaver, not MemorySaver.
- **Schema evolution gotcha:** add new TypedDict fields as Optional with defaults or 10k checkpoints fail on resume.
- **LATS (Language Agent Tree Search):** unifies Reflexion + ToT + plan-and-execute. Backpropagation of reflective feedback.

## Search 7 — Human-in-the-loop + Telegram/Slack + GitHub issue + LangGraph interrupt

- LangGraph native `interrupt()` + `Command(resume=...)` + thread_id-keyed checkpointer.
- `HumanInTheLoopMiddleware` with per-tool `interrupt_on` config; `allowed_decisions: ["approve", "edit", "reject"]`.
- Safe tools = `False` (auto-approve). Risky tools = `InterruptOnConfig`.
- **Lies-in-the-Loop attack:** approval UI shows sanitized summary, actual tool call has malicious args. Countermeasure: full payload visibility in approval UI.
- Slack+LangGraph (Scalekit): listen → classify → github_issue_create / zendesk_create_ticket. OAuth/token refresh/rate-limit in Scalekit, agent just routes.
- openclaw#2023: proposes `tools.approval` config with `mode: confirm`, `via: telegram` — identical shape to VOLAURA's proposal cards.
- Known bug langchain#33787: after edit decision, agent re-attempts original tool call → user has to reject the thing they just edited. Active bug.
- assistant-ui#1899: Approve/Reject button callback → backend never reached. Wiring resume-Command through UI is non-trivial.
- Approval/audit layer pattern: hash-chain audit trail, 13 framework integrations (Apache 2.0).

## Search 8 — Pydantic-AI vs LangGraph

- pydantic-ai v1 stable Sep 4 2025, 15k–16k stars, 40M+ downloads/month, weekly releases.
- Same team as Pydantic → FastAPI-native feel.
- `@agent.tool` with RunContext = same pattern as FastAPI `Depends()`.
- Line counts same chat app: Pydantic-AI 160, LangChain 170, LangGraph 280, CrewAI 420.
- Type-safe: `Agent[Deps, str]` generic, IDE autocomplete.
- Production: LinkedIn, Uber, Replit, Elastic, Klarna, Cloudflare, Coinbase.
- Has Human-in-the-Loop Tool Approval (per-tool flag) + Durable Execution.
- Result validation loop: if LLM output fails Pydantic schema → auto-retry with error as feedback.
- ZenML 2026 pattern: **"PydanticAI for agent logic + LangGraph for orchestration"** as complementary.

## Search 9 — Template repos Telegram + LangGraph/Pydantic-AI with approve-reject inline buttons

- `francescofano/langgraph-telegram-bot` — LangGraph + pgvector memory + Redis rate limit + Next.js dashboard. Chat bot, not action router. Good reference.
- `kosyachniy/aiagent` — FastAPI + LangChain/LangGraph + MongoDB + Motor + Terraform. Task planner. Minimal overlap.
- **No exact match** for "Telegram inline approve/reject + LangGraph or Pydantic-AI + GitHub issue creation" template.
- Conclusion: VOLAURA's proposal-card flow is a novel-ish combo. Post-launch OSS opportunity.

## Search 10 — Stars / Klarna / Uber / LinkedIn

Consolidated numbers (best-effort, sources disagree):
- LangGraph: 90k–126k stars, v1.1.6 Apr 8 2026. 34.5M downloads/mo.
- Pydantic-AI: 15.1k–16k stars, 40.2M downloads/mo.
- LangSmith: "best-in-class observability" per multiple sources.
- Klarna LangGraph case: 85M users, 80% resolution speedup, two-thirds of tickets, $60M saved.
- ZenML quote confirmed: PydanticAI+LangGraph complementary pattern "gaining the most traction in production AI engineering circles 2026."

---

## Raw links dump (for citation back in summary)

- https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen
- https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared
- https://medium.com/data-science-collective/langgraph-vs-crewai-vs-autogen-which-agent-framework-should-you-actually-use-in-2026-b8b2c84f1229
- https://altersquare.io/langgraph-vs-crewai-vs-autogen-review-recommend-production-deployment/
- https://oss.vstorm.co/blog/same-chat-app-4-frameworks/
- https://www.zenml.io/blog/pydantic-ai-vs-langgraph
- https://rajatpandit.com/optimizing-langgraph-cycles/
- https://towardsdatascience.com/your-react-agent-is-wasting-90-of-its-retries-heres-how-to-stop-it/
- https://ranjankumar.in/building-production-ready-ai-agents-with-langgraph-a-developers-guide-to-deterministic-workflows
- https://blog.langchain.com/reflection-agents/
- https://github.com/langchain-ai/langgraph-reflection
- https://github.com/paperclipai/paperclip/issues/390
- https://docs.langchain.com/oss/python/langchain/human-in-the-loop
- https://www.scalekit.com/blog/automate-slack-workflows-langgraph-scalekit
- https://github.com/openclaw/openclaw/issues/2023
- https://github.com/langchain-ai/langchain/issues/33787
- https://github.com/pydantic/pydantic-ai
- https://github.com/anthropics/claude-agent-sdk-python
- https://pypi.org/project/claude-agent-sdk/
- https://github.com/huggingface/smolagents
- https://www.decisioncrafters.com/smolagents-build-powerful-ai-agents-in-1-000-lines-of-code-with-26-3k-github-stars/
- https://github.com/francescofano/langgraph-telegram-bot
- https://github.com/kosyachniy/aiagent
- https://docs.anythingllm.com/channels/telegram
- https://github.com/AIXerum/AI-Telegram-Assistant
- https://softmaxdata.com/blog/definitive-guide-to-agentic-frameworks-in-2026-langgraph-crewai-ag2-openai-and-more/
- https://github.com/huggingface/smolagents
- https://platform.claude.com/docs/en/agent-sdk/overview
