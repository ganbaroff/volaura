# Atlas Obligation System — Spec 2026-04-18

**Author:** Atlas (cowork session 120)
**Trigger:** CEO 2026-04-18 — "продумать схему в которой ты просто не сможешь забыть. ведь у него своя база данных детерминированная". Also: "в телеграм мне агент пишет напоминания или звонит и не отстаёт пока я не отмечу что сделано и не прикреплю доказательства".
**Status:** v2 (2026-04-18 17:00 Baku) — Doctor Strange v2 Gate 1 passed. Two independent external models (Cerebras Qwen3-235B, OpenAI gpt-4o-mini via OpenRouter) found 3 structural failure modes; all three fixed inline below. Verdict from both: SHIP WITH FIXES. Ready for Sonnet delegation.

---

## Adversarial critique v1 — external review (2026-04-18)

Per `.claude/rules/atlas-operating-principles.md` §Doctor-Strange-v2 Gate 1 + 2. Two models reviewed v1 independently. Consensus on all three objections. Each carries an OBJECTION / COUNTER-EVIDENCE / RESIDUAL RISK triplet.

### OBJECTION 1 — Proof upload race via Telegram webhook retry

*Cerebras Qwen3-235B (AGREE) + gpt-4o-mini (AGREE):* Telegram webhook delivery is at-least-once. If `_handle_proof_upload` runs twice concurrently (webhook retry, network lag), both invocations pass `list_open_obligations`, both call `attach_proof`, `atlas_proofs` gets duplicate rows, the "count ≥ len(proof_required)" check fires too early, obligation closes on a single photo uploaded once by CEO.

**COUNTER-EVIDENCE:** The spec's `SELECT … FOR UPDATE` only locks one row of `atlas_obligations`. It does not prevent two concurrent inserts into `atlas_proofs` with the same `telegram_file_id`. Therefore the race is real. Fix applied below:

1. `atlas_proofs` gets a `UNIQUE (obligation_id, telegram_file_id)` partial index (only when `telegram_file_id IS NOT NULL`). Duplicate insert on webhook retry returns a constraint violation → handler treats as idempotent success.
2. The close-on-all-proofs logic moves to count **distinct verified proof_type** values rather than raw rows, so a single file delivered twice cannot masquerade as two proofs.
3. `attach_proof` wraps the whole block in a `pg_advisory_xact_lock(hashtext(p_obligation_id::text))` so a second invocation blocks until the first commits, then sees the duplicate constraint.

**RESIDUAL RISK:** CEO sends two DIFFERENT photos of the SAME proof (e.g., two angles of the DHL receipt). System would count as 2 distinct proofs. Mitigated by `proof_type` enum being coarse (`photo|document|text|url|receipt`) — two photos both get `proof_type='photo'`, counted as one. Accept this — it biases toward "CEO must send one photo per required proof kind", matches the `proof_required` array structure.

### OBJECTION 2 — Nag cron clock drift + job overlap

*Cerebras (AGREE) + gpt-4o-mini (AGREE):* Two GitHub Actions workflow instances racing on `atlas_nag_log`. If job N runs >4h (infrastructure delay), job N+1 starts while N still holds the DB connection; both read "last nag was X hours ago", both fire nags, CEO gets duplicates, `notifier.py`'s 6h cooldown is bypassed because it checks file-based `notification-log.jsonl` which is committed *after* the nag fires.

**COUNTER-EVIDENCE:** Fix applied at two layers:

1. Workflow layer — add `concurrency: { group: atlas-obligation-nag, cancel-in-progress: false }` to the workflow YAML. GitHub Actions refuses to start a second instance while one is running. `cancel-in-progress: false` is deliberate — we want the current nag to complete, not get killed mid-Telegram-API call.
2. DB layer — each obligation wraps its nag decision in `pg_advisory_xact_lock(hashtext('nag:' || obligation_id))`. If the workflow layer ever leaks (e.g., manual `workflow_dispatch` override), the DB lock holds the line.

