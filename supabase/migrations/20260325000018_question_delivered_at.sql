-- HIGH-03: Server-side timing for anti-gaming
-- Records when each question was delivered to the client.
-- Used to compute actual response time instead of trusting client-reported timing.

ALTER TABLE public.assessment_sessions
    ADD COLUMN IF NOT EXISTS question_delivered_at TIMESTAMPTZ;

COMMENT ON COLUMN public.assessment_sessions.question_delivered_at IS
    'Server timestamp when current question was delivered. Used for anti-gaming timing validation instead of client-reported response_time_ms.';
