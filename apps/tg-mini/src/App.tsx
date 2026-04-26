import { AppRoot } from '@telegram-apps/telegram-ui'
import { HashRouter, Routes, Route } from 'react-router-dom'
import { NavBar } from './components/NavBar'
import { TG_MINI_ROUTES } from './routes'

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
            {TG_MINI_ROUTES.map(({ path, component: Component }) => (
              <Route key={path} path={path} element={<Component />} />
            ))}
          </Routes>
          <NavBar />
        </div>
      </HashRouter>
    </AppRoot>
  )
}
