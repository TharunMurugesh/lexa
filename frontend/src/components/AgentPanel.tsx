import type { AgentLog } from '../lib/api'

const agents = ['Evidence', 'LegalResearch', 'Prosecutor', 'Defense', 'ContradictionDetector', 'Judge', 'Jury', 'AppealCourt']
const outputKeys: Record<string, string> = {
  Evidence: 'evidence',
  LegalResearch: 'retrieved_laws',
  Prosecutor: 'prosecution',
  Defense: 'defense',
  ContradictionDetector: 'contradictions',
  Judge: 'judge_reasoning',
  Jury: 'jury_vote',
  AppealCourt: 'appeal_decision',
}

type Props = {
  logs: AgentLog[]
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function unwrap(agent: string, output: unknown) {
  if (!isRecord(output)) return output
  return output[outputKeys[agent]] ?? output
}

function text(value: unknown): string {
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) return value.map(text).filter(Boolean).join(' ')
  if (isRecord(value)) return Object.values(value).map(text).filter(Boolean).join(' ')
  return ''
}

function lines(value: unknown) {
  if (Array.isArray(value)) return value.map(text).filter(Boolean)
  const line = text(value)
  return line ? [line] : []
}

function renderEvidence(value: unknown) {
  const record = isRecord(value) ? value : {}
  const groups = [
    ['Facts', lines(record.facts)],
    ['People', lines(record.people)],
    ['Dates', lines(record.dates)],
    ['Events', lines(record.events)],
  ].filter(([, items]) => Array.isArray(items) && items.length)

  return (
    <div className="agent-output">
      {groups.map(([label, items]) => (
        <div className="mini-block" key={label as string}>
          <strong>{label as string}</strong>
          <ul>
            {(items as string[]).map((item, index) => <li key={`${label}-${index}`}>{item}</li>)}
          </ul>
        </div>
      ))}
    </div>
  )
}

function renderLaws(value: unknown) {
  const laws = Array.isArray(value) ? value : []
  return (
    <div className="agent-output law-mini-list">
      {laws.map((item, index) => {
        const law = isRecord(item) ? item : {}
        return (
          <div className="mini-block" key={index}>
            <strong>{text(law.section) || 'Law citation'}</strong>
            <p>{text(law.text)}</p>
          </div>
        )
      })}
    </div>
  )
}

function renderContradictions(value: unknown) {
  const conflicts = Array.isArray(value) ? value : []
  if (!conflicts.length) return <p className="muted">No direct factual conflict found.</p>
  return (
    <div className="agent-output">
      {conflicts.map((item, index) => {
        const conflict = isRecord(item) ? item : {}
        return (
          <div className="mini-block" key={index}>
            <strong>{text(conflict.conflict) || 'Conflict'}</strong>
            <p>{text(conflict.statement_a)}</p>
            <p>{text(conflict.statement_b)}</p>
          </div>
        )
      })}
    </div>
  )
}

function renderJury(value: unknown) {
  const vote = isRecord(value) ? value : {}
  const votes = isRecord(vote.votes) ? vote.votes : {}
  return (
    <div className="agent-output jury-mini">
      <span className="verdict-chip">{text(vote.verdict) || 'Pending'}</span>
      <strong>{Math.round(Number(vote.confidence ?? 0) * 100)}% confidence</strong>
      <div className="vote-row">
        {Object.entries(votes).map(([label, count]) => (
          <span key={label}>{label.replace('_', ' ')}: {text(count)}</span>
        ))}
      </div>
    </div>
  )
}

function renderText(value: unknown) {
  return <div className="agent-output"><p>{text(value) || 'No output yet.'}</p></div>
}

function renderOutput(agent: string, value: unknown) {
  if (agent === 'Evidence') return renderEvidence(value)
  if (agent === 'LegalResearch') return renderLaws(value)
  if (agent === 'ContradictionDetector') return renderContradictions(value)
  if (agent === 'Jury') return renderJury(value)
  return renderText(value)
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
          const output = log ? unwrap(agent, log.output) : null
          return (
            <details className="agent-card" key={agent} open={Boolean(log)}>
              <summary>
                <span className={log ? 'dot done' : 'dot'} />
                <span>{agent}</span>
                <small>{log ? 'Done' : 'Waiting'}</small>
              </summary>
              {log ? renderOutput(agent, output) : <div className="agent-skeleton" />}
            </details>
          )
        })}
      </div>
    </section>
  )
}
