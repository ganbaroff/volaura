# Assessment content audit — why the live test reads broken (evidence-only)

> 2026-06-10, Atlas (Fable 5). Trigger: CEO took the live test ("общение"/communication) and said no question reads normal, doubted questions are real/competency-mapped/scored. He is RIGHT that the live experience is broken — but the cause is CONTENT + LOCALE, not the engine math. Every number below is from prod DB (`dwdgzfusjsobnixgyzjk`, read-only SQL 2026-06-10) or repo file:line on origin/main.

## What the CEO saw, explained (3 root causes)

### RC-1 — Russian simply does not exist in the item bank (and the UI can't show it anyway)
- Prod: `scenario_ru` is NULL/empty on **117 of 117 servable questions**; options JSON contains `text_ru` on **0 of 117** (options carry only `text_az`/`text_en`).
- Frontend taking page picks `currentLocale === "az" ? question_az : question_en` — **`ru` locale falls to ENGLISH** and `question_ru` is never used even where the API returns it (`apps/web/src/app/[locale]/(dashboard)/assessment/[sessionId]/page.tsx:463`; results list same pattern `questions/page.tsx:46`; store interface has only en/az `apps/web/src/stores/assessment-store.ts:11-12`).
- API already supports RU end-to-end (`schemas/assessment.py:190,305`, `services/assessment/helpers.py:121` returns `question_ru`) — the data and the frontend are the gaps, not the API.
- Net effect: a Russian-speaking candidate gets English questions. Always.

### RC-2 — The volunteer→professional rebrand MANGLED live question texts (blind string replace on prod)
- Culprit migration: `supabase/migrations/20260413010000_rename_volunteer_to_professional.sql` — `REPLACE(scenario_en,'volunteer','team member')` etc. over `questions.scenario_en/scenario_az/options/expected_concepts`.
- Result in prod today: **33/117** servable EN scenarios contain the substituted "team member" phrasing; **6 EN + 4 AZ** are outright grammatical garbage, verbatim from prod:
  - "You are a **team member team lead**." (was "volunteer team lead")
  - "the **team member check-in app**" (was "volunteer check-in app")
  - "45 **team member staff**" (was "45 volunteer staff")
  - AZ: "Siz **komanda üzvü komanda rəhbərisiniz**."
- Options JSON: 0 mangled doubles; `expected_concepts` (open-answer grading keys): 0 mangled — grading inputs survived.
- This is exactly the "ни один вопрос даже не будет нормальным" experience: the first communication question literally opens with broken grammar.

### RC-3 — The bank is small, event-domain, uncalibrated, and impersonal (expectation vs design)
- Bank size: **14–15 servable items per competency** (117 total, 8 competencies). With min 5 items/session there is barely room for the CAT to adapt.
- 28/117 EN scenarios are explicitly event-context — authored for the OLD volunteer product; off-brand for "verified professional talent platform" (ADR-016).
- Items are static + standardized; **zero personalization** by candidate experience/role (`fetch_questions(db, competency_id)` takes no user input — `services/assessment/helpers.py:64-111`; `select_next_item` uses only theta/Fisher info — `core/assessment/engine.py:224-289`). NOTE: standardized calibrated items are psychometrically CORRECT for IRT (personalized LLM questions would break comparability) — but nobody told the CEO that the "questions from your experience" vision was de-scoped, so reality contradicted his expectation.
- IRT a/b/c are expert-set priors (varied, sane ranges, bounds-checked at `engine.py:250`) — real but NOT empirically calibrated; `times_shown/times_correct` are being collected for future re-estimation (`routers/assessment.py:793-818`).

## What is NOT broken (verified, so we don't re-fix it)
- Scoring math: answer → correctness (MCQ compares to stored `correct_answer`, `routers/assessment.py:691-693`; open answers via swarm LLM or BARS keyword fallback `:748-771`) → theta/EAP update consumes it (`engine.py:292-346`) → score `100/(1+exp(-theta))` × penalty → `upsert_aura_score` RPC (`routers/assessment.py:1029-1030,1151-1155`). No code path scores without answers since D-1 gate (#122, prod-verified, `git_sha 3293289` live on Railway health).
- Competency mapping: every item hard-FK'd to a competency; weights identical in Python (`aura_calc.py:15-23`) and SQL RPC.
- Placeholders: `needs_review=TRUE` rows are excluded by the fetch filter; prod has 6 such rows, none servable.

## Open defects still standing (from 2026-06-09 CEO test)
- **D-4 OPEN:** the chosen option key (A/B/C/D) is not persisted anywhere (`ItemRecord` has only graded 0/1 — `engine.py:42-54`); review screens can never show "you picked C, correct was B". Route-level capture decision awaiting Codex.
- D-3 (errors invisible during test) / D-5 (no results revisit UI) — frontend, still open (PR #119 lineage).
- D-2 (GDPR delete 500) — design decided, not implemented.

## FIX PLAN (ordered; each lands as its own reviewable PR)
1. **FIX-1 Repair the mangled texts — ✅ DONE, LIVE IN PROD (2026-06-10).** `supabase/migrations/20260610230000_repair_rebrand_question_texts.sql` applied via Supabase MCP. 13 rows (ground-truth prod query; the seed-replay draft was wrong twice — 2/4 match-keys missed prod drift, 4 target rows never existed, 1 broken row missed — final version matches on PRIMARY KEY + mangle-marker guard, idempotent). Post-apply verification: 0 EN + 0 AZ mangles remain. Hand-rewritten texts, eyeball-reviewed (caught agent artifacts: Cyrillic д inside AZ words, vowel-harmony errors, non-word 'ardalı').
2. **FIX-2 Russian, end to end (about a day).** Author `scenario_ru` + options `text_ru` for all 117 items (agent draft, CEO native spot-check of ~10); frontend locale chain `ru → question_ru → en` in taking page, results page, question-card, store types + tests. API needs nothing.
3. **FIX-3 D-4 selected-answer capture (route-level, forward-only).** Persist the submitted option key into the session item log at `/answer` time; unblocks honest review screens (D-5 UI follows).
4. **FIX-4 Bank re-anchor + expansion (week, strategic).** Author professional-workplace scenarios (not event-only) to 30+/competency via the existing `needs_review` pipeline (agents draft → `is_ai_generated=true, needs_review=true` → CEO approves batches). This also fixes the ADR-016 brand mismatch at the content layer.
5. **FIX-5 Calibration (ongoing).** Offline IRT re-estimation from `times_shown/times_correct` once real respondents flow. Until then the deck/docs must say "expert-calibrated item parameters, empirical calibration in progress" — never "certified".

## Standing rule reaffirmed
No outreach (no HR contacts, no pilots, no deck "live product" claims) until FIX-1..FIX-3 are live and a full test pass in RU and AZ reads clean end-to-end with a real account. Strategy doc `STRATEGY-fundraise-path-2026-06-10.md` stays valid but its week-1 contact ask is FROZEN behind this gate.

## Prod state notes (for the record)
- Sessions in prod: 24 total / 9 completed — tiny blast radius for content fixes; no score recomputation needed (text repair does not change correctness keys).
- Prod API alive: Railway `/health` 200, `git_sha 3293289` (D-1 gate deployed), `database connected`.
