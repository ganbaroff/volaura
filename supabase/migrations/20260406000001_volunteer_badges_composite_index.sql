-- Performance: composite index for volunteer_badges earned_at queries
-- activity.py queries volunteer_badges ORDER BY earned_at DESC per volunteer.
-- Without this, Postgres uses idx_volunteer_badges_volunteer then sorts separately.
-- With composite (volunteer_id, earned_at DESC), the ORDER BY is free (index order matches).
-- CONCURRENTLY: zero-downtime, no table lock.

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_volunteer_badges_volunteer_earned_at
ON public.volunteer_badges USING btree (volunteer_id, earned_at DESC);
