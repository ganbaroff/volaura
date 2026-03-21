CREATE TABLE public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    title_en TEXT NOT NULL,
    title_az TEXT NOT NULL,
    description_en TEXT,
    description_az TEXT,
    event_type TEXT,                   -- conference, marathon, ceremony, etc.
    location TEXT,
    location_coords JSONB,             -- {lat, lng}
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    capacity INT,
    required_competencies UUID[] DEFAULT '{}',
    required_min_aura FLOAT DEFAULT 0,
    required_languages TEXT[] DEFAULT '{}',
    status TEXT DEFAULT 'draft'
        CHECK (status IN ('draft', 'open', 'closed', 'cancelled', 'completed')),
    is_public BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER events_updated_at
    BEFORE UPDATE ON public.events
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE INDEX idx_events_org ON public.events(organization_id);
CREATE INDEX idx_events_status ON public.events(status);
CREATE INDEX idx_events_start_date ON public.events(start_date);

-- Add FK for organization_ratings -> events
ALTER TABLE public.organization_ratings
    ADD CONSTRAINT fk_org_ratings_event
    FOREIGN KEY (event_id) REFERENCES public.events(id) ON DELETE SET NULL;

CREATE TABLE public.registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'waitlisted', 'cancelled')),
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    checked_in_at TIMESTAMPTZ,
    check_in_code TEXT,                -- QR code value
    -- Coordinator rates volunteer
    coordinator_rating INT CHECK (coordinator_rating BETWEEN 1 AND 5),
    coordinator_feedback TEXT,
    coordinator_rated_at TIMESTAMPTZ,
    -- Volunteer rates event/org
    volunteer_rating INT CHECK (volunteer_rating BETWEEN 1 AND 5),
    volunteer_feedback TEXT,
    volunteer_rated_at TIMESTAMPTZ,
    -- No-show tracking
    no_show_reason TEXT,
    cancellation_hours_before INT,
    metadata JSONB DEFAULT '{}',
    UNIQUE(event_id, volunteer_id)
);

CREATE INDEX idx_registrations_event ON public.registrations(event_id);
CREATE INDEX idx_registrations_volunteer ON public.registrations(volunteer_id);
CREATE INDEX idx_registrations_status ON public.registrations(status);

ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public events are viewable by everyone"
    ON public.events FOR SELECT
    USING (is_public = TRUE AND status != 'draft');

CREATE POLICY "Org owners can manage their events"
    ON public.events FOR ALL
    USING (
        organization_id IN (
            SELECT id FROM public.organizations WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Volunteers can view own registrations"
    ON public.registrations FOR SELECT
    USING (auth.uid() = volunteer_id);

CREATE POLICY "Volunteers can register"
    ON public.registrations FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = volunteer_id);

CREATE POLICY "Volunteers can cancel own registration"
    ON public.registrations FOR UPDATE
    USING (auth.uid() = volunteer_id);

CREATE POLICY "Org owners can manage registrations"
    ON public.registrations FOR ALL
    USING (
        event_id IN (
            SELECT e.id FROM public.events e
            JOIN public.organizations o ON e.organization_id = o.id
            WHERE o.owner_id = auth.uid()
        )
    );
