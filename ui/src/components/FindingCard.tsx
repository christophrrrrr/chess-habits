import type { Finding } from '../api'
import { CONFIDENCE_LABEL, axisPosition, points } from '../format'

const RANGE = 0.4 // axis shows -40 to +40 score points

export function FindingCard({ finding }: { finding: Finding }) {
  const { effect, ci_low, ci_high, confidence } = finding
  const showAxis = confidence !== 'insufficient'
  const tone = confidence === 'high' || confidence === 'medium' ? (effect < 0 ? 'bad' : 'good') : 'neutral'
  const lo = axisPosition(ci_low, RANGE)
  const hi = axisPosition(ci_high, RANGE)
  const mid = axisPosition(effect, RANGE)

  return (
    <article className={`finding finding--${tone}`} aria-label={finding.title}>
      <header className="finding__head">
        <h4>{finding.title}</h4>
        <span className={`badge badge--${confidence}`}>{CONFIDENCE_LABEL[confidence]}</span>
      </header>
      <p className="finding__summary">{finding.summary}</p>
      {showAxis && (
        <div
          className="effect"
          role="img"
          aria-label={`Effect ${points(effect)} points, 95% interval ${points(ci_low)} to ${points(ci_high)}`}
        >
          <div className="effect__track">
            <div className="effect__zero" />
            <div className="effect__ci" style={{ left: `${lo}%`, width: `${Math.max(hi - lo, 0.5)}%` }} />
            <div className="effect__dot" style={{ left: `${mid}%` }} />
          </div>
          <div className="effect__labels">
            <span>−40</span>
            <span>
              <strong>{points(effect)}</strong> points vs. the rest of your games
            </span>
            <span>+40</span>
          </div>
        </div>
      )}
      <footer className="finding__foot">Based on {finding.sample_size} games</footer>
    </article>
  )
}
