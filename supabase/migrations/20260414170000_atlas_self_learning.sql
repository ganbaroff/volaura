-- Atlas Self-Learning Memory
-- Stores observations about CEO from each interaction.
-- Used by Telegram Atlas to build understanding of Yusif over time.
-- ZenBrain emotional decay applied: high-intensity memories retrieved more.

CREATE TABLE IF NOT EXISTS public.atlas_learnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL CHECK (category IN (
        'preference',
        'strength',
        'weakness',
        'emotional_pattern',
        'correction',
        'insight',
        'project_context',
        'self_position'
    )),
    content TEXT NOT NULL,
    emotional_intensity FLOAT DEFAULT 0 CHECK (emotional_intensity BETWEEN 0 AND 5),
    source_message TEXT,
    access_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_accessed_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.atlas_learnings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on atlas_learnings"
ON public.atlas_learnings
FOR ALL USING (true) WITH CHECK (true);

CREATE INDEX idx_atlas_learnings_category ON public.atlas_learnings(category);
CREATE INDEX idx_atlas_learnings_emotional ON public.atlas_learnings(emotional_intensity DESC);

COMMENT ON TABLE public.atlas_learnings IS 'Atlas self-learning memory. Each row = one observation about CEO extracted from conversation. ZenBrain decay formula applied at retrieval.';
