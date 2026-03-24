-- S3-06: Replace IVFFlat with HNSW index for pgvector
--
-- Why HNSW over IVFFlat:
--   IVFFlat requires data before building (lists = sqrt(rows)) — unusable at 0 rows.
--   HNSW is incremental: works at 0 rows, self-tunes as data grows, better recall.
--   HNSW tradeoff: more RAM (m*2*8 bytes per vector), but recall > 99% at 10k+ rows.
--
-- Parameters:
--   m = 16         — connections per layer (16 = best quality/RAM balance)
--   ef_construction = 64  — build-time candidate list size (64 = production default)
--
-- Migration is safe to run on existing data (concurrent build not needed for <100k rows).

-- Drop old IVFFlat index
DROP INDEX IF EXISTS idx_volunteer_embeddings_ivfflat;

-- Create HNSW index for cosine similarity search
CREATE INDEX idx_volunteer_embeddings_hnsw
    ON public.volunteer_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Comment for future maintainers
COMMENT ON INDEX idx_volunteer_embeddings_hnsw IS
    'HNSW index for pgvector cosine similarity search. '
    'ef_search (query-time) can be tuned via: SET hnsw.ef_search = 100; '
    'Increase m/ef_construction if recall drops below 99% at 100k+ rows.';
