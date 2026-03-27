-- Sprint B3: Add retry_count to brandedby.generations
-- Enables video generation worker to retry transient fal.ai failures

ALTER TABLE brandedby.generations
    ADD COLUMN IF NOT EXISTS retry_count INT NOT NULL DEFAULT 0;

COMMENT ON COLUMN brandedby.generations.retry_count IS
    'Number of times this job has been retried after failure. Worker stops after MAX_RETRIES.';
