-- Companion to 20260328000040: COMMENT + GRANT + REVOKE for deduct_crystals_atomic.
-- Wrapped in a DO block so the entire file is ONE SQL statement.
-- Supabase CLI raises SQLSTATE 42601 when COMMENT/GRANT/REVOKE appear as separate
-- top-level statements in the same migration file (extended query protocol limitation).

DO $$
BEGIN
    EXECUTE $sql$
        COMMENT ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) IS
        'P0-3 fix: Atomic crystal deduction with advisory lock. Prevents double-spend TOCTOU race on game_crystal_ledger.'
    $sql$;

    -- Only service_role (backend) can call this — never anon or authenticated directly
    EXECUTE 'GRANT EXECUTE ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) TO service_role';
    EXECUTE 'REVOKE EXECUTE ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) FROM PUBLIC';
    EXECUTE 'REVOKE EXECUTE ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) FROM authenticated';
END $$;
