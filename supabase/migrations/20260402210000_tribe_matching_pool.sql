-- Tribe Matching Pool
-- Persists "waiting for tribe match" state so users see "Finding your tribe..."
-- on refresh instead of the join CTA appearing again.
--
-- Lifecycle:
--   INSERT: user calls POST /api/tribes/join-pool (eligibility verified first)
--   DELETE: tribe_matching.py clears rows after successful match
--   The matching service uses service_role to DELETE (RLS bypass).

CREATE TABLE IF NOT EXISTS public.tribe_matching_pool (
    user_id   UUID        PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for matching service: process oldest-waiting users first
CREATE INDEX IF NOT EXISTS idx_tribe_matching_pool_joined_at
    ON public.tribe_matching_pool (joined_at);

ALTER TABLE public.tribe_matching_pool ENABLE ROW LEVEL SECURITY;

-- User can read their own pool status (for GET /me/pool-status)
CREATE POLICY "Users can read own pool status"
ON public.tribe_matching_pool FOR SELECT
USING (auth.uid() = user_id);

-- User can insert themselves (via POST /join-pool with their JWT)
CREATE POLICY "Users can join pool"
ON public.tribe_matching_pool FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- User can remove themselves (leave the pool without joining a tribe)
CREATE POLICY "Users can leave pool"
ON public.tribe_matching_pool FOR DELETE
USING (auth.uid() = user_id);

-- No UPDATE policy: joined_at is immutable (service_role uses DELETE+INSERT if needed)
