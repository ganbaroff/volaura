import { useEffect, useState } from 'react'
import { fetchAgents, type SwarmAgent } from '../api'

const STATUS_DOT: Record<string, string> = {
  active: '#4ECDC4',
  running: '#7B72FF',
  idle: '#F59E0B',
  new: '#8B8BA7',
}

export function AgentsPage() {
  const [agents, setAgents] = useState<SwarmAgent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAgents().then(data => {
      setAgents(data.sort((a, b) => b.tasks_completed - a.tasks_completed))
      setLoading(false)
    })
  }, [])

  if (loading) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#8B8BA7' }}>Loading agents...</div>
  }

  const active = agents.filter(a => a.tasks_completed > 0)
  const dormant = agents.filter(a => a.tasks_completed === 0)

  return (
    <div style={{ padding: 16 }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
        Agents ({agents.length})
      </h2>
      <p style={{ color: '#8B8BA7', fontSize: 12, marginBottom: 16 }}>
        {active.length} active · {dormant.length} dormant
      </p>

      {active.map(agent => (
        <AgentRow key={agent.id} agent={agent} />
      ))}

      {dormant.length > 0 && (
        <>
          <div style={{ color: '#8B8BA7', fontSize: 12, margin: '16px 0 8px', fontWeight: 600 }}>
            Dormant
          </div>
          {dormant.slice(0, 10).map(agent => (
            <AgentRow key={agent.id} agent={agent} dimmed />
          ))}
          {dormant.length > 10 && (
            <div style={{ color: '#8B8BA7', fontSize: 11, textAlign: 'center', padding: 8 }}>
              +{dormant.length - 10} more
            </div>
          )}
        </>
      )}
    </div>
  )
}

function AgentRow({ agent, dimmed }: { agent: SwarmAgent; dimmed?: boolean }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '10px 0',
      borderBottom: '1px solid #1F1F27',
      opacity: dimmed ? 0.5 : 1,
    }}>
      <span style={{
        width: 8, height: 8, borderRadius: '50%',
        background: STATUS_DOT[agent.status] || '#8B8BA7',
        flexShrink: 0,
      }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          color: '#E8E8F0', fontSize: 13, fontWeight: 600,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {agent.name || agent.id}
        </div>
        {agent.last_task && (
          <div style={{
            color: '#8B8BA7', fontSize: 11, marginTop: 1,
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {agent.last_task}
          </div>
        )}
      </div>
      <div style={{ color: '#4ECDC4', fontSize: 12, fontWeight: 600, flexShrink: 0 }}>
        {agent.tasks_completed}
      </div>
    </div>
  )
}
