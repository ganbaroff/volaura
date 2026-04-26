// API client for VOLAURA backend (Railway)
const API_BASE = import.meta.env.VITE_API_URL || 'https://modest-happiness-production.up.railway.app/api'

export interface Proposal {
  id: string
  title: string
  content: string
  agent: string
  severity: string
  status: string
  votes_for: number
  votes_against: number
  judge_score?: number
  created_at?: string
}

export interface SwarmAgent {
  id: string
  name: string
  role: string
  status: string
  last_task?: string
  last_run?: string | null
  next_scheduled?: string | null
  blockers?: string[]
  tasks_completed: number
  tasks_failed?: number
  quality_score?: number
}

export interface SwarmDigest {
  proposals: Proposal[]
  total: number
}

interface ProposalsResponse {
  data?: {
    proposals?: Proposal[]
    summary?: {
      pending?: number
      approved?: number
      rejected?: number
    }
  }
}

interface AgentApiRecord {
  name: string
  display_name?: string
  status: string
  last_task?: string
  last_run?: string | null
  next_scheduled?: string | null
  blockers?: string[]
  tasks_completed?: number
  tasks_failed?: number
}

interface AgentsResponse {
  data?: {
    agents?: AgentApiRecord[]
  }
}

function normalizeAgent(agent: AgentApiRecord): SwarmAgent {
  return {
    id: agent.name,
    name: agent.display_name || agent.name,
    role: 'swarm',
    status: agent.status,
    last_task: agent.last_task,
    last_run: agent.last_run,
    next_scheduled: agent.next_scheduled,
    blockers: agent.blockers ?? [],
    tasks_completed: agent.tasks_completed ?? 0,
    tasks_failed: agent.tasks_failed ?? 0,
  }
}

export async function fetchProposals(): Promise<SwarmDigest> {
  try {
    const res = await fetch(`${API_BASE}/swarm/proposals`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = (await res.json()) as ProposalsResponse
    const proposals = json.data?.proposals ?? []
    const total = json.data?.summary?.pending ?? proposals.length

    return { proposals, total }
  } catch {
    return { proposals: [], total: 0 }
  }
}

export async function fetchAgents(): Promise<SwarmAgent[]> {
  try {
    const res = await fetch(`${API_BASE}/swarm/agents`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = (await res.json()) as AgentsResponse
    return (json.data?.agents ?? []).map(normalizeAgent)
  } catch {
    return []
  }
}

export async function actOnProposal(id: string, action: 'act' | 'dismiss' | 'defer' | 'execute'): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/swarm/proposals/${id}/${action}`, { method: 'POST' })
    return res.ok
  } catch {
    return false
  }
}
