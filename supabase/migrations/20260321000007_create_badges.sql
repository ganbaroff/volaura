CREATE TABLE public.badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    name_en TEXT NOT NULL,
    name_az TEXT NOT NULL,
    description_en TEXT,
    description_az TEXT,
    icon_url TEXT,
    badge_type TEXT DEFAULT 'tier'
        CHECK (badge_type IN ('tier', 'achievement', 'special')),
    requirements JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.volunteer_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    badge_id UUID NOT NULL REFERENCES public.badges(id),
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    open_badges_url TEXT,              -- Open Badges 3.0 JSON URL
    linkedin_exported_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    UNIQUE(volunteer_id, badge_id)
);

CREATE INDEX idx_volunteer_badges_volunteer ON public.volunteer_badges(volunteer_id);

ALTER TABLE public.badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_badges ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Badges are viewable by everyone"
    ON public.badges FOR SELECT USING (TRUE);

CREATE POLICY "Users can view own badges"
    ON public.volunteer_badges FOR SELECT
    USING (auth.uid() = volunteer_id);

CREATE POLICY "Public can view volunteer badges"
    ON public.volunteer_badges FOR SELECT
    USING (TRUE);
