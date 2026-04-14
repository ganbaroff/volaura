-- Formal grievance mechanism (Constitution G35 / ISO 10667-2 §7).
-- WUF13 P0 #9 — a user who disagrees with their AURA score must have a
-- documented channel to contest, review, and appeal. Required by standards
-- for automated decision-making.
--
-- Table shape: intake + state machine (pending → reviewing → resolved | rejected).
-- Admin review UI is a later iteration; this migration just opens the door.

CREATE TABLE IF NOT EXISTS public.grievances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subject TEXT NOT NULL CHECK (char_length(subject) BETWEEN 3 AND 200),
    description TEXT NOT NULL CHECK (char_length(description) BETWEEN 10 AND 5000),
    related_competency_slug TEXT,  -- optional pointer to the competency being contested
    related_session_id UUID,       -- optional pointer to the assessment session
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'reviewing', 'resolved', 'rejected')),
    admin_notes TEXT,
    resolution TEXT,               -- public-facing resolution text returned to user
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS grievances_user_id_idx ON public.grievances(user_id);
CREATE INDEX IF NOT EXISTS grievances_status_idx ON public.grievances(status) WHERE status != 'resolved';

-- RLS: owner can read their own grievances. No one can read others' grievances.
-- Admin review happens via service-role client, never PostgREST.
ALTER TABLE public.grievances ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own grievances"
    ON public.grievances FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users insert own grievances"
    ON public.grievances FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- No UPDATE / DELETE from the API path. Admin-only via service role.

COMMENT ON TABLE public.grievances IS
    'Formal AURA score grievance intake (Constitution G35 / ISO 10667-2 §7). WUF13 P0 #9.';
