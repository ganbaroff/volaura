-- CEO ↔ Agent communication channel via Telegram
-- Stores all CEO messages + bot responses + task delegations

CREATE TABLE IF NOT EXISTS public.ceo_inbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    direction TEXT NOT NULL CHECK (direction IN ('ceo_to_bot', 'bot_to_ceo')),
    message TEXT NOT NULL,
    message_type TEXT DEFAULT 'free_text' CHECK (message_type IN ('free_text', 'command', 'idea', 'task', 'report', 'approval')),
    metadata JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ceo_inbox_created ON public.ceo_inbox(created_at DESC);
CREATE INDEX idx_ceo_inbox_unprocessed ON public.ceo_inbox(processed) WHERE processed = FALSE;

ALTER TABLE public.ceo_inbox ENABLE ROW LEVEL SECURITY;
-- Service role only — no public access. Bot uses admin client which bypasses RLS.