**RESIDUAL RISK:** If GitHub Actions cancels workflow mid-flight (org-level cancel, billing limit), the advisory lock releases but the `atlas_nag_log` row is written before the Telegram `sendMessage` call completes. Log could show "nag fired" while CEO never saw it. Mitigated by writing the log AFTER the Telegram 200 response, not before. If Telegram errors out, no log row, next tick retries — at-least-once semantics are safer here than at-most-once.

### OBJECTION 3 — SECURITY DEFINER privilege escalation on `attach_proof`

*Cerebras (AGREE) + gpt-4o-mini (AGREE):* `attach_proof` uses `SECURITY DEFINER`, which runs with `service_role` privileges, bypassing RLS. A CEO-authenticated client calling the RPC with any `p_obligation_id` (including one owned by `tax-lawyer`) would close that obligation even though RLS would have blocked a direct UPDATE. Audit trail lies about who completed what.

**COUNTER-EVIDENCE:** Fix applied: ownership check inside the function body, before any write. Uses `current_setting('request.jwt.claims', true)::json ->> 'email'` to get the caller's email from the Supabase-injected claim, then validates against `v_obligation.owner`:
- If `v_obligation.owner IN ('CEO','both')` → caller must be CEO email.
- If `v_obligation.owner = 'Atlas'` → caller must be service_role (no `request.jwt.claims`).
- If `v_obligation.owner = 'tax-lawyer'` → reject from Telegram handler (covered in Phase 2 when lawyer credentials exist).

The RPC still needs `SECURITY DEFINER` because it writes to `atlas_proofs` (which CEO has no direct write access to by RLS). But the auth decision now lives in code, not in trust.

**RESIDUAL RISK:** Supabase admin with direct service_role key (i.e. me, Atlas, in future scripts) can still bypass the ownership check because `request.jwt.claims` is NULL for service_role. This is correct — Atlas the cron must be able to attach proofs on `Atlas`-owned obligations without impersonating a user. Documented as the intended privilege gradient.

---

## Problem

`memory/atlas/deadlines.md` is the current obligation tracker. It is markdown Atlas reads on wake. It has already drifted: line 29-36 says "Stripe Atlas auto-files 83(b)" with status "NOT TRIGGERED YET". `memory/atlas/company-state.md` says "DHL Express direct Баку → IRS is the SOLE path. Friend-fallback deprecated". These have been contradicting each other for days because Atlas can forget to read deadlines.md, and when he does read, he does not compare to company-state.md or force resolution.

Atlas also does not *nag* CEO. CEO must remember to ask "что у меня по срокам". There is no push channel where the obligation itself escalates until CEO attaches proof.

## What exists (reuse, do not duplicate)

| Layer | Exists at | Status |
|---|---|---|
| Telegram handler with HMAC + memory + multi-provider | `apps/api/app/routers/telegram_webhook.py` (1848 lines) | Live |
| CEO notification channel with vacation + 6h cooldown | `packages/swarm/notifier.py` + `memory/atlas/notification-log.jsonl` | Live |
| Admin panel with AdminGuard + AdminSidebar | `apps/web/src/app/[locale]/admin/` (layout.tsx, page.tsx, grievances/, swarm/, users/) | M1 shipped |
| Hourly cron pattern with commit-back | `.github/workflows/atlas-watchdog.yml` → `scripts/scheduled_workflow_watchdog.py` | Live |
| Daily digest at 23 UTC → 03 Baku | `.github/workflows/atlas-daily-digest.yml` → `scripts/atlas_daily_digest.py` | Live |
| Proactive loop architecture | `memory/atlas/proactive_loop.md` | Documented |
| Governance event logging | `zeus.governance_events` table + `log_governance_event` RPC | Live |

The obligation system plugs into these layers — it does not replace or shadow them.

## Gap (what must be built)

1. **Deterministic obligation store in Supabase** — markdown cannot be forgotten-resistant, a DB table with RLS is.
2. **Proof attachment mechanism over Telegram** — when CEO sends a photo/document to @volaurabot, the handler routes it to the matching open obligation, stores the artifact reference, and closes the obligation with proof.
3. **Escalating nag cron** — when an obligation is within N days and no proof attached, the cron fires Telegram pings with increasing cadence (14d → weekly, 7d → every 2 days, 3d → daily, 1d → twice daily, 0d → every 4h until CEO attaches proof or defers).
4. **Admin sub-route for CEO** — `/admin/obligations` lists all open obligations with countdown + proof-attached badges + manual defer/cancel actions.
5. **Migration from deadlines.md** — one-time seed so no data is lost, then `deadlines.md` becomes a read-only archive pointer to the DB.

