-- Companion to 20260328000040: COMMENT + GRANT + REVOKE for deduct_crystals_atomic.
-- Separated to avoid Supabase CLI "cannot insert multiple commands into a prepared
-- statement" error that occurs when CREATE OR REPLACE FUNCTION and GRANT appear
-- in the same migration file on supabase start (local CI).

COMMENT ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) IS
'P0-3 fix: Atomic crystal deduction with advisory lock. Prevents double-spend TOCTOU race on game_crystal_ledger.';

-- Only service_role (backend) can call this — never anon or authenticated directly
GRANT EXECUTE ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) TO service_role;
REVOKE EXECUTE ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.deduct_crystals_atomic(UUID, INT, TEXT, TEXT) FROM authenticated;
