# CLONE RESCUE — decisions for the owner (MEGA-SPRINT Stage 4)

> Read-only investigation, **no merges, no deletes** (per the sprint STOP line). These three clones hold work not on `main`. Below is what each contains and a recommendation. You decide; the assessment-pipeline items need Codex review (spend/scoring-sensitive). Once decided, the rescue is one PR each + archive the clone.

## Summary
- `volaura-webhook-fix` and `VOLAURA_railway_fix` are the **same Telegram effort** — their `telegram_webhook.py` is byte-identical. `railway_fix` is the **superset** (same webhook fix + `atlas_consult` changes + the tests + scratch). Treat them as ONE telegram-stabilization landing.
- `VOLAURA_premerge` is 4 unrelated commits from **2026-05-07 (5 weeks stale)** — two touch the assessment pipeline (conflict risk with the recent D-1/D-3/D-5 work), one is a BrandedBy dashboard, one is a tiny infra route.

---

## A. VOLAURA_premerge — 4 commits ahead (2026-05-07)

| commit | what | recommendation |
|---|---|---|
| `abb4fc7` fix(assessment): atomic aura completion payload | `assessment.py` +194 / `schemas/assessment.py` +5. Reworks the completion payload. | **REVIEW (Codex) — do NOT blind-merge.** Same file + area I rewrote for D-1 (#122). "atomic" is NOT on main, and this predates D-1 by 5 weeks → high conflict/supersession risk. Diff against current `assessment.py` first; salvage only genuinely-new ideas. |
| `f391dda` fix(web): reveal aura+badge on completion | complete page, ±63 lines. | **REVIEW — likely partially superseded** by the D-3/D-5 complete-page work. Cherry-pick only what's not already shipped. |
| `eb407a9` fix(api): legacy v1 status route | `health.py` +9, additive. | **LAND (low risk)** — small, additive health route. Safe to cherry-pick. |
| `6830d4d` feat(brandedby): real dashboard | `brandedby/page.tsx` → 339 lines (main has a **27-line placeholder**). | **PRODUCT DECISION.** This contradicts "park BrandedBy" — but it's 325 lines of real work. Either (a) land it = BrandedBy gets a real dashboard and graduates from CONCEPT, or (b) keep parked. Either way **archive this branch so the work isn't lost.** |

## B. Telegram stabilization — `volaura-webhook-fix` (committed) + `VOLAURA_railway_fix` (uncommitted superset)

| source | what | recommendation |
|---|---|---|
| `volaura-webhook-fix` `d592e65` | Reworks `telegram_webhook.py` (276 lines), `main.py`, `telegram_llm.py`, `telegram_ambassador.py`. Stabilizes webhook delivery. | Part of the same effort as railway_fix (identical webhook file). |
| `VOLAURA_railway_fix` (9 uncommitted) | The SAME telegram_webhook rework **plus** `atlas_consult.py` changes, **plus the tests** (`test_atlas_consult.py`, `test_telegram_handle_atlas.py`), plus untracked `.tools/` and a captured inbox message. | **REVIEW + LAND TOGETHER as one "telegram-stabilization" PR**, using railway_fix's fuller set (it carries the tests). **Real value** for the "CEO's Telegram working" goal. ⚠️ Caveat: cannot be live-verified until the dead bot token (401) is replaced (Hermes Gate 2). Exclude the untracked `.tools/` and the inbox `.md` (local scratch, not repo content) unless you want them. |

---

## One-tap decisions for you
1. **Telegram stabilization** (B): land railway_fix's full set + tests as one PR? (Recommended — yes; it's the foundation for your Telegram working.) → I prepare the PR on your go.
2. **premerge assessment items** (A `abb4fc7`/`f391dda`): send to Codex for a supersession diff before any merge? (Recommended — yes.)
3. **premerge `eb407a9` health route**: cherry-pick now? (Recommended — yes, trivial.)
4. **BrandedBy dashboard** (A `6830d4d`): land it (graduate BrandedBy) or keep parked? (Your product call — but archive the branch regardless.)

After you decide, each clone collapses: rescue the chosen commits → archive the clone dir → `C:/Projects` loses 3 more redundant checkouts. **Nothing has been merged or deleted tonight.**
