import { describe, expect, it } from 'vitest'

import { TG_MINI_CLASSIFICATION, TG_MINI_ROUTES } from './routes'

describe('tg-mini route manifest', () => {
  it('classifies the surface as an admin shell prototype', () => {
    expect(TG_MINI_CLASSIFICATION).toBe('admin-shell-prototype')
  })

  it('declares only the currently shipped prototype routes', () => {
    expect(TG_MINI_ROUTES.map(route => route.path)).toEqual(['/', '/proposals', '/agents'])
    expect(TG_MINI_ROUTES.map(route => route.path)).not.toContain('/scene')
  })
})
