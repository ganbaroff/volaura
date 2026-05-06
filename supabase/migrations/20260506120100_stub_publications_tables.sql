-- P0 audit fix: stub missing publication tables referenced by swarm code.
-- TODO: replace these minimal audit tables with full publication schemas once
-- the content pipelines are productized.

CREATE TABLE IF NOT EXISTS public.atlas_publications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  payload JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.zeus_publications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  payload JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