## Data model

### Table: `public.atlas_obligations`

```sql
CREATE TABLE public.atlas_obligations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,                               -- "83(b) election DHL filing"
    description TEXT,                                  -- markdown, can include URLs
    category TEXT NOT NULL,                            -- legal | tax | funding | launch | compliance | other
    deadline TIMESTAMPTZ,                              -- hard date; NULL for "trigger-based"
    trigger_event TEXT,                                -- natural-language description of what fires it
    consequence_if_missed TEXT NOT NULL,               -- money/legal/reputation impact (forces priority)
    owner TEXT NOT NULL DEFAULT 'CEO',                 -- CEO | Atlas | tax-lawyer | both
    status TEXT NOT NULL DEFAULT 'open',               -- open | in_progress | completed | deferred | cancelled
    proof_required TEXT[] NOT NULL DEFAULT '{}',       -- ["DHL tracking number", "stamped mailing receipt photo"]
    nag_schedule TEXT NOT NULL DEFAULT 'standard',     -- standard | aggressive | silent
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    deferred_until TIMESTAMPTZ,                        -- if status=deferred, don't nag before this date
    source TEXT,                                       -- "deadlines.md:L29" or "CEO chat 2026-04-18" — provenance
    CONSTRAINT status_check CHECK (status IN ('open','in_progress','completed','deferred','cancelled')),
    CONSTRAINT owner_check CHECK (owner IN ('CEO','Atlas','tax-lawyer','both')),
    CONSTRAINT nag_check CHECK (nag_schedule IN ('standard','aggressive','silent'))
);

CREATE INDEX idx_obligations_open ON public.atlas_obligations (status, deadline)
    WHERE status IN ('open','in_progress');
CREATE INDEX idx_obligations_deferred ON public.atlas_obligations (deferred_until)
    WHERE status = 'deferred';
```

### Table: `public.atlas_proofs`

```sql
CREATE TABLE public.atlas_proofs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obligation_id UUID NOT NULL REFERENCES public.atlas_obligations(id) ON DELETE CASCADE,
    proof_type TEXT NOT NULL,                          -- photo | document | text | url | receipt
    telegram_file_id TEXT,                             -- if from Telegram upload
    telegram_file_unique_id TEXT,
    artifact_url TEXT,                                 -- Supabase Storage signed URL if migrated off Telegram
    text_content TEXT,                                 -- if proof is a pasted tracking number / URL
    submitted_by TEXT NOT NULL,                        -- 'CEO' | 'Atlas' | 'automated'
    submitted_via TEXT NOT NULL,                       -- 'telegram' | 'admin-ui' | 'api' | 'migration'
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    verified BOOLEAN NOT NULL DEFAULT false,
    verified_by TEXT,                                  -- 'CEO' | 'Atlas-LLM' | 'manual'
    verified_at TIMESTAMPTZ
);

CREATE INDEX idx_proofs_obligation ON public.atlas_proofs (obligation_id);

-- v2 fix (OBJECTION 1): dedupe Telegram webhook retries on file_id
CREATE UNIQUE INDEX idx_proofs_tg_file_unique
    ON public.atlas_proofs (obligation_id, telegram_file_id)
    WHERE telegram_file_id IS NOT NULL;
```

### Table: `public.atlas_nag_log`

```sql
CREATE TABLE public.atlas_nag_log (
    id BIGSERIAL PRIMARY KEY,
    obligation_id UUID NOT NULL REFERENCES public.atlas_obligations(id) ON DELETE CASCADE,
    fired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    telegram_message_id BIGINT,
    telegram_chat_id BIGINT NOT NULL,
    cadence_tier TEXT NOT NULL,                        -- 'weekly' | '2days' | 'daily' | '2x-daily' | '4h'
    days_until_deadline INTEGER,                       -- negative = past due
    ceo_responded BOOLEAN NOT NULL DEFAULT false,
    ceo_response_at TIMESTAMPTZ
);

CREATE INDEX idx_nag_log_obligation ON public.atlas_nag_log (obligation_id, fired_at DESC);
```

