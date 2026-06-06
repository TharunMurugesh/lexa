import type { AgentLog } from '../lib/api'

const agents = ['Evidence', 'LegalResearch', 'Prosecutor', 'Defense', 'ContradictionDetector', 'Judge', 'Jury', 'AppealCourt']

type Props = {
  logs: AgentLog[]
}

export function AgentPanel({ logs }: Props) {
  return (
    <section>
      <div className="section-heading">
        <span>Live trace</span>
        <strong>Agent progress</strong>
      </div>
      <div className="agent-grid">
        {agents.map((agent) => {
          const log = logs.find((item) => item.agent_name === agent)
          return (
            <details className="agent-card" key={agent} open={Boolean(log)}>
              <summary>
                <span className={log ? 'dot done' : 'dot'} />
                <span>{agent}</span>
                <small>{log ? 'Done' : 'Waiting'}</small>
              </summary>
              <pre>{log ? JSON.stringify(log.output, null, 2) : 'Waiting for this step...'}</pre>
            </details>
          )
        })}
      </div>
    </section>
  )
}
