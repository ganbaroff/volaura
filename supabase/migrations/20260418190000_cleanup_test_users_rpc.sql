-- cleanup_test_users() — prod hygiene RPC
-- Removes E2E test accounts (*@test.volaura.app) via CASCADE through FK relationships.
-- SECURITY DEFINER + service_role-only grant: no RLS bypass for regular users.

CREATE OR REPLACE FUNCTION public.cleanup_test_users()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  -- Capture IDs before delete so we can count them.
  WITH deleted AS (
    DELETE FROM auth.users
    WHERE email LIKE '%@test.volaura.app'
    RETURNING id
  )
  SELECT count(*)::INTEGER INTO deleted_count FROM deleted;

  RETURN deleted_count;
END;
$$;

-- Revoke from PUBLIC and roles that should not call this.
REVOKE ALL ON FUNCTION public.cleanup_test_users() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.cleanup_test_users() FROM anon;
REVOKE ALL ON FUNCTION public.cleanup_test_users() FROM authenticated;

-- Only service_role may execute.
GRANT EXECUTE ON FUNCTION public.cleanup_test_users() TO service_role;

COMMENT ON FUNCTION public.cleanup_test_users() IS
  'Deletes auth.users rows with email matching %@test.volaura.app (E2E test accounts). '
  'Returns count of deleted rows. Callable by service_role only. '
  'FK child rows are removed via ON DELETE CASCADE defined on each child table.';
