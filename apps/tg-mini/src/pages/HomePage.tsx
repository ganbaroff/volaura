import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchProposals, type Proposal } from '../api'

export function HomePage() {
  const navigate = useNavigate()
  const [critical, setCritical] = useState(0)
  const [pending, setPending] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProposals().then(data => {
      const all = data.proposals || []
      setCritical(all.filter(p => p.severity === 'critical' && p.status === 'pending').length)
      setPending(all.filter(p => p.status === 'pending').length)
      setLoading(false)
    })
  }, [])

  return (
    <div style={{ padding: 16 }}>
      {/* ADHD-safe: one primary action (Law 5), warm greeting (Law 3) */}
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>VOLAURA Swarm</h1>
      <p style={{ color: '#8B8BA7', fontSize: 13, marginBottom: 20 }}>Your agents are working.</p>

      {loading ? (
        <div style={{ color: '#8B8BA7', textAlign: 'center', padding: 40 }}>Loading...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Stats cards */}
          <div style={{ display: 'flex', gap: 12 }}>
            <StatCard
              label="Critical"
              value={critical}
              color={critical > 0 ? '#D4B4FF' : '#4ECDC4'}
              onClick={() => navigate('/proposals')}
            />
            <StatCard
              label="Pending"
              value={pending}
              color="#F59E0B"
              onClick={() => navigate('/proposals')}
            />
          </div>

          {/* Primary CTA — one action (Law 5) */}
          <button
            onClick={() => navigate('/proposals')}
            style={{
              width: '100%',
              padding: '16px',
              background: 'linear-gradient(135deg, #7B72FF, #4ECDC4)',
              border: 'none',
              borderRadius: 14,
              color: 'white',
              fontSize: 16,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Review Proposals
          </button>

          {/* Secondary — ghost style */}
          <button
            onClick={() => navigate('/agents')}
            style={{
              width: '100%',
              padding: '14px',
              background: 'transparent',
              border: '1px solid #292932',
              borderRadius: 14,
              color: '#8B8BA7',
              fontSize: 14,
              cursor: 'pointer',
            }}
          >
            View Agents
          </button>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color, onClick }: {
  label: string
  value: number
  color: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        padding: '16px',
        background: '#1B1B23',
        border: '1px solid #292932',
        borderRadius: 14,
        textAlign: 'center',
        cursor: 'pointer',
      }}
    >
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 12, color: '#8B8BA7', marginTop: 4 }}>{label}</div>
    </button>
  )
}
