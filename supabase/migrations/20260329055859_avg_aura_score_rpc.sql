-- ============================================================
-- avg_aura_score() — server-side aggregation for public stats
-- Session 64 | 2026-03-29
-- ============================================================
-- Problem: stats.py computed avg by fetching ALL aura_scores rows into Python memory,
--          then running sum()/len() — O(n) bandwidth + memory, wrong results at scale.
-- Fix:     PostgreSQL AVG() aggregates in-database — single float returned, no row transfer.
-- ============================================================

CREATE OR REPLACE FUNCTION public.avg_aura_score()
RETURNS FLOAT
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT ROUND(AVG(total_score)::NUMERIC, 1)::FLOAT
    FROM public.aura_scores
    WHERE total_score IS NOT NULL;
$$;

COMMENT ON FUNCTION public.avg_aura_score IS
    'Session 64: Returns platform-wide average AURA score as a single float. '
    'Used by /api/stats/public. O(1) bandwidth vs old O(n) Python fetch. '
    'Returns NULL if no scores exist (caller defaults to 0.0).';

-- Allow anon + authenticated + service_role (called by public stats endpoint via service key)
GRANT EXECUTE ON FUNCTION public.avg_aura_score() TO anon;
GRANT EXECUTE ON FUNCTION public.avg_aura_score() TO authenticated;
GRANT EXECUTE ON FUNCTION public.avg_aura_score() TO service_role;
