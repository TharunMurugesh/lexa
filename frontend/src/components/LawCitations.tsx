type Props = {
  laws: Array<{ section: string; text: string; relevance?: number }>
}

export function LawCitations({ laws }: Props) {
  if (!laws.length) return <p className="muted">No citations returned.</p>

  return (
    <div className="citation-list">
      {laws.map((law, index) => (
        <details key={`${law.section}-${index}`} open={index === 0}>
          <summary>
            <span>{law.section}</span>
            <small>Relevance {law.relevance ?? 0}</small>
          </summary>
          <p>{law.text}</p>
        </details>
      ))}
    </div>
  )
}
