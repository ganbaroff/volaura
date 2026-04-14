-- Constitution VOLAURA Rule 30 — Ghosting Grace for pre-activation users.
-- WUF13 P0 #14. After signup, if user does not complete any assessment within
-- 48h, send ONE warm re-entry email. The column tracks whether the email was
-- already sent so we don't double-nudge.

ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS ghosting_grace_sent_at TIMESTAMPTZ;

COMMENT ON COLUMN public.profiles.ghosting_grace_sent_at IS
    'Constitution Rule 30 — timestamp when the 48h warm re-entry email was sent. NULL = not yet sent. Set once, never reset.';

-- Index supports the candidate query: WHERE ghosting_grace_sent_at IS NULL AND created_at < now() - 48h
CREATE INDEX IF NOT EXISTS profiles_ghosting_grace_pending_idx
    ON public.profiles(created_at)
    WHERE ghosting_grace_sent_at IS NULL;