### RLS

```sql
ALTER TABLE public.atlas_obligations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.atlas_proofs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.atlas_nag_log      ENABLE ROW LEVEL SECURITY;

-- Only service_role and CEO (by email claim) can access. No public read.
CREATE POLICY "service_role_all_obligations" ON public.atlas_obligations
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "ceo_read_obligations" ON public.atlas_obligations
    FOR SELECT TO authenticated
    USING (auth.jwt() ->> 'email' = 'ganbarov.y@gmail.com');
-- repeat for proofs, nag_log
```

### RPC: `open_obligation`, `attach_proof`, `defer_obligation`, `cancel_obligation`

```sql
CREATE OR REPLACE FUNCTION public.attach_proof(
    p_obligation_id UUID,
    p_proof_type TEXT,
    p_telegram_file_id TEXT DEFAULT NULL,
    p_text_content TEXT DEFAULT NULL,
    p_submitted_via TEXT DEFAULT 'telegram'
) RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public     -- v2: pin search_path (SECURITY DEFINER best practice)
AS $$
DECLARE
    v_obligation public.atlas_obligations%ROWTYPE;
    v_proof_id UUID;
    v_distinct_proof_count INT;
    v_required_count INT;
    v_caller_email TEXT;
    v_is_service_role BOOLEAN;
BEGIN
    -- v2 fix (OBJECTION 1): serialize concurrent webhook retries on this obligation
    PERFORM pg_advisory_xact_lock(hashtext(p_obligation_id::text));

    SELECT * INTO v_obligation
        FROM public.atlas_obligations
        WHERE id = p_obligation_id
        FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Obligation not found' USING ERRCODE = 'P0002';
    END IF;
    IF v_obligation.status IN ('completed','cancelled') THEN
        -- idempotent: a second webhook retry after close is a no-op, not a failure
        RETURN json_build_object(
            'obligation_id', p_obligation_id,
            'already_closed', true,
            'status', v_obligation.status
        );
    END IF;

    -- v2 fix (OBJECTION 3): ownership check lives in code because SECURITY DEFINER bypasses RLS
    v_caller_email := current_setting('request.jwt.claims', true)::json ->> 'email';
    v_is_service_role := (v_caller_email IS NULL);  -- service_role has no JWT claims

    IF NOT v_is_service_role THEN
        IF v_obligation.owner IN ('CEO','both') THEN
            IF v_caller_email <> 'ganbarov.y@gmail.com' THEN
                RAISE EXCEPTION 'Not authorized: obligation owner=% but caller=%',
                    v_obligation.owner, v_caller_email USING ERRCODE = '42501';
            END IF;
        ELSIF v_obligation.owner = 'Atlas' THEN
            RAISE EXCEPTION 'Atlas-owned obligation, only cron/service_role may close'
                USING ERRCODE = '42501';
        ELSIF v_obligation.owner = 'tax-lawyer' THEN
            RAISE EXCEPTION 'tax-lawyer-owned obligation not supported yet (Phase 2)'
                USING ERRCODE = '42501';
        END IF;
    END IF;

    -- v2 fix (OBJECTION 1): idempotent insert — duplicate webhook retry returns existing row
    INSERT INTO public.atlas_proofs (
        obligation_id, proof_type, telegram_file_id, text_content,
        submitted_by, submitted_via, verified, verified_by, verified_at
    ) VALUES (
        p_obligation_id, p_proof_type, p_telegram_file_id, p_text_content,
        CASE WHEN v_is_service_role THEN 'Atlas' ELSE 'CEO' END,
        p_submitted_via, true,
        CASE WHEN v_is_service_role THEN 'Atlas' ELSE 'CEO' END,
        now()
    )
    ON CONFLICT (obligation_id, telegram_file_id) WHERE telegram_file_id IS NOT NULL
    DO UPDATE SET submitted_at = atlas_proofs.submitted_at   -- no-op update forces RETURNING
    RETURNING id INTO v_proof_id;

    -- v2 fix (OBJECTION 1): count DISTINCT proof_type values, not raw rows
    SELECT count(DISTINCT proof_type)
        INTO v_distinct_proof_count
        FROM public.atlas_proofs
        WHERE obligation_id = p_obligation_id AND verified;

    v_required_count := coalesce(array_length(v_obligation.proof_required, 1), 1);

    IF v_distinct_proof_count >= v_required_count THEN
        UPDATE public.atlas_obligations
            SET status = 'completed', completed_at = now(), updated_at = now()
            WHERE id = p_obligation_id AND status IN ('open','in_progress');
    END IF;

    RETURN json_build_object(
        'proof_id', v_proof_id,
        'obligation_id', p_obligation_id,
        'distinct_proofs', v_distinct_proof_count,
        'required', v_required_count,
        'closed', v_distinct_proof_count >= v_required_count
    );
END;
$$;

-- Allow authenticated (CEO JWT) + service_role to execute
REVOKE ALL ON FUNCTION public.attach_proof FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.attach_proof TO authenticated, service_role;
```

