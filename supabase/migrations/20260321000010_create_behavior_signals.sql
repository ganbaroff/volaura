-- 6-signal behavioral reliability model
CREATE TABLE public.volunteer_behavior_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    signal_type TEXT NOT NULL CHECK (signal_type IN (
        'onboarding_velocity',
        'assessment_completion',
        'profile_completeness',
        'sjt_reliability',
        'contact_verification',
        'availability_specificity',
        'attendance',
        'punctuality',
        'shift_completion',
        'no_show',
        'late_cancellation'
    )),
    signal_value FLOAT NOT NULL,
    measured_at TIMESTAMPTZ DEFAULT NOW(),
    source TEXT,                       -- 'system', 'coordinator', 'event'
    source_id UUID,                    -- event_id or session_id
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_behavior_signals_volunteer ON public.volunteer_behavior_signals(volunteer_id);
CREATE INDEX idx_behavior_signals_type ON public.volunteer_behavior_signals(signal_type);

ALTER TABLE public.volunteer_behavior_signals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own behavior signals"
    ON public.volunteer_behavior_signals FOR SELECT
    USING (auth.uid() = volunteer_id);

CREATE POLICY "System can insert behavior signals"
    ON public.volunteer_behavior_signals FOR INSERT
    TO authenticated
    WITH CHECK (TRUE);
