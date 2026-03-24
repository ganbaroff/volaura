---
description: Supabase + pgvector rules — migrations, RLS, vector(768) only, RPC functions
globs:
  - "supabase/**"
---

# Database Rules (Supabase + pgvector)

## Migrations
- Location: `supabase/migrations/`
- Naming: `YYYYMMDDHHMMSS_description.sql`
- One migration per logical change
- Always include RLS policies with table creation

## RLS Policies
```sql
-- Pattern: owner can read/write own rows
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own profile"
ON public.profiles FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
ON public.profiles FOR UPDATE
USING (auth.uid() = id);
```

## pgvector
- Dimensions: vector(768) — Gemini text-embedding-004
- NEVER use vector(1536) — that's OpenAI
- All vector operations via RPC functions ONLY
- Never use pgvector operators via PostgREST client

```sql
-- RPC function for vector search
CREATE OR REPLACE FUNCTION match_volunteers(
    query_embedding VECTOR(768),
    match_count INT,
    min_aura FLOAT DEFAULT 0
) RETURNS TABLE(volunteer_id UUID, similarity FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT ve.volunteer_id,
           1 - (ve.embedding <=> query_embedding) AS similarity
    FROM volunteer_embeddings ve
    JOIN aura_scores a ON ve.volunteer_id = a.volunteer_id
    WHERE a.total_score >= min_aura
    ORDER BY ve.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
```

## Seed Data
- `supabase/seed.sql` for development data
- 8 competencies with exact AURA weights
- Sample questions with IRT parameters

## Naming
- Tables: snake_case, plural (e.g., `profiles`, `assessment_sessions`)
- Columns: snake_case
- Functions: snake_case
- Always use `gen_random_uuid()` for UUIDs
- Always use `TIMESTAMPTZ` (not `TIMESTAMP`)
