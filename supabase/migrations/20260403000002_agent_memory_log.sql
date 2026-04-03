-- ADR-011: Persistent Agent Memory + Run Log
-- Enables cross-session memory for autonomous swarm agents.
-- Two tables:
--   agent_memory  — episodic/semantic/procedural/failure memories per agent
--   agent_run_log — audit trail of every autonomous run (scheduled, deploy, event)
--
-- Service-role only. No anon/user access. All swarm reads/writes go through
-- the Railway API (admin client) or GitHub Actions (SUPABASE_SERVICE_ROLE_KEY).

-- ── agent_memory ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agent_memory (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id      TEXT        NOT NULL,
    memory_type   TEXT        NOT NULL CHECK (memory_type IN ('episodic', 'semantic', 'procedural', 'failure')),
    content       TEXT        NOT NULL,
    context_tags  TEXT[]      DEFAULT '{}',
    confidence    NUMERIC(3,2) DEFAULT 1.0 CHECK (confidence BETWEEN 0.0 AND 1.0),
    used_count    INTEGER     DEFAULT 0,
    last_used_at  TIMESTAMPTZ,
    expires_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Index: fetch all memories for a given agent ordered by recency
CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_created
    ON public.agent_memory (agent_id, created_at DESC);

-- Index: filter by memory type (e.g. get all 'failure' entries for retrospective)
CREATE INDEX IF NOT EXISTS idx_agent_memory_type
    ON public.agent_memory (memory_type);

-- Auto-update updated_at on row change
CREATE OR REPLACE FUNCTION public.touch_agent_memory()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS agent_memory_updated ON public.agent_memory;
CREATE TRIGGER agent_memory_updated
    BEFORE UPDATE ON public.agent_memory
    FOR EACH ROW EXECUTE FUNCTION public.touch_agent_memory();

-- ── agent_run_log ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agent_run_log (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id        TEXT        NOT NULL,                   -- deterministic: mode + date (e.g. "daily-ideation-2026-04-03")
    agent_id      TEXT        NOT NULL,                   -- perspective name (e.g. "Security Auditor")
    trigger_type  TEXT        NOT NULL CHECK (trigger_type IN ('scheduled', 'event', 'ceo_command', 'error_spike', 'deploy')),
    trigger_meta  JSONB       DEFAULT '{}',               -- e.g. {"deploy_sha": "abc123", "branch": "main"}
    model_used    TEXT,                                   -- e.g. "groq/llama-3.3-70b-versatile"
    tokens_in     INTEGER,
    tokens_out    INTEGER,
    duration_ms   INTEGER,
    proposal_ids  TEXT[]      DEFAULT '{}',               -- UUIDs of proposals this run produced
    proposals_count INTEGER   GENERATED ALWAYS AS (array_length(proposal_ids, 1)) STORED,
    status        TEXT        DEFAULT 'completed' CHECK (status IN ('completed', 'failed', 'skipped', 'partial')),
    error_message TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Index: look up runs by mode (run_id prefix) and date for DORA tracking
CREATE INDEX IF NOT EXISTS idx_agent_run_log_run_id
    ON public.agent_run_log (run_id, created_at DESC);

-- Index: filter by trigger type for analytics (how many deploy-triggered vs scheduled)
CREATE INDEX IF NOT EXISTS idx_agent_run_log_trigger
    ON public.agent_run_log (trigger_type, created_at DESC);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- No user-level access. Service role (GitHub Actions + Railway) only.
ALTER TABLE public.agent_memory  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_run_log ENABLE ROW LEVEL SECURITY;

-- No policies = only service_role bypass can read/write (Supabase RLS semantics).
-- Anon and authenticated roles are denied by default when RLS is enabled and no
-- permissive policy exists.

COMMENT ON TABLE public.agent_memory  IS 'Cross-session persistent memory for autonomous swarm agents (ADR-011).';
COMMENT ON TABLE public.agent_run_log IS 'Audit log of every autonomous swarm run for DORA tracking (ADR-011).';
