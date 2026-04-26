import { useEffect, useState } from 'react'
import { fetchProposals, actOnProposal, type Proposal } from '../api'

const SEV_COLOR: Record<string, string> = {
  // Law 1: no red. Critical = purple, high = amber
  critical: '#D4B4FF',
  high: '#F59E0B',
  medium: '#8B8BA7',
  low: '#4ECDC4',
}

export function ProposalsPage() {
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [acting, setActing] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    fetchProposals().then(data => {
      setProposals(data.proposals?.filter(p => p.status === 'pending') || [])
      setLoading(false)
    })
  }

  useEffect(() => { load() }, [])

  const handleAction = async (id: string, action: 'approve' | 'dismiss' | 'defer') => {
    setActing(id)
    const ok = await actOnProposal(id, action)
    if (ok) {
      setProposals(prev => prev.filter(p => p.id !== id))
    }
    setActing(null)
  }

  if (loading) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#8B8BA7' }}>Loading proposals...</div>
  }

  if (!proposals.length) {
    // Law 3: warm empty state, no shame
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>✨</div>
        <div style={{ color: '#E8E8F0', fontSize: 16, fontWeight: 600 }}>All clear</div>
        <div style={{ color: '#8B8BA7', fontSize: 13, marginTop: 4 }}>Agents haven't found anything urgent.</div>
      </div>
    )
  }

  return (
    <div style={{ padding: 16 }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>
        Proposals ({proposals.length})
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {proposals.map(p => {
          const isExpanded = expanded === p.id
          const isActing = acting === p.id

          return (
            <div
              key={p.id}
              style={{
                background: '#1B1B23',
                border: `1px solid ${isExpanded ? SEV_COLOR[p.severity] || '#292932' : '#292932'}`,
                borderRadius: 14,
                overflow: 'hidden',
              }}
            >
              {/* Header — tap to expand */}
              <button
                onClick={() => setExpanded(isExpanded ? null : p.id)}
                style={{
                  width: '100%',
                  padding: '14px 16px',
                  background: 'none',
                  border: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: SEV_COLOR[p.severity] || '#8B8BA7',
                  flexShrink: 0,
                }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    color: '#E8E8F0', fontSize: 14, fontWeight: 600,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {p.title}
                  </div>
                  <div style={{ color: '#8B8BA7', fontSize: 11, marginTop: 2 }}>
                    {p.agent} · {p.severity}
                    {p.judge_score != null && ` · ${p.judge_score}/5`}
                  </div>
                </div>
                <span style={{ color: '#8B8BA7', fontSize: 12 }}>{isExpanded ? '▲' : '▼'}</span>
              </button>

              {/* Expanded content + action buttons */}
              {isExpanded && (
                <div style={{ padding: '0 16px 14px' }}>
                  <p style={{
                    color: '#8B8BA7', fontSize: 13, lineHeight: 1.5,
                    marginBottom: 14, maxHeight: 120, overflow: 'auto',
                  }}>
                    {p.content?.slice(0, 400)}
                  </p>

                  {/* Action buttons — ADHD-safe: clear labels, no ambiguity */}
                  <div style={{ display: 'flex', gap: 8 }}>
                    <ActionButton
                      label="✅ Approve"
                      bg="#4ECDC433"
                      color="#4ECDC4"
                      disabled={isActing}
                      onClick={() => handleAction(p.id, 'approve')}
                    />
                    <ActionButton
                      label="⏳ Defer"
                      bg="#7B72FF33"
                      color="#7B72FF"
                      disabled={isActing}
                      onClick={() => handleAction(p.id, 'defer')}
                    />
                    <ActionButton
                      label="❌ Reject"
                      bg="#8B8BA722"
                      color="#8B8BA7"
                      disabled={isActing}
                      onClick={() => handleAction(p.id, 'dismiss')}
                    />
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ActionButton({ label, bg, color, disabled, onClick }: {
  label: string; bg: string; color: string; disabled: boolean; onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        flex: 1,
        padding: '10px 4px',
        background: bg,
        border: 'none',
        borderRadius: 10,
        color,
        fontSize: 12,
        fontWeight: 600,
        cursor: disabled ? 'default' : 'pointer',
        opacity: disabled ? 0.5 : 1,
      }}
    >
      {label}
    </button>
  )
}
