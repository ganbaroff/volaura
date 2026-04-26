import { afterEach, describe, expect, it, vi } from 'vitest'

import { actOnProposal, fetchAgents, fetchProposals } from './api'

describe('tg-mini api envelope handling', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('unwraps proposals from the admin data envelope', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            proposals: [{ id: 'p-1', title: 'Fix drift', content: '...', agent: 'Atlas', severity: 'high', status: 'pending', votes_for: 3, votes_against: 0 }],
            summary: { pending: 7, approved: 1, rejected: 2 },
          },
        }),
      }),
    )

    await expect(fetchProposals()).resolves.toEqual({
      proposals: [
        {
          id: 'p-1',
          title: 'Fix drift',
          content: '...',
          agent: 'Atlas',
          severity: 'high',
          status: 'pending',
          votes_for: 3,
          votes_against: 0,
        },
      ],
      total: 7,
    })
  })

  it('unwraps agents and normalizes ids from the admin data envelope', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            agents: [
              {
                name: 'qa-quality-agent',
                display_name: 'Qa Quality',
                status: 'idle',
                last_task: 'DoD verification',
                tasks_completed: 4,
                tasks_failed: 1,
              },
            ],
          },
        }),
      }),
    )

    await expect(fetchAgents()).resolves.toEqual([
      {
        id: 'qa-quality-agent',
        name: 'Qa Quality',
        role: 'swarm',
        status: 'idle',
        last_task: 'DoD verification',
        last_run: undefined,
        next_scheduled: undefined,
        blockers: [],
        tasks_completed: 4,
        tasks_failed: 1,
      },
    ])
  })

  it('posts proposal decisions to the decide route with the backend action shape', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true })
    vi.stubGlobal('fetch', fetchMock)

    await expect(actOnProposal('p-42', 'approve')).resolves.toBe(true)

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/swarm/proposals/p-42/decide'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ action: 'approve' }),
      }),
    )

    // Headers come back as a Headers instance (api.ts uses authHeaders({...}))
    // not a plain object literal — assert content-type via Headers semantics.
    const requestInit = fetchMock.mock.calls[0]?.[1] as RequestInit
    const headers = requestInit.headers as Headers
    expect(headers.get('Content-Type')).toBe('application/json')
  })

  it('adds the stored bearer token to admin requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { agents: [] } }),
    })

    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('window', {
      location: {
        href: 'https://mini.volaura.app/#/agents',
        search: '',
        hash: '#/agents',
      },
      sessionStorage: {
        getItem: vi.fn().mockReturnValue('stored-jwt'),
        setItem: vi.fn(),
      },
      history: { replaceState: vi.fn() },
      document: { title: 'tg-mini' },
    })

    await fetchAgents()

    const requestInit = fetchMock.mock.calls[0]?.[1] as RequestInit
    const headers = requestInit.headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer stored-jwt')
  })

  it('bootstraps a bearer token from the URL, stores it, and scrubs the location', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { proposals: [], summary: { pending: 0 } } }),
    })
    const getItem = vi.fn().mockReturnValue(null)
    const setItem = vi.fn()
    const replaceState = vi.fn()

    vi.stubGlobal('fetch', fetchMock)
    vi.stubGlobal('window', {
      location: {
        href: 'https://mini.volaura.app/#/proposals?access_token=bridge-jwt',
        search: '',
        hash: '#/proposals?access_token=bridge-jwt',
      },
      sessionStorage: {
        getItem,
        setItem,
      },
      history: { replaceState },
      document: { title: 'tg-mini' },
    })

    await fetchProposals()

    const requestInit = fetchMock.mock.calls[0]?.[1] as RequestInit
    const headers = requestInit.headers as Headers

    expect(headers.get('Authorization')).toBe('Bearer bridge-jwt')
    expect(setItem).toHaveBeenCalledWith('volaura.tg-mini.access-token', 'bridge-jwt')
    expect(replaceState).toHaveBeenCalledWith({}, 'tg-mini', '/#/proposals')
  })
})
