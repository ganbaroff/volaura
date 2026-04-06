import { AppRoot } from '@telegram-apps/telegram-ui'
import { HashRouter, Routes, Route } from 'react-router-dom'
import { ProposalsPage } from './pages/ProposalsPage'
import { AgentsPage } from './pages/AgentsPage'
import { HomePage } from './pages/HomePage'
import { NavBar } from './components/NavBar'

export function App() {
  // ADHD-safe: dark theme, calm colors, no red (Law 1)
  // HashRouter: Telegram Mini Apps don't support BrowserRouter (no server-side routing)
  return (
    <AppRoot appearance="dark">
      <HashRouter>
        <div style={{
          minHeight: '100vh',
          background: '#0F1117',
          color: '#E8E8F0',
          paddingBottom: 72,
        }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/proposals" element={<ProposalsPage />} />
            <Route path="/agents" element={<AgentsPage />} />
          </Routes>
          <NavBar />
        </div>
      </HashRouter>
    </AppRoot>
  )
}
