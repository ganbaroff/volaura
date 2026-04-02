-- Sprint D.1: Partial index for org_view notification throttle check.
--
-- Pattern served:
--   SELECT id FROM notifications
--   WHERE user_id = $1
--     AND type = 'org_view'
--     AND reference_id = $2
--     AND created_at >= NOW() - INTERVAL '24 hours'
--   LIMIT 1;
--
-- Without index: seq scan on full notifications table (grows unbounded).
-- With index: partial index covers only org_view rows — small, fast.
-- reference_id stores org_id (UUID as TEXT) for profile view throttle.

CREATE INDEX IF NOT EXISTS idx_notifications_org_view_throttle
    ON public.notifications (user_id, reference_id, created_at)
    WHERE type = 'org_view';
