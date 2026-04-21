-- RPC for error_watcher.py signal #2: count character_events where user_id has no matching profile.
-- Detects bridge leaks (events emitted for deleted/orphaned users).
-- Called every 10 min by cron; returns integer count.

CREATE OR REPLACE FUNCTION public.count_orphan_character_events(since_ts TIMESTAMPTZ)
RETURNS INTEGER
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = 'public'
AS $$
  SELECT count(*)::int
  FROM public.character_events ce
  LEFT JOIN public.profiles p ON p.id = ce.user_id
  WHERE ce.created_at >= since_ts
    AND p.id IS NULL;
$$;

REVOKE ALL ON FUNCTION public.count_orphan_character_events(TIMESTAMPTZ) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.count_orphan_character_events(TIMESTAMPTZ) FROM anon;
REVOKE ALL ON FUNCTION public.count_orphan_character_events(TIMESTAMPTZ) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.count_orphan_character_events(TIMESTAMPTZ) TO service_role;
