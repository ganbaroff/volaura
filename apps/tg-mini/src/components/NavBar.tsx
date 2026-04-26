import { useLocation, useNavigate } from 'react-router-dom'
import { TG_MINI_ROUTES } from '../routes'

export function NavBar() {
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: 64,
      background: '#1B1B23',
      borderTop: '1px solid #292932',
      display: 'flex',
      justifyContent: 'space-around',
      alignItems: 'center',
      zIndex: 50,
    }}>
      {TG_MINI_ROUTES.map(tab => {
        const active = location.pathname === tab.path
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 2,
              background: 'none',
              border: 'none',
              // ADHD-safe: teal for active, muted for inactive (Law 1: no red)
              color: active ? '#4ECDC4' : '#8B8BA7',
              fontSize: 22,
              cursor: 'pointer',
              padding: '8px 16px',
            }}
          >
            <span>{tab.icon}</span>
            <span style={{ fontSize: 10, fontWeight: active ? 600 : 400 }}>{tab.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
