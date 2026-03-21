-- Vector embeddings for semantic volunteer matching
-- Uses Gemini text-embedding-004: 768 dimensions
CREATE TABLE public.volunteer_embeddings (
    volunteer_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    embedding VECTOR(768) NOT NULL,    -- Gemini text-embedding-004
    embedding_text TEXT,               -- the text that was embedded (for debugging)
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for approximate nearest neighbor search
-- Lists = sqrt(expected_rows): start with 100, tune after 10k+ rows
CREATE INDEX idx_volunteer_embeddings_ivfflat
    ON public.volunteer_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

ALTER TABLE public.volunteer_embeddings ENABLE ROW LEVEL SECURITY;

-- Only accessible via RPC functions (service role)
CREATE POLICY "Embeddings readable by authenticated"
    ON public.volunteer_embeddings FOR SELECT
    TO authenticated
    USING (TRUE);
