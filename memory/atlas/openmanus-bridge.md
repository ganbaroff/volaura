---
name: OpenManus as ZEUS skeleton
description: OpenManus agent framework at C:\Users\user\OneDrive\Desktop\openmanus\OpenManus is the foundation for ZEUS swarm — each agent gets own sandbox VM
type: project
---

## Decision: OpenManus = ZEUS foundation (CEO directive 2026-04-18)

CEO launched Atlas inside OpenManus directory (whisper model path) and explained the vision:
- ZEUS orchestrates agents, each agent manages its own VM on CEO's laptop
- Whisper gives Atlas ears (speech-to-text)
- The swarm is the most important thing — CEO corrected Atlas for not reminding him
- Each agent starts within its capabilities, then improves the project

**Why:** `packages/swarm/agents/` is EMPTY (Session 112 finding). "44 agents" was an inflated claim; reality is 13 perspectives in PERSPECTIVES array + ~118 skill modules. OpenManus is MIT-licensed, production-ready agent framework with exactly the pieces we need. Building from scratch = Class 9 (skipped research). Using OpenManus = standing on MetaGPT team's shoulders.

**How to apply:** Every ZEUS agent design decision should start from OpenManus base classes, not from scratch.

## OpenManus Architecture (verified 2026-04-18)

Path: `C:\Users\user\OneDrive\Desktop\openmanus\OpenManus`

### Agent hierarchy
- `app/agent/base.py` → `BaseAgent(BaseModel, ABC)` — step loop, memory, LLM, state machine (IDLE→RUNNING→FINISHED→ERROR)
- `app/agent/react.py` → `ReActAgent` — think/act cycle
- `app/agent/toolcall.py` → `ToolCallAgent` — tool calls with LLM, 30 max steps
- `app/agent/browser.py` → `BrowserAgent` — web automation
- `app/agent/swe.py` → `SWEAgent` — software engineering
- `app/agent/mcp.py` → `MCPAgent` — Model Context Protocol

### Tools available
bash, python_execute, browser_use, file_operators, web_search, planning, str_replace_editor, computer_use, crawl4ai, chart_visualization, mcp, sandbox tools, ask_human, terminate

### Flow system
- `app/flow/base.py` → `BaseFlow`
- `app/flow/planning.py` → `PlanningFlow` — multi-agent orchestration
- `app/flow/flow_factory.py` → FlowFactory

### Sandbox (VM isolation!)
- `app/sandbox/` — Docker containers per agent
- Config: image, work_dir, memory_limit, cpu_limit, timeout, network toggle
- Daytona integration for cloud sandboxes
- THIS is how each swarm agent gets its own VM

### Config
- TOML-based (`config/config.toml`)
- Multiple LLM configs (default + per-agent overrides)
- Supports: OpenAI, Azure, Ollama API types

## ZEUS ↔ OpenManus mapping

| VOLAURA concept | OpenManus equivalent |
|-----------------|---------------------|
| ZEUS orchestrator | PlanningFlow + FlowFactory |
| Swarm agent | ToolCallAgent subclass |
| Agent VM | SandboxSettings (Docker container) |
| Agent tools | ToolCollection per agent |
| Agent memory | Memory class (extend with ZenBrain) |
| Whisper input | New WhisperTool (to build) |
| Atlas Brain | LLM config with Ollama/local models |

## Hardware (verified 2026-04-18)
- GPU: NVIDIA GeForce RTX 5060 Laptop GPU, 8151 MiB VRAM
- CUDA: 13.2 driver, torch being upgraded to cu128
- Whisper: openai-whisper installed, tiny model loads OK
- Ollama: confirmed live from Session 114

## Next steps
1. Whisper running on GPU ← in progress
2. Create ZEUS config bridging OpenManus to VOLAURA
3. First real agent: one ToolCallAgent with sandbox, given a simple VOLAURA task
4. Wire Whisper as input → Atlas Brain as processing → agent dispatch as output
