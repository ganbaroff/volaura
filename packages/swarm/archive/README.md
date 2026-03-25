# Swarm Archive

This folder contains one-time evaluation outputs and historical reports from the MiroFish swarm engine.

## Contents

- `*_result.json` — Single-run evaluation outputs (architecture audits, LinkedIn reviews, etc.)
- `*_report.json` — Detailed reports from self-upgrade and code review runs
- `*_summary.md` — Human-readable summaries of reports

## Why Archive?

These files are generated during experimental runs and are not part of the active codebase. They're kept here for historical reference and retrospective analysis.

## Active vs. Archived

**Active (kept in parent directory):**
- `autonomous_run.py` — Main entry point for daily autonomy
- `engine.py`, `inbox_protocol.py`, `middleware.py` — Core infrastructure
- `agent_hive.py`, `agent_memory.py`, `skills.py` — Agent management
- `self_upgrade_v7.py` — Latest self-upgrade protocol
- `providers/` — LLM provider implementations
- `prompt_modules/` — Active prompt templates
- `discovered_models.json` — Current model registry

**Archived (kept here):**
- Evaluation scripts: `evaluate_cto_review*.py`, `run_*_evaluation.py`, `run_*_review.py`
- Old self-upgrade versions: `self_upgrade*.py` (v1-v6), `self_analysis.py`
- Experimental tools: `benchmark.py`, `architecture_audit_summary.md`
- One-time evaluation outputs (JSON results)
- Historical self-upgrade reports
- Past code review sessions
