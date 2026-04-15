-- Tighten volunteer UPDATE on public.registrations — ghost-audit 2026-04-15 P1
--
-- Prior state (20260324000015_rls_audit_fixes.sql FIX C7):
--   Volunteer UPDATE policy had `WITH CHECK (status = 'cancelled')`.
--   This only guards the status column. A volunteer could run:
--     UPDATE registrations SET status = 'cancelled',
--       coordinator_rating = 5, coordinator_feedback = 'perfect', check_in_code = 'X'
--     WHERE id = :my_row_id;
--   and RLS accepted it — opening self-rating injection and check-in code fabrication.
--   The policy comment even said "All other fields must be unchanged (enforced at
--   application layer too)" but the application layer gate does not cover direct
--   PostgREST / mobile-client access.
--
-- Fix: add a BEFORE UPDATE trigger that, when the updater is the volunteer owner
-- of the row, raises unless ONLY `status` has actually changed value.
--
-- Why trigger, not WITH CHECK: PostgreSQL RLS WITH CHECK can only reference NEW,
-- not OLD — there is no first-class way to express "NEW = OLD except for column X".
-- Triggers are the idiomatic workaround.
--
-- The trigger is defensive: org-owner updates, admin RPC, system updates all
-- continue to work because they are not `auth.uid() = volunteer_id`.

CREATE OR REPLACE FUNCTION public._enforce_volunteer_update_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    -- Only constrain volunteers acting on their own row. Other callers
    -- (org owners, service role, RPCs with SECURITY DEFINER) pass through.
    IF auth.uid() IS NULL OR auth.uid() <> NEW.volunteer_id THEN
        RETURN NEW;
    END IF;

    -- Volunteers may only flip status to 'cancelled'. No other column may change.
    IF NEW.event_id           IS DISTINCT FROM OLD.event_id
       OR NEW.volunteer_id    IS DISTINCT FROM OLD.volunteer_id
       OR NEW.professional_id IS DISTINCT FROM OLD.professional_id
       OR NEW.registered_at   IS DISTINCT FROM OLD.registered_at
       OR NEW.checked_in_at   IS DISTINCT FROM OLD.checked_in_at
       OR NEW.check_in_code   IS DISTINCT FROM OLD.check_in_code
       OR NEW.coordinator_rating    IS DISTINCT FROM OLD.coordinator_rating
       OR NEW.coordinator_feedback  IS DISTINCT FROM OLD.coordinator_feedback
       OR NEW.coordinator_rated_at  IS DISTINCT FROM OLD.coordinator_rated_at
       OR NEW.no_show_reason        IS DISTINCT FROM OLD.no_show_reason
       OR NEW.cancellation_hours_before IS DISTINCT FROM OLD.cancellation_hours_before
       OR NEW.metadata        IS DISTINCT FROM OLD.metadata
    THEN
        RAISE EXCEPTION
            'Volunteers can only cancel their registration — other columns are read-only. Blocked column change detected.'
            USING ERRCODE = '42501', HINT = 'Use the dedicated rating / feedback endpoints instead of direct UPDATE.';
    END IF;

    -- Volunteer feedback columns (volunteer_rating / volunteer_feedback /
    -- volunteer_rated_at) are intentionally permitted here because they represent
    -- the volunteer's own review — separate from coordinator_* which is the
    -- org's review of them. If a future change wants to lock these behind a
    -- dedicated /ratings endpoint, add them to the IS DISTINCT list above.

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS enforce_volunteer_update_scope ON public.registrations;

CREATE TRIGGER enforce_volunteer_update_scope
    BEFORE UPDATE ON public.registrations
    FOR EACH ROW
    EXECUTE FUNCTION public._enforce_volunteer_update_scope();

COMMENT ON FUNCTION public._enforce_volunteer_update_scope IS
    'Ghost-audit 2026-04-15 P1 — prevents volunteer self-rating injection via direct UPDATE. Volunteers may only change status column on their own registration row; all other columns must match OLD. See migration 20260415124500.';
