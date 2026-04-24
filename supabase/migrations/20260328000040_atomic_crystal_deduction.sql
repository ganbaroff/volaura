-- =============================================================================
-- P0-3: Atomic crystal deduction — advisory lock prevents TOCTOU double-spend
-- Session 53 | 2026-03-28
-- =============================================================================
-- Problem: character.py lines 66-82 SELECT balance then INSERT deduction in two
--          separate async calls. Concurrent requests can both pass the check and
--          both insert, causing a negative balance (double-spend).
-- Fix:     PostgreSQL advisory lock scoped to user_id ensures only ONE crystal_spent
--          transaction can proceed per user at a time. SELECT + INSERT are atomic.
-- =============================================================================

CREATE OR REPLACE FUNCTION public.deduct_crystals_atomic(
    p_user_id    UUID,
    p_amount     INT,
    p_source     TEXT,
    p_reference_id TEXT
)
RETURNS TABLE (
    success      BOOLEAN,
    new_balance  INT,
    error_code   TEXT,
    error_msg    TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_balance    INT;
    v_lock_key   BIGINT;
BEGIN
    -- Derive a stable per-user lock key from the UUID (fits in bigint)
    v_lock_key := ('x' || substr(md5(p_user_id::text), 1, 16))::bit(64)::bigint;

    -- Acquire session-level advisory lock (blocks concurrent crystal_spent for same user)
    PERFORM pg_advisory_lock(v_lock_key);

    -- Read balance INSIDE the lock — no other session can insert for this user yet
    SELECT COALESCE(SUM(amount), 0)
    INTO   v_balance
    FROM   public.game_crystal_ledger
    WHERE  user_id = p_user_id;

    -- Check balance
    IF v_balance < p_amount THEN
        PERFORM pg_advisory_unlock(v_lock_key);
        RETURN QUERY SELECT
            FALSE,
            v_balance,
            'INSUFFICIENT_CRYSTALS'::TEXT,
            format('Cannot spend %s crystals — balance is %s', p_amount, v_balance);
        RETURN;
    END IF;

    -- Deduct: insert negative amount into ledger (atomic with the check above)
    INSERT INTO public.game_crystal_ledger (user_id, amount, source, reference_id)
    VALUES (p_user_id, -p_amount, p_source, p_reference_id);

    v_balance := v_balance - p_amount;

    -- Release lock
    PERFORM pg_advisory_unlock(v_lock_key);

    RETURN QUERY SELECT TRUE, v_balance, NULL::TEXT, NULL::TEXT;

EXCEPTION WHEN OTHERS THEN
    -- Always release lock on error to prevent deadlock
    PERFORM pg_advisory_unlock(v_lock_key);
    RAISE;
END;
$$;

COMMENT ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) IS 'P0-3 fix (Session 53): Atomic crystal deduction with advisory lock. Prevents double-spend TOCTOU race on game_crystal_ledger. Session-level lock ensures SELECT + INSERT are atomic per user.';

-- Only service_role (backend) can call this — never anon or authenticated directly
GRANT EXECUTE ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) TO service_role;
REVOKE EXECUTE ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) FROM authenticated;
