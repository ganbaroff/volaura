-- Sprint B1: BrandedBy schema — AI Twin video platform
-- Separate PostgreSQL schema: brandedby.* (isolates from public.* Volaura tables)
-- Auth is shared: auth.users (one JWT = all products)

-- ============================================================
-- 0. Create schema
-- ============================================================
CREATE SCHEMA IF NOT EXISTS brandedby;

-- ============================================================
-- 1. ai_twins — user's AI digital twin profile
-- ============================================================
CREATE TABLE brandedby.ai_twins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    tagline TEXT,                          -- one-liner ("Volunteer leader & tech enthusiast")
    photo_url TEXT,                        -- portrait photo (R2 or Supabase Storage)
    voice_id TEXT,                         -- TTS voice identifier (Phase 2)
    personality_prompt TEXT,               -- auto-generated from character_state
    status TEXT NOT NULL DEFAULT 'draft',  -- draft | active | suspended
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ai_twins_status_check CHECK (status IN ('draft', 'active', 'suspended')),
    CONSTRAINT ai_twins_one_per_user UNIQUE (user_id)  -- one AI Twin per user (MVP)
);

CREATE INDEX idx_ai_twins_user ON brandedby.ai_twins(user_id);
CREATE INDEX idx_ai_twins_status ON brandedby.ai_twins(status);

-- ============================================================
-- 2. generations — video/audio generation jobs
-- ============================================================
CREATE TABLE brandedby.generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    twin_id UUID NOT NULL REFERENCES brandedby.ai_twins(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    gen_type TEXT NOT NULL DEFAULT 'video',  -- video | audio | text_chat
    input_text TEXT NOT NULL,                -- script or prompt
    output_url TEXT,                         -- generated video/audio URL (R2)
    thumbnail_url TEXT,                      -- video thumbnail for sharing
    status TEXT NOT NULL DEFAULT 'queued',   -- queued | processing | completed | failed
    error_message TEXT,                      -- failure reason (if failed)
    queue_position INT,                      -- for queue mechanic (free=wait, crystal=skip)
    crystal_cost INT NOT NULL DEFAULT 0,     -- crystals spent to skip queue
    duration_seconds INT,                    -- output duration
    processing_started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT generations_type_check CHECK (gen_type IN ('video', 'audio', 'text_chat')),
    CONSTRAINT generations_status_check CHECK (status IN ('queued', 'processing', 'completed', 'failed'))
);

CREATE INDEX idx_generations_twin ON brandedby.generations(twin_id);
CREATE INDEX idx_generations_user ON brandedby.generations(user_id);
CREATE INDEX idx_generations_status ON brandedby.generations(status, created_at);

-- ============================================================
-- 3. RLS policies — user-scoped access
-- ============================================================

-- ai_twins: users can CRUD their own twin
ALTER TABLE brandedby.ai_twins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own AI twin"
    ON brandedby.ai_twins FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own AI twin"
    ON brandedby.ai_twins FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own AI twin"
    ON brandedby.ai_twins FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own AI twin"
    ON brandedby.ai_twins FOR DELETE
    USING (auth.uid() = user_id);

-- generations: users can read/create their own, system updates status
ALTER TABLE brandedby.generations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own generations"
    ON brandedby.generations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own generations"
    ON brandedby.generations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- No user UPDATE/DELETE — status transitions handled by service role (backend)

-- ============================================================
-- 4. updated_at trigger for ai_twins
-- ============================================================
CREATE OR REPLACE FUNCTION brandedby.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER ai_twins_updated_at
    BEFORE UPDATE ON brandedby.ai_twins
    FOR EACH ROW
    EXECUTE FUNCTION brandedby.set_updated_at();

-- ============================================================
-- 5. Grant schema access to authenticated users
-- ============================================================
GRANT USAGE ON SCHEMA brandedby TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA brandedby TO authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA brandedby GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

-- Service role (backend) needs full access for status transitions
GRANT USAGE ON SCHEMA brandedby TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA brandedby TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA brandedby GRANT ALL ON TABLES TO service_role;
