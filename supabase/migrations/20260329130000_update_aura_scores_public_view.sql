-- BUG-ARCH-022 + BUG-ARCH-023 FIX: Update aura_scores_public view
--
-- BUG-ARCH-022: discovery.py selects 'events_attended' from aura_scores_public,
--   but the view (created in 20260324000015) explicitly excluded it.
--   PostgREST returns null for missing columns — discovery endpoint always showed 0 events.
--   Fix: add events_attended (count of events attended is not sensitive, unlike events_no_show).
--
-- BUG-ARCH-023: discovery.py does .eq("visibility", "public") filter on aura_scores_public,
--   but the view does NOT include the visibility column.
--   With security_barrier=TRUE, PostgreSQL cannot push the filter to the base table.
--   Result: the visibility filter silently did nothing — ALL scores (including hidden) were returned.
--   Fix: add visibility column to the view.
--
-- events_no_show, reliability_score, reliability_status, aura_history remain EXCLUDED
-- (they are genuinely private — see 20260324000015 comment).

CREATE OR REPLACE VIEW public.aura_scores_public
    WITH (security_barrier = TRUE)
AS
SELECT
    volunteer_id,
    total_score,
    badge_tier,
    elite_status,
    competency_scores,
    percentile_rank,
    last_updated,
    visibility,          -- BUG-ARCH-023: needed for .eq("visibility","public") filter to work
    events_attended      -- BUG-ARCH-022: non-sensitive count; needed by discovery endpoint
FROM public.aura_scores;

COMMENT ON VIEW public.aura_scores_public IS
    'Safe public projection of aura_scores. '
    'Excludes: aura_history, events_no_show, events_late, reliability_score, reliability_status. '
    'Includes: visibility (for filter), events_attended (for discovery display). '
    'Use this view for all org-facing queries, leaderboards, and discovery endpoints. '
    'Never query the base table directly for public-facing endpoints.';
