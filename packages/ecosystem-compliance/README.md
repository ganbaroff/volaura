# ecosystem-compliance

Shared GDPR Article 22 + EU AI Act + AZ PDPA compliance schema + types for the VOLAURA ecosystem.

Backed by 4 Postgres tables in the shared Supabase project:

| Table | Purpose |
|-------|---------|
| `policy_versions` | Immutable log of every privacy policy / ToS / consent text version we publish. |
| `consent_events` | Append-only ledger: every consent given / withdrawn / updated by every user. |
| `automated_decision_log` | Every AI-Act-relevant decision (AURA score, match, recommendation, focus score). |
| `human_review_requests` | Article 22 contest tickets, 30-day SLA auto-set by trigger. |

Migration: `supabase/migrations/20260415230000_ecosystem_compliance_schema.sql`.

## Design principle

Every row carries `source_product TEXT` constrained to `('volaura','mindshift','lifesim','brandedby','zeus')`. Each product writes via its own service_role (BYPASSRLS), tagging rows with its own name. RLS lets authenticated users read their own rows across **all** products with a single JOIN on `user_id`.

Shared Supabase auth → single `auth.users.id` across all 5 products → one compliance backbone.

## Append-only guarantees

- `policy_versions`: no `UPDATE`/`DELETE` policy exists. service_role can still mutate (BYPASSRLS), but anon/authenticated cannot even under SQL injection.
- `consent_events`: same — append-only by policy omission.
- `automated_decision_log`: same.
- `human_review_requests`: users can `INSERT` their own tickets; no UPDATE/DELETE for users (reviewer mutations happen via service_role).

`policy_versions.content_sha256` is auto-computed by `policy_versions_hash_content()` trigger on insert/update of `content_markdown`. Tamper detection: compare stored hash vs `sha256(content_markdown)` at any time.

`human_review_requests.sla_deadline` is auto-set to `requested_at + 30 days` by `human_review_requests_set_sla()` trigger. Overdue query:

```sql
SELECT id, user_id, source_product, sla_deadline
FROM human_review_requests
WHERE status IN ('pending','in_review')
  AND sla_deadline < now()
ORDER BY sla_deadline ASC;
```

## Python usage (FastAPI products: volaura, mindshift, zeus)

Install in editable mode from monorepo:

```bash
pip install -e packages/ecosystem-compliance/python
```

Record an automated decision:

```python
from ecosystem_compliance import AutomatedDecisionCreate
from app.deps import SupabaseAdmin

async def log_aura_score(db: SupabaseAdmin, user_id: UUID, theta: float, score: float, se: float):
    record = AutomatedDecisionCreate(
        user_id=user_id,
        source_product="volaura",
        decision_type="aura_score_computed",
        decision_output={"score": score, "theta": theta, "se": se},
        algorithm_version="aura-engine-v1.2.0",
        explanation_text=(
            f"Based on {theta:.2f} ability estimate from adaptive assessment. "
            f"Standard error ±{se:.2f}. Weights: communication 20%, reliability 15%, "
            f"English 15%, leadership 15%, event performance 10%, tech 10%, "
            f"adaptability 10%, empathy 5%."
        ),
        human_reviewable=True,
    )
    result = await db.table("automated_decision_log").insert(record.model_dump(mode="json")).execute()
    return result.data[0]
```

Record a consent event:

```python
from ecosystem_compliance import ConsentEventCreate

event = ConsentEventCreate(
    user_id=user_id,
    source_product="mindshift",
    event_type="consent_given",
    policy_version_id=current_privacy_policy_id,
    consent_scope={"ai_decisions": True, "cross_product_share": True, "marketing": False},
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
)
await db.table("consent_events").insert(event.model_dump(mode="json")).execute()
```

## TypeScript usage (Next.js: volaura web, brandedby; Expo: mindshift, lifesim)

Depends on `zod@^3.22`.

```bash
pnpm add zod
pnpm add -D @volaura/ecosystem-compliance  # workspace:* in monorepo
```

Validate then insert from client / edge:

```ts
import { ConsentEventCreateSchema } from "@volaura/ecosystem-compliance";
import { createClient } from "@/lib/supabase/server";

export async function recordConsent(input: unknown) {
  const payload = ConsentEventCreateSchema.parse(input);
  const supabase = await createClient(); // service_role on server
  const { data, error } = await supabase.from("consent_events").insert(payload).select().single();
  if (error) throw error;
  return data;
}
```

Read user's consent history (RLS owner-read applies automatically):

```ts
import { ConsentEventSchema } from "@volaura/ecosystem-compliance";

const { data } = await supabase
  .from("consent_events")
  .select("*")
  .order("created_at", { ascending: false });

const events = data?.map((row) => ConsentEventSchema.parse(row)) ?? [];
```

## Per-product integration notes

| Product | Service_role writes | User-facing reads |
|---------|---------------------|-------------------|
| **volaura** | Every AURA score → `automated_decision_log` (`aura_score_computed`), every badge tier → (`badge_tier_assigned`). Article 22 opt-in modal → `consent_events`. | `/profile/decisions` shows full history with `explanation_text`; `[Request human review]` button → `human_review_requests` insert. |
| **mindshift** | Daily focus score → `automated_decision_log` (`focus_session_scored`). Onboarding consent → `consent_events`. | Timeline view can join user's own decisions across products. |
| **lifesim** | Crystal economy decisions (`match_suggested`, `content_recommended`) → `automated_decision_log`. | In-game settings panel reads consent state via `source_product='lifesim'`. |
| **brandedby** | AI-twin content recommendations → `automated_decision_log` (`content_recommended`). | Creator dashboard surfaces review-request workflow. |
| **zeus** | Agent-triggered actions that affect users → `automated_decision_log`. Telegram consent → `consent_events`. | Read-only; user views via volaura web. |

All 5 products share the same `auth.users.id`. An EU DSAR (Article 15) returns every consent and every decision across every product with one query keyed on `user_id`.

## Why append-only

GDPR Art. 5(2) accountability principle: the controller must be able to demonstrate compliance. If consent records can be silently updated, they aren't evidence — they're a claim. Append-only gives you a tamper-evident history; overriding an earlier state is done by inserting a `consent_updated` or `consent_withdrawn` row, not by mutating the original.

## Next steps (not in this phase)

- Wire `/auth/register` → write first `consent_events` row referencing current ToS `policy_versions.id`.
- Seed `policy_versions` with privacy v1.0, ToS v1.0, AI decision notice v1.0 in az/en/ru.
- `<Article22ConsentModal />` React component.
- `<HumanReviewRequestForm />` + admin queue UI at `/admin/review-queue`.
- DPIA via CNIL PIA tool → `docs/compliance/DPIA-v1.md`.
- FRIA template for B2B deployers → `docs/compliance/FRIA-template-for-deployers.md`.
