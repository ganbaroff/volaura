-- EventShift: People-first domain
-- CEO directive 2026-04-17: universal module, people-first shape (not incident-first)
-- Domain: Event → Department → Area → Unit → People + Metrics
-- Every table carries org_id (Path 5: multi-tenant by design from day 1)
-- MVP RLS: owner-of-org can read/write (matches existing events/organizations pattern)
--   Future: switch to current_setting('request.jwt.claims.org_id')::uuid once auth hook is live

-- ============================================================
-- 1. eventshift_events — umbrella real-world event
--    (e.g. "WUF13 Baku 2026", "SOCAR Annual Offsite", "Formula 1 Baku 2026")
-- ============================================================
CREATE TABLE IF NOT EXISTS public.eventshift_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT,                                -- optional short code (e.g. "wuf13-baku-2026")
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    venue TEXT,                               -- human-readable location
    status TEXT NOT NULL DEFAULT 'planning'
        CHECK (status IN ('planning', 'staffing', 'live', 'closed', 'cancelled')),
    timezone TEXT DEFAULT 'Asia/Baku',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT eventshift_events_end_after_start CHECK (end_at > start_at),
    CONSTRAINT eventshift_events_org_slug_unique UNIQUE (org_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_eventshift_events_org ON public.eventshift_events(org_id);
CREATE INDEX IF NOT EXISTS idx_eventshift_events_status ON public.eventshift_events(org_id, status);
CREATE INDEX IF NOT EXISTS idx_eventshift_events_time ON public.eventshift_events(org_id, start_at);

CREATE TRIGGER eventshift_events_updated_at
    BEFORE UPDATE ON public.eventshift_events
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ============================================================
-- 2. eventshift_departments — operational groupings within an event
--    (e.g. "Security", "Accreditation", "Medical", "Logistics")
-- ============================================================
CREATE TABLE IF NOT EXISTS public.eventshift_departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES public.eventshift_events(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    lead_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    color_hex TEXT,                           -- for UI chips (validated: no red)
    sort_order INT DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT eventshift_departments_event_name_unique UNIQUE (event_id, name)
);

CREATE INDEX IF NOT EXISTS idx_eventshift_departments_org ON public.eventshift_departments(org_id);
CREATE INDEX IF NOT EXISTS idx_eventshift_departments_event ON public.eventshift_departments(event_id, sort_order);

CREATE TRIGGER eventshift_departments_updated_at
    BEFORE UPDATE ON public.eventshift_departments
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ============================================================
-- 3. eventshift_areas — physical/logical zones inside a department
--    (e.g. under Security → "Main Entrance", "VIP Lounge", "Perimeter")
-- ============================================================
CREATE TABLE IF NOT EXISTS public.eventshift_areas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    department_id UUID NOT NULL REFERENCES public.eventshift_departments(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    coordinator_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    location JSONB NOT NULL DEFAULT '{}',     -- flexible: {lat, lng} or {building, floor, wing}
    sort_order INT DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT eventshift_areas_dept_name_unique UNIQUE (department_id, name)
);

CREATE INDEX IF NOT EXISTS idx_eventshift_areas_org ON public.eventshift_areas(org_id);
CREATE INDEX IF NOT EXISTS idx_eventshift_areas_department ON public.eventshift_areas(department_id, sort_order);

CREATE TRIGGER eventshift_areas_updated_at
    BEFORE UPDATE ON public.eventshift_areas
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ============================================================
-- 4. eventshift_units — staffed positions within an area (shifts, posts, patrols)
--    (e.g. under Main Entrance → "Morning Shift Post 1", "Evening Patrol A")
--    A unit is a time-bounded slot that needs people.
-- ============================================================
CREATE TABLE IF NOT EXISTS public.eventshift_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    area_id UUID NOT NULL REFERENCES public.eventshift_areas(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    shift_start TIMESTAMPTZ NOT NULL,
    shift_end TIMESTAMPTZ NOT NULL,
    required_headcount INT NOT NULL DEFAULT 1 CHECK (required_headcount >= 0),
    required_skills JSONB NOT NULL DEFAULT '[]',  -- array of competency slugs for AURA matching
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'staffed', 'live', 'closed')),
    notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT eventshift_units_end_after_start CHECK (shift_end > shift_start)
);

