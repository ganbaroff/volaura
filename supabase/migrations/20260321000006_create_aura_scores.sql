CREATE TABLE public.aura_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    volunteer_id UUID UNIQUE NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    total_score FLOAT NOT NULL DEFAULT 0,
    badge_tier TEXT DEFAULT 'none'
        CHECK (badge_tier IN ('none', 'bronze', 'silver', 'gold', 'platinum')),
    elite_status BOOLEAN DEFAULT FALSE,
    -- Per-competency scores: {slug: score_0_to_100}
    competency_scores JSONB NOT NULL DEFAULT '{}',
    -- Reliability
    reliability_score FLOAT DEFAULT 50.0,
    reliability_status TEXT DEFAULT 'pending'
        CHECK (reliability_status IN ('pending', 'verified', 'proven')),
    -- Event stats
    events_attended INT DEFAULT 0,
    events_no_show INT DEFAULT 0,
    events_late INT DEFAULT 0,
    -- Rankings
    percentile_rank FLOAT,
    -- History for timeline visualization
    aura_history JSONB DEFAULT '[]',   -- [{date, total_score, badge_tier}]
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_aura_scores_total ON public.aura_scores(total_score DESC);
CREATE INDEX idx_aura_scores_badge ON public.aura_scores(badge_tier);

ALTER TABLE public.aura_scores ENABLE ROW LEVEL SECURITY;

-- Public read for volunteer discovery
CREATE POLICY "AURA scores are publicly readable"
    ON public.aura_scores FOR SELECT
    USING (TRUE);

CREATE POLICY "System can insert AURA scores"
    ON public.aura_scores FOR INSERT
    WITH CHECK (auth.uid() = volunteer_id);

CREATE POLICY "System can update AURA scores"
    ON public.aura_scores FOR UPDATE
    USING (auth.uid() = volunteer_id);
