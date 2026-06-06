import type { CaseSummary } from '../lib/api'

type Props = {
  cases: CaseSummary[]
  activeCaseId: string
  onSelect: (caseId: string) => void
}

export function CaseHistory({ cases, activeCaseId, onSelect }: Props) {
  return (
    <section>
      <div className="section-heading">
        <span>Persistence</span>
        <strong>Case history</strong>
      </div>
      <div className="history-list">
        {cases.length === 0 && <p className="muted">No cases yet.</p>}
        {cases.map((item) => (
          <button className={item.id === activeCaseId ? 'history-row active' : 'history-row'} key={item.id} onClick={() => onSelect(item.id)}>
            <span>{item.title}</span>
            <small>{item.verdict?.verdict ?? item.status}</small>
          </button>
        ))}
      </div>
    </section>
  )
}
