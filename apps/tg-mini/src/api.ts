// API client for VOLAURA backend (Railway)
const API_BASE = import.meta.env.VITE_API_URL || 'https://modest-happiness-production.up.railway.app/api'
const ACCESS_TOKEN_STORAGE_KEY = 'volaura.tg-mini.access-token'
const TOKEN_PARAM_KEYS = ['access_token', 'token'] as const

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

function readStoredAccessToken(): string | null {
  if (typeof window === 'undefined') return null

  try {
    return window.sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

function persistAccessToken(token: string): void {
  if (typeof window === 'undefined') return

  try {
    window.sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token)
  } catch {
    // Ignore storage failures — requests can still proceed with the in-memory token.
  }
}

function extractTokenFromLocation(): string | null {
  if (typeof window === 'undefined') return null

  const candidates = [new URLSearchParams(window.location.search)]
  const hash = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : window.location.hash
  const hashQueryIndex = hash.indexOf('?')

  if (hashQueryIndex >= 0) {
    candidates.push(new URLSearchParams(hash.slice(hashQueryIndex + 1)))
  } else if (hash.includes('=')) {
    candidates.push(new URLSearchParams(hash))
  }

  for (const params of candidates) {
    for (const key of TOKEN_PARAM_KEYS) {
      const value = params.get(key)?.trim()
      if (value) return value
    }
  }

  return null
}

function stripTokenFromLocation(): void {
  if (typeof window === 'undefined' || typeof window.history?.replaceState !== 'function') return

  const url = new URL(window.location.href)
  let dirty = false

  for (const key of TOKEN_PARAM_KEYS) {
    if (url.searchParams.has(key)) {
      url.searchParams.delete(key)
      dirty = true
    }
  }

  const hash = url.hash.startsWith('#') ? url.hash.slice(1) : url.hash
  const hashQueryIndex = hash.indexOf('?')
  if (hashQueryIndex >= 0) {
    const hashPath = hash.slice(0, hashQueryIndex)
    const hashParams = new URLSearchParams(hash.slice(hashQueryIndex + 1))
    let hashDirty = false

    for (const key of TOKEN_PARAM_KEYS) {
      if (hashParams.has(key)) {
        hashParams.delete(key)
        hashDirty = true
      }
    }

    if (hashDirty) {
      url.hash = hashParams.toString() ? `#${hashPath}?${hashParams.toString()}` : `#${hashPath}`
      dirty = true
    }
  }

  if (dirty) {
    window.history.replaceState({}, window.document?.title ?? '', `${url.pathname}${url.search}${url.hash}`)
  }
}

function getAccessToken(): string | null {
  const stored = readStoredAccessToken()
  if (stored) return stored

  const token = extractTokenFromLocation()
  if (!token) return null

  persistAccessToken(token)
  stripTokenFromLocation()
  return token
}

function authHeaders(init?: HeadersInit): Headers {
  const headers = new Headers(init)
  const token = getAccessToken()

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  return headers
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
    const res = await fetch(`${API_BASE}/swarm/proposals`, { headers: authHeaders() })
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
    const res = await fetch(`${API_BASE}/swarm/agents`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = (await res.json()) as AgentsResponse
    return (json.data?.agents ?? []).map(normalizeAgent)
  } catch {
    return []
  }
}

export async function actOnProposal(id: string, action: 'approve' | 'dismiss' | 'defer'): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/swarm/proposals/${id}/decide`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ action }),
    })
    return res.ok
  } catch {
    return false
  }
}
