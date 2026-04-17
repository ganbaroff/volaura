---
name: Sprint E1 — Ecosystem Identity Sprint outcomes
description: What was decided and built in Sprint E1 (2026-03-29) — rebrand, architecture, integration spec
type: project
last_updated: 2026-03-29
---

# Sprint E1 — Ecosystem Identity Sprint

## Positioning Decision (LOCKED)
VOLAURA is now "Verified Professional Talent Platform"
- NOT a volunteer platform (all copy removed)
- NOT a LinkedIn competitor
- Tagline: "Prove your skills. Earn your AURA. Get found by top organizations."
- Org tagline: "Search talent by verified skill and score, not CVs."

**Why:** DSP simulation with 7 council personas scored Path C (43/50). "Professional" gives B2B vocabulary (Nigar, Aynur), "Talent" is aspirational for users (Kamal, Rauf, Leyla). "Platform" is honest at any scale (Attacker, Scaling Engineer).

**How to apply:** Never write "volunteer" in UI copy. Always say "talent", "professionals", "participants" for event context.

## Files Changed
- `apps/web/src/locales/en/common.json` — 20+ volunteer strings replaced
- `apps/web/src/locales/az/common.json` — 20+ könüllü strings replaced
- `CLAUDE.md` — Project Overview + council personas updated
- `docs/PROJECT-OVERVIEW.md` — NEW: full 5-product ecosystem description
- `docs/adr/ADR-006-ecosystem-architecture.md` — NEW: shared Supabase + character_state architecture
- `docs/MINDSHIFT-INTEGRATION-SPEC.md` — NEW: exact API contract for MindShift ↔ VOLAURA

## Architecture Confirmed (ADR-006)
1. Shared Supabase project — one auth, schemas per product
2. Shared FastAPI monolith — character.py router at /api/character/...
3. Event-sourced character_state — character_events + materialized view
4. Crystal economy — idempotent via game_character_rewards PRIMARY KEY

## What Was Already Built (Sprint 52-54, not E1)
- `character_events`, `game_crystal_ledger`, `game_character_rewards` tables — EXIST in migrations
- `GET/POST /api/character/events`, `GET /api/character/state` — BUILT and registered
- `emit_assessment_rewards()` service — BUILT, called from assessment completion
- `deduct_crystals_atomic` RPC — BUILT

## Sprint E2 Plan (next)
- MindShift Supabase migration (their project → shared VOLAURA Supabase)
- MindShift focus_sessions → character events bridge
- AURA badge display in MindShift ProgressPage
- Crystal balance in MindShift

## Sprint E3 Plan (after E2)
- Fix Life Simulator 4 P0 bugs (see ecosystem_master_plan.md bug list)
- Wire CloudSaveManager to character_state API (CLOUD_ENABLED=true)
- Crystal balance + verified skills visible in game

## Life Simulator Repo
- Location: C:\Users\user\OneDrive\Desktop\BestGame\life-simulator-2026
- Engine: Godot 4.4 GDScript
- CloudSaveManager exists but CLOUD_ENABLED = false
- 4 P0 crashes before playable
