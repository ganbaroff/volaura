-- ARCH-M02: Composite index for leaderboard period filtering
-- Problem: leaderboard.py filters (visibility='public', last_updated>=cutoff, ORDER BY total_score DESC)
-- Current indexes exist separately but no composite index for weekly/monthly queries.
-- Without composite index: planner uses one index then heap-fetches to apply the other filter.
-- At 10k public users: 200-500ms latency on weekly/monthly vs <10ms with composite.
--
-- Note: aura_scores_public is a VIEW on aura_scores table — index goes on base table.

CREATE INDEX IF NOT EXISTS idx_aura_scores_period_leaderboard
ON public.aura_scores (visibility, last_updated DESC, total_score DESC)
WHERE visibility = 'public' AND total_score IS NOT NULL;

COMMENT ON INDEX idx_aura_scores_period_leaderboard IS
'ARCH-M02 2026-03-30: Supports weekly/monthly leaderboard queries with period cutoff filter. '
'Covers: visibility=public + last_updated>=cutoff + ORDER BY total_score DESC in one index scan.';