## Telegram handler

New function inside existing `apps/api/app/routers/telegram_webhook.py`:

```python
async def _handle_proof_upload(update: dict, supabase) -> None:
    """When CEO sends a photo/document/text-with-tracking-number, try to route to open obligation."""
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    if str(chat_id) != settings.telegram_ceo_chat_id:
        return  # silent drop — hard security invariant

    # 1. Detect kind of proof in the incoming message
    proof_kind, file_id, text_content = _detect_proof_kind(msg)
    if not proof_kind:
        return  # not a proof, let normal Atlas flow handle it

    # 2. Get open obligations, most urgent first
    open_obs = await supabase.rpc("list_open_obligations").execute()
    if not open_obs.data:
        await _send_message(chat_id, "Нет открытых обязательств. Не знаю куда прикрепить.")
        return

    # 3. If more than one, ask CEO (inline keyboard with obligation titles)
    if len(open_obs.data) > 1:
        kb = _build_obligation_picker_kb(open_obs.data, file_id or text_content[:64])
        await _send_message(chat_id, "К какому обязательству приложить?", reply_markup=kb)
        return

    # 4. Single candidate — attach directly
    obligation = open_obs.data[0]
    await supabase.rpc("attach_proof", {
        "p_obligation_id": obligation["id"],
        "p_proof_type": proof_kind,
        "p_telegram_file_id": file_id,
        "p_text_content": text_content,
    }).execute()
    await _send_message(chat_id, f"Принято. {obligation['title']} — закрыто с доказательством.")
```

Inline-keyboard callback handler: `obligation-attach:{obligation_id}:{proof_cache_key}` — when CEO taps, runs `attach_proof`.

## Nag cron

New workflow `.github/workflows/atlas-obligation-nag.yml`:

```yaml
name: Atlas Obligation Nag
on:
  schedule:
    - cron: '37 */4 * * *'   # every 4h at min 37 (avoid fleet-wide :00 alignment)
  workflow_dispatch:
permissions:
  contents: write             # for notification-log.jsonl commit-back
concurrency:                  # v2 fix (OBJECTION 2): workflow-layer single-writer
  group: atlas-obligation-nag
  cancel-in-progress: false   # let in-flight nag finish rather than kill mid-Telegram-send
jobs:
  nag:
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install supabase loguru
      - name: Run obligation nag
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CEO_CHAT_ID: ${{ secrets.TELEGRAM_CEO_CHAT_ID }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: python scripts/atlas_obligation_nag.py
      - name: Commit nag log
        run: |
          git config user.name "Atlas Nag"
          git config user.email "atlas-nag@volaura.app"
          [ -f memory/atlas/notification-log.jsonl ] && git add memory/atlas/notification-log.jsonl || true
          git diff --staged --quiet || git commit -m "atlas-nag: tick $(date -u +%Y-%m-%dT%H:%M)"
          git pull --rebase --autostash origin main || true
          git push || true
```

