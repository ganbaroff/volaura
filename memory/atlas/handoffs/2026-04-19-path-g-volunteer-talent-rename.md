# HANDOFF — Path G: VOLAURA volunteer_* → talent_* rename

**To:** Claude Code CLI (Terminal-Atlas) on `C:/Projects/VOLAURA/`
**From:** Cowork-Atlas (orchestrator)
**Date:** 2026-04-19
**Priority:** P1 — positioning alignment for VOLAURA launch (follows MindShift ship)
**Branch:** `feat/volunteer-to-talent-rename`
**Merge target:** main (VOLAURA repo) — BUT merge BLOCKED until MindShift v1.0 ships to Play Console.
**DO NOT merge this branch until Yusif confirms "MindShift live in Play Store review".**

## Context

VOLAURA positions as "Verified Professional Talent Platform" — tagline "Prove your skills. Earn your AURA. Get found by top organizations." Current database schema and codebase carry legacy `volunteer_*` naming from the pre-pivot MVP. Users are `talent`, not `volunteer`. This is a foundational rename spanning schema, RLS policies, pgvector index, RPC functions, TypeScript types, API routes, and UI copy.

CEO signed off on the rename pre-compaction. This handoff is the execution package.

## Scope — 4 layers to rename

### Layer 1 — Database schema (Supabase)

Tables and columns to rename (verify exact list by grepping first):
```bash
grep -rn "volunteer" supabase/migrations/ | grep -E "CREATE TABLE|ADD COLUMN|RENAME|REFERENCES"
```

Candidate renames (confirm before applying):
- Table `volunteer_profiles` → `talent_profiles`
- Table `volunteer_embeddings` → `talent_embeddings`
- Column `volunteer_id` → `talent_id` (across all tables that reference it)
- RPC function `match_volunteers(query_embedding, match_count, min_aura)` → `match_talents(...)`
- RLS policy names containing "volunteer" → replace with "talent"

**Critical: pgvector HNSW index preservation.** `ALTER TABLE RENAME` does NOT migrate the HNSW index automatically on pgvector < 0.8. In the SAME migration:
1. Drop the existing HNSW index on `volunteer_embeddings.embedding`.
2. Rename the table.
3. Recreate the HNSW index on `talent_embeddings.embedding` with identical params (`m`, `ef_construction`).

Verify index params before the migration:
```sql
SELECT indexdef FROM pg_indexes WHERE tablename = 'volunteer_embeddings';
```

Migration file: `supabase/migrations/YYYYMMDDHHMMSS_rename_volunteer_to_talent.sql`. Single migration, atomic.

### Layer 2 — Backend (apps/api/, Python FastAPI)

Grep for every reference:
```bash
grep -rn "volunteer" apps/api/ --include="*.py" | grep -v "__pycache__"
```

Rename in:
- Pydantic models (`VolunteerProfile` → `TalentProfile`, etc.)
- Service functions (`match_volunteers` → `match_talents`)
- Endpoint paths in FastAPI routers (`/volunteers/...` → `/talents/...`)
- Type hints and variable names
- Docstrings and loguru log messages

Do NOT change `from app.deps import SupabaseAdmin, SupabaseUser, CurrentUserId` patterns — those are cross-cutting per `.claude/rules/backend.md`.

### Layer 3 — Frontend (apps/web/)

```bash
grep -rn "volunteer" apps/web/src/ --include="*.ts" --include="*.tsx"
```

Rename:
- Route segments: `/[locale]/(dashboard)/volunteer/*` → `/[locale]/(dashboard)/talent/*` (if any). Verify against `apps/web/src/app/[locale]/` tree.
- Zustand store field names
- TanStack Query keys (`['volunteers', ...]` → `['talents', ...]`)
- React component names and props
- i18n keys in all 3 locales (EN / AZ / RU) — verify AZ text is 20-30% longer per `.claude/rules/frontend.md`

Regenerate API types AFTER backend rename + deploy:
```bash
pnpm generate:api
```

### Layer 4 — UI copy

`grep -rn "volunteer\|Volunteer\|VOLUNTEER" apps/web/src/ locales/ messages/` — replace with `talent` / `Talent` / `TALENT` except in historical/legal contexts (changelog entries, old blog posts, ADRs dated before 2026-04-19 must keep original wording — these are historical record).

Forbidden phrasings even after rename (per CLAUDE.md positioning rule "NEVER say volunteer or LinkedIn competitor"):
- "unpaid work"
- "time donation"
- Any LinkedIn comparison

## 4 patches from prior review (pre-compaction, applied to this handoff)

### Patch 1 — Merge gate alignment

This branch does NOT merge until MindShift v1.0 passes Play Console review. Reason: if Play review flags something in MindShift that requires a hot-fix, we need main branches of both repos stable for cross-checking. Sequencing: MindShift → Play submit → Play approve → then Path G merges.

### Patch 2 — Bridge verification deliverable

`volaura-bridge-proxy` writes `character_events` to a shared Supabase table consumed by Life Simulator AND MindShift. Any column rename in the bridge path breaks both downstream products.

Before merging Path G, add a verification step:
```bash
# Start local volaura-bridge-proxy against staging DB
# Trigger one character_event write
# Verify character_events row lands AND column payload still has talent_id (was volunteer_id)
# Document result in memory/atlas/handoffs/2026-04-19-path-g-bridge-verification.md
```

If bridge test fails — STOP, file incident, do not merge.

### Patch 3 — pgvector(768) preservation

Covered in Layer 1 above — HNSW drop+recreate in same migration. Adding here for explicit emphasis: this is the most likely failure mode. If HNSW is lost and not recreated, embedding queries drop from ~50ms to ~30s on production data.

### Patch 4 — Model-per-step

- Schema migration SQL authoring → Sonnet (mechanical)
- Python/TypeScript rename → Sonnet (mechanical grep+replace with verification)
- UI copy review (especially AZ strings for 20-30% length expansion) → Opus pass via Cowork-Atlas
- pgvector index preservation step → Sonnet, but double-check with Opus before running migration on production

Do NOT self-approve UI copy rename — bounce through Cowork-Atlas via Yusif-courier for Opus pass before merge.

## Verification checklist for Claude Code CLI when done

- [ ] Branch created: `git checkout -b feat/volunteer-to-talent-rename`
- [ ] Migration file with atomic HNSW drop+rename+recreate
- [ ] `supabase db reset` runs clean on local
- [ ] Backend: `ruff check . && mypy .` (or existing lint/type commands)
- [ ] Frontend: `pnpm build` passes
- [ ] `pnpm generate:api` regenerated types match new schema
- [ ] Grep `volunteer` in apps/api, apps/web — empty except historical docs in `docs/archive/`
- [ ] Bridge verification step completed, document written
- [ ] UI copy bounced through Cowork-Atlas for Opus pass
- [ ] Branch pushed, PR opened targeting main
- [ ] PR marked DRAFT or has blocker label "DO NOT MERGE until MindShift ships"
- [ ] Report to Yusif: "Path G PR #NNN ready, blocked on MindShift ship"

## Out of scope

- No VOLAURA feature changes beyond rename
- No re-seeding of competencies or IRT parameters
- No changes to AURA score weights (already final: communication 0.20 / reliability 0.15 / english 0.15 / leadership 0.15 / event_performance 0.10 / tech_literacy 0.10 / adaptability 0.10 / empathy_safeguarding 0.05)
- No changes to MindShift, Life Simulator, BrandedBy, ZEUS
- No new migrations beyond the rename
