# MiroFish Swarm Engine

Core autonomous agent engine for Volaura. Runs via GitHub Actions (`swarm-daily.yml`) every day at 09:00 Baku time.

## Active Components

### Entry Point
- `autonomous_run.py` — Daily ideation, code review, CTO audit. Called by CI/CD.

### Core Engine
- `engine.py` — LLM orchestration, prompt routing, response parsing
- `inbox_protocol.py` — Proposal management and escalation
- `provider/` — Multi-model support (Groq, Gemini, DeepSeek, OpenAI)

### Agent Infrastructure
- `agent_hive.py` — Agent instance management
- `agent_memory.py` — Persistent agent state and context
- `middleware.py` — Request/response middleware for logging and filtering
- `skills.py` — Agent skill definitions and context injection

### Memory & Reasoning
- `memory.py` — Session memory for agents
- `structured_memory.py` — Structured data serialization
- `reasoning_graph.py` — Decision tree traversal for multi-step reasoning

### Swarm Governance
- `team_leads.py` — Agent role definitions and weights
- `types.py` — Shared type definitions

### Self-Improvement
- `self_upgrade_v7.py` — Latest self-upgrade protocol (v7)
- `autonomous_upgrade.py` — Autonomous self-enhancement workflow

### Integrations
- `telegram_ambassador.py` — CEO notifications via Telegram/MindShift bot
- `inbox_protocol.py` — Proposal persistence and ranking

### Data & Modules
- `prompt_modules/` — Modular prompt context (architecture, gaps, team identity)
- `discover_models.py` — Dynamic model discovery and evaluation

## Archived Components

See `archive/` for historical evaluation scripts and reports:
- Old evaluation runners (`run_*_evaluation.py`, `evaluate_cto_*_v*.py`)
- Past self-upgrade versions (v1-v6)
- Historical reports and summaries

## Running the Swarm

### Automatic (via GitHub Actions)
```bash
# Runs daily at 09:00 Baku time
# Or trigger manually via GitHub Actions UI
```

### Manual
```bash
# Daily ideation
python -m packages.swarm.autonomous_run --mode=daily-ideation

# Code review focus
python -m packages.swarm.autonomous_run --mode=code-review

# CTO audit focus
python -m packages.swarm.autonomous_run --mode=cto-audit
```

## Configuration

- `GROQ_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY` — LLM APIs (set in GitHub Secrets)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CEO_CHAT_ID` — CEO notifications (set in GitHub Secrets)
- Results saved to `memory/swarm/proposals.json`
- Escalations logged to `memory/swarm/ceo-inbox.md`
