-- Constitution Law 2 (Energy Adaptation) — cross-device persistence.
-- Column stores the user's last-chosen energy mode so a signed-in user sees the same
-- adaptive UI on every device. Null = user has never picked → client defaults to 'full'.
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS energy_level TEXT
  CHECK (energy_level IS NULL OR energy_level IN ('full', 'mid', 'low'));

COMMENT ON COLUMN public.profiles.energy_level IS
  'User-selected UX energy mode (Constitution Law 2). NULL until first pick; client defaults to full.';
