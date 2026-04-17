---
name: Assessment 500 + Activity Badge Bug Post-Mortem (April 5, 2026)
description: Two P0 bugs that blocked all assessment starts. Root causes, what slipped through, what changes permanently.
type: feedback
---

## The two bugs and what actually happened

**Bug 1 — Assessment start returned 500 for every user.**

The `options` column in `questions` stores MCQ answer choices as JSONB. But the values were inserted as double-encoded JSON strings (jsonb_typeof = 'string', not 'array'). The Python SDK returned `options` as a Python `str`. Pydantic v2 typed the field as `list[dict]` — couldn't coerce string to list — threw `ValidationError`. FastAPI → 500.

The DB INSERT succeeded (201 in Supabase logs). The session was written. The response serialization crashed. Users saw a blank spinner.

**Bug 2 — Activity feed silently threw DB errors on every request.**

`activity.py` queried the `badges` catalog table and asked for `volunteer_id`, `tier`, `earned_at` columns that don't exist there. Correct table: `volunteer_badges` (earned records). The error was swallowed by `except Exception as e: logger.warning(...)` — users saw an empty feed with zero indication of failure.

## Why: Validate at the boundary, not inside it

`fetch_questions()` returns raw dicts. No schema check. No DB-layer validation. It handed `options` as a string directly into `QuestionOut()`. Pydantic was the first checkpoint — and it was too late.

The `activity.py` column names were written from memory, not verified against the actual schema. One table read before writing would have caught it instantly.

## Fix 1: parse options in fetch_questions

```python
for q in questions:
    if isinstance(q.get("options"), str):
        try:
            parsed = json.loads(q["options"])
            q["options"] = parsed if isinstance(parsed, list) else None
        except (json.JSONDecodeError, TypeError):
            q["options"] = None
```

QA caught that the first version of this fix only handled `JSONDecodeError` but not "valid JSON, wrong type" (e.g. `{}` or `42`). Second commit added the `isinstance(parsed, list)` guard.

## Fix 2: correct table + join

```python
await db.table("volunteer_badges")
    .select("id, badge_id, earned_at, metadata, badges(badge_type, name_en)")
    .eq("volunteer_id", user_id)
    ...
```

PostgREST executes the FK join as a single SQL query — no N+1 risk.

## What the swarm found (that I missed)

**QA Engineer:**
- The fix initially didn't guard against `options = {}` or `options = 42` after parse. Caught and fixed.
- No tests existed for `fetch_questions()` with real question data. It was only tested through full assessment flow integration — which masked the type error.
- The `volunteer_badges` FK join can return `null` if the badge definition row doesn't exist (orphaned row). Not guarded against.
- `limit` parameter has no validation — `limit=-1` or `limit=10001` untested.

**Scaling Engineer:**
- `fetch_questions()` mutates dicts in place before caching. The mutation itself is safe here. But any downstream code that further mutates returned dicts would corrupt the shared cache. Should use `copy.deepcopy()` before returning to callers. Not fixed yet — tracked as tech debt.
- Two concurrent cache misses for the same key both reach the DB (thundering herd at TTL expiry). Async lock not in place. Tracked as tech debt.
- The Supabase join is a single SQL JOIN — zero N+1 risk.
- `volunteer_badges` needs composite index `(volunteer_id, earned_at DESC)` for scale. Not verified as existing.

**Leyla (user impact):**
- Trust damage: 8/10. Silent failure on the first action is worse than a visible error.
- The 30-min cooldown applied to a user whose failure was caused by the platform — not by them. She was punished for the bug.
- Recovery requires a personal, specific message sent within the hour: "Leyla, this was our fault. Your cooldown is removed. Here's what we fixed." Not a banner. Not tomorrow. Now.

## Rules that change permanently

**Rule 1: Validate DB boundary results before they reach Pydantic.**
Any function that returns raw DB dicts and feeds them into a Pydantic model needs a test that seeds real-shape data (including edge cases like string-in-JSONB) and asserts the output type.

**Rule 2: No silent swallow on paths that gate core user actions.**
`logger.warning` is fine for supplementary feed items. It is never acceptable on the path for: assessment start, answer submit, score write, profile load. These must raise or surface.

**Rule 3: Column names verified against schema before any PR ships.**
Any PR that references a column name by string literal must have a query against the real schema — or a grep of the migration files — proving the column exists. This takes 30 seconds.

**Rule 4: Cooldown must distinguish "user abandoned" from "platform failed."**
If a session was inserted and then the response failed server-side (500 after 201), the session should be marked `failed_start` not counted as a user-initiated start for cooldown purposes. This is a future schema change — tracked.

**Why:** Platform's core promise is professional credibility. A broken first assessment attempt directly contradicts that promise. A silent spinner is worse than a visible error because it implies either incompetence or indifference. Recovery is possible but only if it's fast and personal.