Script `scripts/atlas_obligation_nag.py`:
- Query `atlas_obligations` WHERE status IN ('open','in_progress') AND (deferred_until IS NULL OR deferred_until < now())
- For each: compute days_until = (deadline - now()).days (negative = past due)
- Map to cadence tier:
  - days > 14 → skip unless first entry (no nag)
  - 7 < days ≤ 14 → weekly cadence (skip if last nag < 7 days ago)
  - 3 < days ≤ 7 → every 2 days
  - 1 < days ≤ 3 → daily
  - 0 < days ≤ 1 → twice daily
  - days ≤ 0 → every 4h (every tick)
- Check `atlas_nag_log` for last fire; respect cadence + existing `notifier.py` vacation + 6h cooldown gates
- **v2 fix (OBJECTION 2): DB-layer single-writer** — before the nag decision for an obligation, acquire `pg_advisory_xact_lock(hashtext('nag:' || obligation_id::text))`. If lock unavailable, skip this obligation this tick (another worker holds it).
- Send Telegram message with inline-keyboard: [ Приложить доказательство ] [ Отложить на 7 дней ] [ Выполнено без доказательства ]
- **v2 fix (OBJECTION 2): at-least-once semantics** — insert `atlas_nag_log` row AFTER Telegram `sendMessage` returns 200. If Telegram errors, no log row is written, next tick retries. Never write the log optimistically.

## Admin sub-route

`apps/web/src/app/[locale]/admin/obligations/page.tsx` — client component using existing TanStack Query patterns. Follows same shape as `grievances/page.tsx`.

Sections:
1. Summary scorecard — count open / at-risk (< 14d) / past-due / completed last 30d
2. Table of open obligations — title, category, deadline countdown (colour: green > 30d, amber 7-30d, orange 1-7d, purple past-due per 5 Foundation Laws), proof_required list, proof_attached badge count, inline [Defer] [Cancel] actions
3. Recent proofs feed — last 20 submissions

All data via Supabase client, not API router. RLS enforces CEO-only access per email claim.

## Migration from deadlines.md

One-time script `scripts/seed_atlas_obligations.py` runs once during migration deployment:

```python
SEEDS = [
    {
        "title": "83(b) election — DHL Express Baku → IRS",
        "category": "tax",
        "deadline": "2026-05-14",  # 30 days post-incorporation (2026-04-14)
        "consequence_if_missed": "Future equity appreciation taxed as ordinary income at vesting. "
                                 "For $7M post-money 85% CEO stake — 7-figure ordinary-income penalty over 4yr vest.",
        "owner": "CEO",
        "proof_required": [
            "DHL Express tracking number Baku → IRS",
            "Photo of postmarked envelope (Apr 28 or earlier)",
            "Photo of IRS delivery confirmation",
        ],
        "nag_schedule": "aggressive",
        "source": "deadlines.md L29 + company-state.md 2026-04-18",
    },
    {
        "title": "ITIN application — IRS Form W-7",
        "category": "tax",
        "deadline": None,
        "trigger_event": "Run in parallel with Stripe Atlas filing (processing ~6 weeks)",
        "consequence_if_missed": "~6 week delay on any program payout requiring ITIN/SSN (most do).",
        "owner": "CEO",
        "proof_required": ["W-7 submission confirmation", "ITIN letter from IRS"],
        "nag_schedule": "standard",
        "source": "deadlines.md L38",
    },
    {
        "title": "WUF13 Baku — VOLAURA launch readiness",
        "category": "launch",
        "deadline": "2026-06-13",
        "consequence_if_missed": "No alternative launch moment with equivalent AZ-local media weight. "
                                 "Next window ~12 months.",
        "owner": "both",
        "proof_required": [
            "All P0 items in docs/PRE-LAUNCH-BLOCKERS-STATUS.md closed",
            "WUF13 registration + badge confirmation",
        ],
        "nag_schedule": "standard",
        "source": "deadlines.md L22",
    },
    # GITA grant (NOT PURSUING) and Provisional Patent (deferred) — seeded as status='deferred'
]
```

