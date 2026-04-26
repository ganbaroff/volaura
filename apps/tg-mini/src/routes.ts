import type { ComponentType } from 'react'

import { AgentsPage } from './pages/AgentsPage'
import { HomePage } from './pages/HomePage'
import { ProposalsPage } from './pages/ProposalsPage'

export const TG_MINI_CLASSIFICATION = 'admin-shell-prototype' as const

export interface TgMiniRoute {
  path: '/' | '/proposals' | '/agents'
  label: string
  icon: string
  component: ComponentType
}

export const TG_MINI_ROUTES: readonly TgMiniRoute[] = [
  { path: '/', label: 'Home', icon: '🏠', component: HomePage },
  { path: '/proposals', label: 'Tasks', icon: '📋', component: ProposalsPage },
  { path: '/agents', label: 'Agents', icon: '🤖', component: AgentsPage },
]
