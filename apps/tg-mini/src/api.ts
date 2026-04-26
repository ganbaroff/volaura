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
  tasks_completed: number
  quality_score?: number
}

export interface SwarmDigest {
  proposals: Proposal[]
  total: number
}

export async function fetchProposals(): Promise<SwarmDigest> {
  try {
    const res = await fetch(`${API_BASE}/swarm/proposals`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } catch {
    return { proposals: [], total: 0 }
  }
}

export async function fetchAgents(): Promise<SwarmAgent[]> {
  try {
    const res = await fetch(`${API_BASE}/swarm/agents`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    return data.agents || []
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
