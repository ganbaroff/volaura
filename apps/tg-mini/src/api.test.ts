import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchAgents, fetchProposals } from './api'

describe('tg-mini api envelope handling', () => {
  afterEach(() => {
    vi.restoreAllMocks()
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
})
