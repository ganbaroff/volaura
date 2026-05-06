-- P0 audit fix: restore missing analytics table and brandedby compatibility views.
-- Keep compatibility columns for existing app writes while standardizing on
-- event_type/event_data as the canonical shape.

CREATE TABLE IF NOT EXISTS public.analytics_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  event_data JSONB DEFAULT '{}'::jsonb,
  session_id TEXT,
  ip_hash TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  event_name TEXT,
  properties JSONB DEFAULT '{}'::jsonb,
  platform TEXT DEFAULT 'web',
  locale TEXT
);

CREATE OR REPLACE FUNCTION public.sync_analytics_event_columns()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.event_type IS NULL OR NEW.event_type = '' THEN
    NEW.event_type := COALESCE(NEW.event_name, '');
  END IF;
  IF NEW.event_name IS NULL OR NEW.event_name = '' THEN
    NEW.event_name := NEW.event_type;
  END IF;

  IF NEW.event_data IS NULL THEN
    NEW.event_data := COALESCE(NEW.properties, '{}'::jsonb);
  END IF;
  IF NEW.properties IS NULL THEN
    NEW.properties := COALESCE(NEW.event_data, '{}'::jsonb);
  END IF;

  IF NEW.event_type = '' THEN
    RAISE EXCEPTION 'analytics_events.event_type cannot be empty';
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_sync_analytics_event_columns ON public.analytics_events;
CREATE TRIGGER trg_sync_analytics_event_columns
BEFORE INSERT OR UPDATE ON public.analytics_events
FOR EACH ROW
EXECUTE FUNCTION public.sync_analytics_event_columns();

ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role full access" ON public.analytics_events;
CREATE POLICY "Service role full access" ON public.analytics_events
  FOR ALL USING (auth.role() = 'service_role');

CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id
  ON public.analytics_events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_type_created
  ON public.analytics_events(event_type, created_at DESC);

CREATE OR REPLACE VIEW public.brandedby_ai_twins AS
SELECT * FROM brandedby.ai_twins;

CREATE OR REPLACE VIEW public.brandedby_generations AS
SELECT * FROM brandedby.generations;
