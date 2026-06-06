import type { Verdict } from '../lib/api'
import { LawCitations } from './LawCitations'

type Props = {
  verdict: Verdict | null
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

  return (
    <section className="verdict-panel">
      <div className="verdict-top">
        <div>
          <span>Final verdict</span>
          <strong>{verdict.verdict}</strong>
        </div>
        <div className="confidence">
          <span>{confidence}%</span>
          <div><i style={{ width: `${confidence}%` }} /></div>
        </div>
      </div>
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
      <article>
        <h3>Judge reasoning</h3>
        <p>{verdict.judge_reasoning}</p>
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