CREATE INDEX IF NOT EXISTS idx_eventshift_units_org ON public.eventshift_units(org_id);
CREATE INDEX IF NOT EXISTS idx_eventshift_units_area ON public.eventshift_units(area_id, shift_start);
CREATE INDEX IF NOT EXISTS idx_eventshift_units_status ON public.eventshift_units(org_id, status);

CREATE TRIGGER eventshift_units_updated_at
    BEFORE UPDATE ON public.eventshift_units
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ============================================================
-- 5. eventshift_unit_assignments — people → units (the "people" in people-first)
--    Canonical link between a person and the unit they staff.
-- ============================================================
CREATE TABLE IF NOT EXISTS public.eventshift_unit_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    unit_id UUID NOT NULL REFERENCES public.eventshift_units(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'staff'
        CHECK (role IN ('lead', 'staff', 'backup', 'volunteer')),
    status TEXT NOT NULL DEFAULT 'assigned'
        CHECK (status IN ('assigned', 'accepted', 'declined', 'checked_in', 'completed', 'no_show')),
    assigned_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    checked_in_at TIMESTAMPTZ,
    checked_out_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT eventshift_unit_assignments_unique UNIQUE (unit_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_eventshift_assignments_org ON public.eventshift_unit_assignments(org_id);
CREATE INDEX IF NOT EXISTS idx_eventshift_assignments_unit ON public.eventshift_unit_assignments(unit_id);
CREATE INDEX IF NOT EXISTS idx_eventshift_assignments_user ON public.eventshift_unit_assignments(user_id, status);

CREATE TRIGGER eventshift_unit_assignments_updated_at
    BEFORE UPDATE ON public.eventshift_unit_assignments
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ============================================================
-- 6. eventshift_unit_metrics — measurement stream per unit
--    Metric types (extensible): attendance, handover_integrity, incident_closure, reliability_proof, ...
--    Incidents are ONE metric_type — not the root entity (CEO correction).
-- ============================================================
CREATE TABLE IF NOT EXISTS public.eventshift_unit_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    unit_id UUID NOT NULL REFERENCES public.eventshift_units(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL,
    -- Canonical metric_type values (add new types freely, keep these names stable):
    --   attendance          — was the unit staffed at expected headcount?
    --   handover_integrity  — did handover between shifts complete cleanly?
    --   incident            — an incident occurred (payload describes it)
    --   incident_closure    — incident resolved (payload links to incident row)
    --   reliability_proof   — cumulative reliability signal for AURA event_performance
    value NUMERIC,                            -- for scalar metrics (0-100, counts, durations)
    payload JSONB NOT NULL DEFAULT '{}',      -- for structured metric data
    recorded_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_eventshift_metrics_org ON public.eventshift_unit_metrics(org_id);
CREATE INDEX IF NOT EXISTS idx_eventshift_metrics_unit ON public.eventshift_unit_metrics(unit_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_eventshift_metrics_type ON public.eventshift_unit_metrics(org_id, metric_type, recorded_at DESC);

-- ============================================================
-- 7. RLS — tenant isolation by organization ownership
--    MVP pattern: org owner can read/write all rows for their org.
--    Future (Path 5 full): current_setting('request.jwt.claims.org_id', true)::uuid = org_id
--    once Supabase auth hook injects org membership into JWT claims.
-- ============================================================

ALTER TABLE public.eventshift_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eventshift_departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eventshift_areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eventshift_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eventshift_unit_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.eventshift_unit_metrics ENABLE ROW LEVEL SECURITY;

-- Helper predicate (repeated inline for each table since Postgres RLS can't call IMMUTABLE helper
-- referencing auth.uid() cleanly across all operations). Pattern: org owner has full access.

-- eventshift_events
CREATE POLICY "Org owner can read eventshift_events"
    ON public.eventshift_events FOR SELECT
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can insert eventshift_events"
    ON public.eventshift_events FOR INSERT
    WITH CHECK (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can update eventshift_events"
    ON public.eventshift_events FOR UPDATE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can delete eventshift_events"
    ON public.eventshift_events FOR DELETE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

-- eventshift_departments
CREATE POLICY "Org owner can read eventshift_departments"
    ON public.eventshift_departments FOR SELECT
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can insert eventshift_departments"
    ON public.eventshift_departments FOR INSERT
    WITH CHECK (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can update eventshift_departments"
    ON public.eventshift_departments FOR UPDATE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can delete eventshift_departments"
    ON public.eventshift_departments FOR DELETE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

-- eventshift_areas
CREATE POLICY "Org owner can read eventshift_areas"
    ON public.eventshift_areas FOR SELECT
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can insert eventshift_areas"
    ON public.eventshift_areas FOR INSERT
    WITH CHECK (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can update eventshift_areas"
    ON public.eventshift_areas FOR UPDATE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can delete eventshift_areas"
    ON public.eventshift_areas FOR DELETE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

-- eventshift_units
CREATE POLICY "Org owner can read eventshift_units"
    ON public.eventshift_units FOR SELECT
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can insert eventshift_units"
    ON public.eventshift_units FOR INSERT
    WITH CHECK (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can update eventshift_units"
    ON public.eventshift_units FOR UPDATE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can delete eventshift_units"
    ON public.eventshift_units FOR DELETE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

-- eventshift_unit_assignments — the assigned person can read their own assignment
CREATE POLICY "Org owner can read eventshift_unit_assignments"
    ON public.eventshift_unit_assignments FOR SELECT
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Assigned user can read own eventshift_unit_assignments"
    ON public.eventshift_unit_assignments FOR SELECT
    USING (user_id = auth.uid());
CREATE POLICY "Org owner can insert eventshift_unit_assignments"
    ON public.eventshift_unit_assignments FOR INSERT
    WITH CHECK (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can update eventshift_unit_assignments"
    ON public.eventshift_unit_assignments FOR UPDATE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Assigned user can update own status"
    ON public.eventshift_unit_assignments FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
CREATE POLICY "Org owner can delete eventshift_unit_assignments"
    ON public.eventshift_unit_assignments FOR DELETE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

-- eventshift_unit_metrics — append-only for MVP; org owner reads, service role writes
CREATE POLICY "Org owner can read eventshift_unit_metrics"
    ON public.eventshift_unit_metrics FOR SELECT
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));
CREATE POLICY "Org owner can insert eventshift_unit_metrics"
    ON public.eventshift_unit_metrics FOR INSERT
    WITH CHECK (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

-- ============================================================
-- 8. Comments (documentation inside the DB)
-- ============================================================
COMMENT ON TABLE public.eventshift_events IS
    'EventShift: real-world event tenant root. CEO-canonical domain (2026-04-17): Event → Department → Area → Unit → People + Metrics. People-first, not incident-first.';
COMMENT ON TABLE public.eventshift_departments IS
    'EventShift: operational department inside an event (Security, Accreditation, Medical, ...).';
COMMENT ON TABLE public.eventshift_areas IS
    'EventShift: physical/logical zone inside a department (Main Entrance, VIP Lounge, ...).';
COMMENT ON TABLE public.eventshift_units IS
    'EventShift: time-bounded staffed position inside an area (shift, post, patrol).';
COMMENT ON TABLE public.eventshift_unit_assignments IS
    'EventShift: person ↔ unit link. The "people" in people-first.';
COMMENT ON TABLE public.eventshift_unit_metrics IS
    'EventShift: measurement stream per unit. Incidents are ONE metric_type, not the root entity.';
