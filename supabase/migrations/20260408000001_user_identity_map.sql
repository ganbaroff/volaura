-- Sprint E2.D.1 — cross-project user identity mapping
-- ADR-006 Option D: bridge MindShift (standalone project) ↔ VOLAURA (shared project)
--
-- Problem: MindShift auth.users live in standalone project awfoqycoltvhamtrsvxk.
-- VOLAURA character_events.user_id references auth.users in shared project
-- dwdgzfusjsobnixgyzjk. JWTs from MindShift are not valid against VOLAURA.
--
-- Solution: per MindShift-Claude's verified Option D plan, maintain a mapping table.
-- When a MindShift user first hits VOLAURA, we create a shadow auth.users entry
-- in shared project (email-linked) and store the mapping here. All subsequent
-- character_events use the shared_user_id.
--
-- This file creates:
--   1. public.user_identity_map — the mapping table
--   2. RLS policy — deny all user-scoped access (only service role writes)
--   3. Indexes for lookup by standalone_user_id and by email

CREATE TABLE IF NOT EXISTS public.user_identity_map (
    -- Composite primary key: same standalone user id could theoretically exist
    -- in multiple projects (unlikely but makes the key semantically complete).
    standalone_user_id TEXT NOT NULL,
    standalone_project_ref TEXT NOT NULL,

    -- Shared project user (VOLAURA auth.users) — the canonical ID used by all
    -- character_events rows. FK ensures we never orphan a mapping.
    shared_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Email at time of mapping. Used for shadow user creation and lookup.
    -- Not a FK because email can change but the mapping persists.
    email TEXT NOT NULL,

    -- Origin metadata — useful for debugging / audit
    source_product TEXT NOT NULL DEFAULT 'mindshift',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (standalone_user_id, standalone_project_ref)
);

-- Lookup by email (used when checking for existing shared user before create)
CREATE INDEX IF NOT EXISTS idx_user_identity_map_email
    ON public.user_identity_map(email);

-- Lookup by shared_user_id (used by audit / debug tools)
CREATE INDEX IF NOT EXISTS idx_user_identity_map_shared
    ON public.user_identity_map(shared_user_id);

-- Lookup by standalone project (used for ops — "show me all mindshift users")
CREATE INDEX IF NOT EXISTS idx_user_identity_map_project
    ON public.user_identity_map(standalone_project_ref, created_at DESC);

-- Comments for future readers
COMMENT ON TABLE public.user_identity_map IS
    'Cross-project user identity bridge for ADR-006 Option D. Maps users from standalone Supabase projects (e.g. MindShift) to shared project auth.users. Only the backend bridge endpoint writes here.';

COMMENT ON COLUMN public.user_identity_map.standalone_user_id IS
    'auth.users.id from the originating project (TEXT because Supabase uses UUID but we keep it flexible for non-Supabase sources).';

COMMENT ON COLUMN public.user_identity_map.standalone_project_ref IS
    'Supabase project ref of the originating project (e.g. awfoqycoltvhamtrsvxk for MindShift).';

COMMENT ON COLUMN public.user_identity_map.shared_user_id IS
    'The canonical auth.users.id in the shared project that all cross-product events should reference.';

-- ============================================================
-- RLS — deny all direct client access, only service role writes
-- ============================================================
ALTER TABLE public.user_identity_map ENABLE ROW LEVEL SECURITY;

-- No user-scoped policies. This means:
--   - anon/authenticated clients cannot SELECT, INSERT, UPDATE, or DELETE
--   - only service_role (backend) can touch this table
--   - users cannot see other users' mappings (would leak email → uid)
--
-- The ONLY writer is the /api/auth/from_external endpoint which uses the
-- service role client. Readers are ops tools using the service role as well.
--
-- If a user-scoped read is ever needed, add:
--   CREATE POLICY "own_mapping_read" ON public.user_identity_map
--     FOR SELECT USING (shared_user_id = auth.uid());
-- But for now, no client needs this — MindShift edge function goes through
-- the bridge endpoint which returns only the shared_user_id, nothing else.
