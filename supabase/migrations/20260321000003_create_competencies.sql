CREATE TABLE public.competencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    name_en TEXT NOT NULL,
    name_az TEXT NOT NULL,
    description_en TEXT,
    description_az TEXT,
    weight FLOAT NOT NULL CHECK (weight > 0 AND weight <= 1),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Public read-only (reference data)
ALTER TABLE public.competencies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Competencies are viewable by everyone"
    ON public.competencies FOR SELECT
    USING (TRUE);
