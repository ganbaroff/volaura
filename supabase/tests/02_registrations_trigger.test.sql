-- pgTAP: the 20260415124500 trigger must block the ghost-audit §2.1 injection
-- (volunteer sneaks coordinator_rating / check_in_code through a status=cancelled UPDATE).
--
-- Research: docs/research/rls-testing/summary.md §"Proposed 1-week adoption path" Day 2
-- test 010-registrations-volunteer-update.
--
-- We simulate an authenticated volunteer by spoofing `request.jwt.claim.sub` and
-- setting role to `authenticated`. The row is inserted as postgres so RLS does not
-- block the fixture. Then each assertion runs as the volunteer owner.

BEGIN;

SELECT plan(5);

-- ── fixture ──────────────────────────────────────────────────────────────────
-- UUIDs hard-coded for determinism. Event + volunteer seeded minimally.

-- Event (bypasses FK to profiles/orgs by using service-owned fixture UUIDs).
-- We use a synthetic org + event + registration owned by volunteer_id.
DO $$
DECLARE
    v_vol UUID := '11111111-1111-1111-1111-111111111111';
    v_org UUID := '22222222-2222-2222-2222-222222222222';
    v_evt UUID := '33333333-3333-3333-3333-333333333333';
    v_reg UUID := '44444444-4444-4444-4444-444444444444';
BEGIN
    -- Seed auth.users — required for profiles FK + organizations.owner_id FK.
    INSERT INTO auth.users (id, email, aud, role, created_at, updated_at, encrypted_password)
        VALUES (v_vol, 'pgtap_vol@test.internal', 'authenticated', 'authenticated',
                now(), now(), '')
        ON CONFLICT (id) DO NOTHING;

    -- Seed profiles — volunteer_id FK. account_type must be valid per CHECK constraint.
    INSERT INTO public.profiles (id, username, account_type)
        VALUES (v_vol, 'pgtap_test_volunteer', 'professional')
        ON CONFLICT (id) DO NOTHING;

    -- Seed org — owner_id is NOT NULL FK to auth.users(id).
    INSERT INTO public.organizations (id, name, owner_id)
        VALUES (v_org, '__pgtap_test_org__', v_vol)
        ON CONFLICT (id) DO NOTHING;

    -- Seed event — column names: organization_id, title_en/az (both NOT NULL), start_date/end_date.
    INSERT INTO public.events (id, organization_id, title_en, title_az, start_date, end_date)
        VALUES (v_evt, v_org, '__pgtap_test_event__', '__pgtap_test_event__', now(), now() + interval '2 hours')
        ON CONFLICT (id) DO NOTHING;

    -- status CHECK: ('pending','approved','rejected','waitlisted','cancelled') — 'confirmed' is invalid.
    INSERT INTO public.registrations (id, event_id, volunteer_id, status)
        VALUES (v_reg, v_evt, v_vol, 'approved')
        ON CONFLICT (id) DO NOTHING;
END $$;

-- Switch to volunteer identity.
SELECT set_config('request.jwt.claim.sub', '11111111-1111-1111-1111-111111111111', true);
SET LOCAL ROLE authenticated;

-- ── assertions ───────────────────────────────────────────────────────────────

-- 1. Allowed: volunteer cancels the registration — only status changes.
SELECT lives_ok(
    $$UPDATE public.registrations
         SET status = 'cancelled'
       WHERE id = '44444444-4444-4444-4444-444444444444'$$,
    'volunteer can cancel (only status changes) — trigger allows'
);

-- 2. Blocked: sneaky coordinator_rating injection under cover of cancellation.
SELECT throws_ok(
    $$UPDATE public.registrations
         SET status = 'cancelled',
             coordinator_rating = 5,
             coordinator_feedback = 'self-rated'
       WHERE id = '44444444-4444-4444-4444-444444444444'$$,
    '42501',
    NULL,
    'volunteer CANNOT set coordinator_rating via cancel-UPDATE — trigger raises'
);

-- 3. Blocked: check_in_code fabrication.
SELECT throws_ok(
    $$UPDATE public.registrations
         SET status = 'cancelled',
             check_in_code = 'FORGED'
       WHERE id = '44444444-4444-4444-4444-444444444444'$$,
    '42501',
    NULL,
    'volunteer CANNOT set check_in_code via cancel-UPDATE — trigger raises'
);

-- 4. Blocked: changing volunteer_id (handover to another user).
SELECT throws_ok(
    $$UPDATE public.registrations
         SET status = 'cancelled',
             volunteer_id = '99999999-9999-9999-9999-999999999999'
       WHERE id = '44444444-4444-4444-4444-444444444444'$$,
    '42501',
    NULL,
    'volunteer CANNOT reassign volunteer_id via cancel-UPDATE — trigger raises'
);

-- 5. Allowed: non-volunteer caller (service role / other path) updates coordinator_rating.
RESET ROLE;
SELECT set_config('request.jwt.claim.sub', '', true);
SELECT lives_ok(
    $$UPDATE public.registrations
         SET coordinator_rating = 4
       WHERE id = '44444444-4444-4444-4444-444444444444'$$,
    'non-volunteer caller can set coordinator_rating — trigger passes through'
);

SELECT * FROM finish();
ROLLBACK;
