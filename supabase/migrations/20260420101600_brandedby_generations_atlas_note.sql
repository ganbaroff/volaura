-- E5: Atlas note seed — 1-sentence memory anchor per generation
-- Stores what Atlas knows about the user at generation time.
-- Full integration (LLM-composed twin briefing) deferred to E7 sprint.

ALTER TABLE brandedby.generations
    ADD COLUMN IF NOT EXISTS atlas_note TEXT;

COMMENT ON COLUMN brandedby.generations.atlas_note IS
    'E5: 1-sentence Atlas memory anchor — what Atlas knew about this user when the generation was requested. Populated fire-and-forget from atlas_learnings at creation time.';
