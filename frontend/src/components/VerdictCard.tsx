import type { Verdict } from '../lib/api'
import { LawCitations } from './LawCitations'

type Props = {
  verdict: Verdict | null
}

function verdictClass(value: string) {
  if (value === 'Guilty') return 'guilty'
  if (value === 'Not Guilty') return 'not-guilty'
  return 'insufficient'
}

function judgementStatement(verdict: Verdict, confidence: number) {
  if (verdict.verdict === 'Guilty') {
    return `Having considered the evidence, legal citations, opposing submissions, and jury confidence, this Court records a finding of guilt with ${confidence}% confidence.`
  }
  if (verdict.verdict === 'Not Guilty') {
    return `Having considered the evidence, legal citations, opposing submissions, and jury confidence, this Court records a finding of not guilty with ${confidence}% confidence.`
  }
  return `Having considered the evidence, legal citations, opposing submissions, and jury confidence, this Court finds that the present record is insufficient for a conclusive finding.`
}

export function VerdictCard({ verdict }: Props) {
  if (!verdict) {
    return (
      <section className="verdict-empty">
        <div className="section-heading">
          <span>Verdict</span>
          <strong>Awaiting analysis</strong>
        </div>
      </section>
    )
  }

  const confidence = Math.round((verdict.confidence ?? verdict.jury_vote?.confidence ?? 0) * 100)
  const votes = verdict.jury_vote?.votes ?? {}

  return (
    <section className="verdict-panel">
      <div className="verdict-top">
        <div>
          <span>Final verdict</span>
          <strong className={`verdict-badge ${verdictClass(verdict.verdict)}`}>{verdict.verdict}</strong>
        </div>
        <div className="confidence">
          <span>{confidence}%</span>
          <div><i style={{ width: `${confidence}%` }} /></div>
        </div>
      </div>
      <article className="judgement-statement">
        <h3>Final judgement statement</h3>
        <p>{judgementStatement(verdict, confidence)}</p>
      </article>
      <div className="argument-grid">
        <article>
          <h3>Prosecution</h3>
          <p>{verdict.prosecution_args}</p>
        </article>
        <article>
          <h3>Defense</h3>
          <p>{verdict.defense_args}</p>
        </article>
      </div>
      {verdict.evidence_summary && (
        <article>
          <h3>Evidence summary</h3>
          <p>{verdict.evidence_summary}</p>
        </article>
      )}
      <article>
        <h3>Judge reasoning</h3>
        <p>{verdict.judge_reasoning}</p>
      </article>
      <article>
        <h3>Jury vote</h3>
        <div className="vote-breakdown">
          {Object.entries(votes).map(([label, count]) => (
            <span key={label}>{label.replace('_', ' ')} <strong>{count}</strong></span>
          ))}
        </div>
      </article>
      <article>
        <h3>Contradictions</h3>
        <div className="contradiction-list">
          {verdict.contradictions.length === 0 && <p className="muted">No direct factual conflict found.</p>}
          {verdict.contradictions.map((item, index) => {
            const record = typeof item === 'object' && item !== null ? item as Record<string, unknown> : {}
            return (
              <div key={index}>
                <strong>{String(record.conflict ?? 'Conflict')}</strong>
                <p>{String(record.statement_a ?? '')}</p>
                <p>{String(record.statement_b ?? '')}</p>
              </div>
            )
          })}
        </div>
      </article>
      <article>
        <h3>Law citations</h3>
        <LawCitations laws={verdict.retrieved_laws ?? []} />
      </article>
      <article>
        <h3>Appeal review</h3>
        <p>{verdict.appeal_decision}</p>
      </article>
    </section>
  )
}
