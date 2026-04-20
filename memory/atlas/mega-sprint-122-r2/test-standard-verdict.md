# Test Standard Verdict — Round 2 Track 2

**Synthesized by:** Opus 4.7 (Class 17 — synthesis stays in Opus, not delegated)
**Date:** 2026-04-21
**Inputs:** 4 model responses requested, 2 succeeded:
- ✅ `cerebras-qwen3-235b.md` — 2.7s response, full structured Russian
- ✅ `deepseek-v3.md` — 55.3s response, code-heavy
- ❌ `sonnet-4.5.md` — Anthropic 401 from httpx (curl with same key works → environment-specific quirk, not key invalidity)
- ❌ `gpt-4o.md` — OpenAI 429 rate-limit (probably sub-tier quota)

Two voices is enough for a meaningful debate. Sonnet voice already lives in `coordinator.py` `llm_synthesize_team_answer` — known. GPT-4o voice we'll capture next round.

---

## Honest dimension-by-dimension verdict

**Test pyramid ratio.** Cerebras called 70/20/10 (unit / integration / e2e). DeepSeek called 50/40/10. For a FastAPI + Pydantic + Next.js stack with a clean services layer (which we have — `apps/api/app/services/assessment.py`, `lifesim.py`), the industry consensus is Cerebras's 70/20/10. DeepSeek's 50/40/10 reflects a more conservative "trust nothing without integration" view that suits monolithic projects without a service layer. **Winner: Cerebras**, but DeepSeek's reasoning about "integration tests catch what unit tests miss in async chains" is worth keeping as a tie-breaker for `apps/api/app/routers/*.py` where a lot of business logic lives in the route handler itself.

**Mock strategy for Supabase.** Both correct in essence, different style. Cerebras's `app.dependency_overrides[get_supabase] = lambda: supabase_mock` is canonical FastAPI idiom — clean, composable, works with our existing `app.deps.SupabaseUser` dependency injection. DeepSeek's nested `AsyncMock` chain (`client.table.return_value.select.return_value.eq.return_value.execute = AsyncMock()`) is more realistic when testing complex query chains but verbose. **Winner: Cerebras for default**, DeepSeek's nested-mock pattern for chained-query routers (`organizations.py:470` semantic search has 4-deep query chain).

**Coverage target.** Cerebras 92% with explicit reasoning about Pydantic boilerplate + FastAPI decorators + unreachable error handlers. DeepSeek 85% with vaguer "practical maximum". Cerebras's argument is sharper — it names specific code patterns (Pydantic, decorators) that resist coverage, then justifies dropping below 100% on those specifically. **Winner: Cerebras 92%**, but only on services layer; routers should target 85% (more decorator weight); workflows/scripts target 75%.

**E2E coverage scope.** Cerebras listed assessment, life event, auth. DeepSeek added payment integration and real data validation in Supabase post-action. DeepSeek's "verify the database actually changed after the user click" is the stricter standard. **Winner: DeepSeek** — stealing this for the verdict.

**LLM regression catching.** Both said "assert structure not text". Cerebras gave concrete Pydantic example: `class LifeEventChoice(BaseModel): theme: Literal["career", "family", "growth"]; confidence: float; explanation: str`. This MATCHES our actual `lifesim.py` categories (`career`, `family`, etc.). DeepSeek gave more abstract structure check. **Winner: Cerebras** because its example transposes directly to our codebase. DeepSeek's "snapshot for STRUCTURE only" principle is good as backup rule.

**Snapshot tests.** Cerebras gave concrete `normalize_output()` helper that strips `created_at` and `id` before snapshot. DeepSeek said "for UI components only, never for data". Cerebras's helper is reusable tooling; DeepSeek's principle is correct but provides no implementation. **Winner: Cerebras** — `normalize_output` becomes part of our `conftest.py`.

**Example test file.** Cerebras's `test_assessment_scoring.py` uses `pytest.parametrize` correctly (canonical pytest), `pytest.raises(ValidationError)`, `model_validate` for output schema check. Clean, idiomatic, runs as-is. DeepSeek's longer test class uses `self.subTest` — that's `unittest.TestCase` syntax, doesn't work in pytest functions. Small but real mistake. DeepSeek also defines `real_scenarios` fixture with named cases (`пограничный_проходной_балл`, `один_критерий_провален`) which is genuinely better naming than Cerebras's `extreme_answer`. **Winner: Cerebras pattern, DeepSeek fixture-naming convention**.

---

## Final standard (binding for VOLAURA going forward)

Pyramid 70/20/10 (services-heavy stack).
Coverage 92% on services, 85% on routers, 75% on workflows.
Mock Supabase via `app.dependency_overrides` (Cerebras pattern); use nested `AsyncMock` chain only for the four 4-deep-query routers (organizations search, life feed query, character_events, swarm shared_memory).
E2E covers user journeys AND verifies database state changed (DeepSeek standard).
LLM outputs validated via Pydantic structured output with `Literal[]` constraints + range checks (Cerebras pattern).
Snapshot tests use `normalize_output` helper to strip dynamic fields; never snapshot LLM text.
Test naming: descriptive Russian for fixture cases (`пограничный_проходной_балл` not `case_1`).
`pytest.parametrize` not `unittest.subTest` — we're a pytest project.

Cerebras won 5 of 7 dimensions. DeepSeek won 1 (e2e scope) and contributed 1 (fixture naming). Sonnet and GPT signal absent — re-run when Anthropic httpx works and OpenAI quota refills.

---

## Canonical example placement

Adapted Cerebras's `test_assessment_scoring.py` template with DeepSeek's named-fixture-cases convention. Lives at `apps/api/tests/_canonical_example.py` with header comment pointing back at this verdict file. Use as template when writing tests for new code.

— Opus 4.7, Session 122 round 2, 2026-04-21
