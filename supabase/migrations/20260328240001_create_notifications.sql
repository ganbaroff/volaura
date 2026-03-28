-- Sprint 4: Create notifications table.
-- Notifications page currently uses MOCK_NOTIFICATIONS hardcoded array.
-- This table makes notifications real. Wire to frontend in Sprint 6.
-- Sprint 4 MVP: backend creates rows; frontend count badge reads count.

CREATE TABLE IF NOT EXISTS public.notifications (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    type         TEXT NOT NULL
                     CHECK (type IN (
                         'aura_update', 'badge_earned', 'event_invite',
                         'org_view', 'intro_request', 'verification',
                         'assessment_complete'
                     )),
    title        TEXT NOT NULL,
    body         TEXT,
    is_read      BOOLEAN NOT NULL DEFAULT FALSE,
    reference_id TEXT,   -- e.g. intro_request id, event id
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for unread count query (dashboard badge)
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread
    ON public.notifications (user_id, is_read)
    WHERE is_read = FALSE;

-- RLS
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own notifications"
    ON public.notifications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can mark own notifications read"
    ON public.notifications FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Service role inserts on behalf of users (backend creates notifications)
CREATE POLICY "Service role can insert notifications"
    ON public.notifications FOR INSERT
    WITH CHECK (TRUE);
