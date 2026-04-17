-- Module catalogue + per-tenant activations
-- Per docs/MODULES.md §6. One row per module, owned by the core.
-- Activation is per-org (module_activations), reversible, audit-able.

-- ============================================================
-- 1. modules — core-owned catalogue (one row per module)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.modules (
    slug TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('core', 'gateway', 'module', 'experience')),
    default_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    billing_sku TEXT,
    min_core_version TEXT,
    owner_team TEXT,
    settings_schema JSONB NOT NULL DEFAULT '{}',  -- JSON Schema for per-org settings
    status TEXT NOT NULL DEFAULT 'stable'
        CHECK (status IN ('alpha', 'beta', 'stable', 'deprecated', 'archived')),
    version TEXT NOT NULL DEFAULT '0.1.0',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER modules_updated_at
    BEFORE UPDATE ON public.modules
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

COMMENT ON TABLE public.modules IS
    'Core-owned module catalogue. One row per arm of the octopus (MODULES.md §6). Adding a new module = insert a row here first, then ship the code.';

-- ============================================================
-- 2. module_activations — per-tenant activation state
-- ============================================================
CREATE TABLE IF NOT EXISTS public.module_activations (
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    module_slug TEXT NOT NULL REFERENCES public.modules(slug) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    settings JSONB NOT NULL DEFAULT '{}',
    activated_at TIMESTAMPTZ,
    activated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    deactivated_at TIMESTAMPTZ,
    deactivated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    stripe_subscription_item_id TEXT,             -- bound to module.billing_sku when paid
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (org_id, module_slug)
);

CREATE INDEX IF NOT EXISTS idx_module_activations_org_enabled
    ON public.module_activations(org_id, enabled) WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_module_activations_slug_enabled
    ON public.module_activations(module_slug, enabled) WHERE enabled = TRUE;

CREATE TRIGGER module_activations_updated_at
    BEFORE UPDATE ON public.module_activations
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

COMMENT ON TABLE public.module_activations IS
    'Per-tenant module on/off state. PK (org_id, module_slug). Deactivation preserves data; re-activation restores visibility.';

-- ============================================================
-- 3. RLS — modules catalogue is publicly readable, org_admin reads own activations
-- ============================================================

ALTER TABLE public.modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.module_activations ENABLE ROW LEVEL SECURITY;

-- Modules catalogue: anyone authenticated can see what modules exist (it's not secret)
CREATE POLICY "Authenticated users can read modules catalogue"
    ON public.modules FOR SELECT
    TO authenticated
    USING (TRUE);

-- Module activations: org owner reads and writes own activations
CREATE POLICY "Org owner can read own module_activations"
    ON public.module_activations FOR SELECT
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

CREATE POLICY "Org owner can insert own module_activations"
    ON public.module_activations FOR INSERT
    WITH CHECK (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

CREATE POLICY "Org owner can update own module_activations"
    ON public.module_activations FOR UPDATE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

CREATE POLICY "Org owner can delete own module_activations"
    ON public.module_activations FOR DELETE
    USING (org_id IN (SELECT id FROM public.organizations WHERE owner_id = auth.uid()));

-- ============================================================
-- 4. Seed: the 5 known arms of the octopus (MODULES.md §6)
-- ============================================================
INSERT INTO public.modules (slug, display_name, tier, default_enabled, status, version, description, owner_team)
VALUES
    ('volaura-core',      'VOLAURA',         'core',       TRUE,  'stable', '1.0.0',
     'Identity, AURA score, assessment engine, crystal ledger, character_events bus, billing.',
     'core'),
    ('mindshift-gateway', 'MindShift',       'gateway',    FALSE, 'stable', '1.0.0',
     'ADHD-aware productivity PWA. Daily gateway surface; feeds character_events.',
     'gateway'),
    ('eventshift',        'EventShift',      'module',     FALSE, 'beta',   '0.1.0',
     'Universal event shift ops: Event → Department → Area → Unit → People + Metrics. People-first.',
     'verticals'),
    ('brandedby',         'BrandedBy',       'module',     FALSE, 'alpha',  '0.1.0',
     'AI professional identity builder. Vertical arm, core-billed.',
     'verticals'),
    ('life-simulator',    'Life Simulator',  'experience', FALSE, 'alpha',  '0.1.0',
     '3D agent office (Godot 4). Reads character_events; never writes primary data. Opt-in per user.',
     'experience')
ON CONFLICT (slug) DO UPDATE SET
    display_name     = EXCLUDED.display_name,
    tier             = EXCLUDED.tier,
    default_enabled  = EXCLUDED.default_enabled,
    status           = EXCLUDED.status,
    version          = EXCLUDED.version,
    description      = EXCLUDED.description,
    owner_team       = EXCLUDED.owner_team,
    updated_at       = now();

-- ============================================================
-- 5. Helper: is_module_active_for_org(org_id, slug) — used by FastAPI activation gate
-- ============================================================
CREATE OR REPLACE FUNCTION public.is_module_active_for_org(p_org_id UUID, p_slug TEXT)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.module_activations
        WHERE org_id = p_org_id
          AND module_slug = p_slug
          AND enabled = TRUE
    );
$$;

GRANT EXECUTE ON FUNCTION public.is_module_active_for_org(UUID, TEXT) TO authenticated, service_role;

COMMENT ON FUNCTION public.is_module_active_for_org IS
    'Activation gate: returns TRUE iff (org_id, slug) has an enabled module_activations row. Used by module routers to enforce 403 MODULE_NOT_ACTIVATED.';