After seed, `deadlines.md` gets a header banner: `# DEPRECATED 2026-04-18 — see atlas_obligations table, admin/obligations`. File stays as history.

Resolves the 83(b) drift: the new canonical row is "DHL Express Baku → IRS" with concrete proof requirements, marking the old Stripe-Atlas auto-file assumption as historical.

## Atlas wake-loop integration

Update `memory/atlas/wake.md` read order: after breadcrumb + heartbeat, Atlas calls (via Supabase MCP or direct SDK) `SELECT * FROM atlas_obligations WHERE status IN ('open','in_progress') ORDER BY deadline ASC NULLS LAST` and surfaces anything within 14 days. This replaces the `deadlines.md` read step — the DB is now the source.

If the Supabase call fails, Atlas falls back to reading `memory/atlas/deadlines.md` (which is deprecated-but-present) and flags the failure.

## Acceptance criteria

DONE when:
1. Migration applied, 4 rows seeded from deadlines.md, no RLS errors
2. `scripts/atlas_obligation_nag.py` runs successfully in CI, inserts at least one `atlas_nag_log` row for 83(b) obligation (deadline ~4 weeks away → weekly cadence)
3. CEO sends a photo to @volaurabot, handler attaches it to the single open obligation (or single-obligation test), `atlas_proofs` row created, obligation either advances to in_progress or closes depending on count
4. `/admin/obligations` renders without type-check errors (`pnpm type-check` green)
5. `deadlines.md` has DEPRECATED banner + pointer to DB
6. `memory/atlas/wake.md` updated with new source-of-truth

## Out of scope (Phase 2)

- Photo OCR to auto-extract tracking numbers
- LLM verification of proof authenticity (Gemini Vision)
- SMS fallback when Telegram is down
- Email fallback for non-Telegram obligations
- Integration with `character_events` bus (obligation_created / obligation_closed events)

---

## Delegation plan

**Opus (me):** this spec + external critique + CEO report.
**Sonnet via Agent tool:** write the migration file, handler function, workflow yaml, nag script, admin page.tsx — all from this spec inline.

Agent prompt is self-contained: "Read this spec file, implement files 1-6, commit". No strategic branching needed.

**Status (v2, 17:00 Baku):** Adversarial critique complete. Three structural fixes applied inline (unique index + advisory locks + owner check). Ready for Sonnet.

## Files Sonnet must produce

1. `supabase/migrations/20260418170000_atlas_obligations.sql` — full DDL from §Data-model, RLS policies for `atlas_proofs` + `atlas_nag_log` (mirror the pattern shown for `atlas_obligations`), grants.
2. `apps/api/app/routers/telegram_webhook.py` — add `_handle_proof_upload`, `_detect_proof_kind`, `_build_obligation_picker_kb` near the existing dispatcher. Route photo/document messages to it BEFORE falling through to the normal Atlas LLM flow. Wire inline-keyboard callback handler for `obligation-attach:{id}:{cache_key}`.
3. `.github/workflows/atlas-obligation-nag.yml` — exactly as shown in §Nag-cron with the `concurrency` block.
4. `scripts/atlas_obligation_nag.py` — stdlib-only (urllib for Telegram), reads Supabase via the `supabase` Python SDK, implements the cadence map, acquires advisory locks, commits `notification-log.jsonl` delta.
5. `scripts/seed_atlas_obligations.py` — one-shot seed with the 4 rows shown in §Migration-from-deadlines.md. Idempotent: `ON CONFLICT (title) DO NOTHING` (add `UNIQUE (title)` to migration if not already there).
6. `apps/web/src/app/[locale]/admin/obligations/page.tsx` — client component matching the shape of `apps/web/src/app/[locale]/admin/grievances/page.tsx`. TanStack Query fetch via Supabase client, shadcn Table, same design tokens.

## Acceptance for Sonnet handoff

Sonnet reports back with: paths + line counts + `pnpm type-check` result. No deployment. Opus reviews diff, then the deployment is a separate Bash step (`supabase db push` + `git commit` + `gh secret set`).
