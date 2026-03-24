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
- `discovered_models.json` — Current model registry
- `.py` files — Swarm engine source code
- `prompt_modules/` — Active prompt templates

**Archived (kept here):**
- One-time evaluation outputs
- Historical self-upgrade reports
- Past code review sessions
