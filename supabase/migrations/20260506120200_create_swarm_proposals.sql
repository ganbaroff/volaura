-- P0 audit fix: durable queue for Atlas Gateway proposals.

CREATE TABLE IF NOT EXISTS public.swarm_proposals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  agent_id TEXT NOT NULL,
  proposal_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'executed')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.swarm_proposals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role full access" ON public.swarm_proposals;
CREATE POLICY "Service role full access" ON public.swarm_proposals
  FOR ALL USING (auth.role() = 'service_role');
