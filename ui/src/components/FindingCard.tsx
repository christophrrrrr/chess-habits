import type { Finding } from '../api'
import { axisPosition, elo, points } from '../format'
import type { RuleActions } from './AdoptButton'
import { CardHeader } from './CardHeader'
import { ClockProfileCard } from './ClockProfileCard'
import { HabitCharts } from './HabitCharts'
import { StopLossCard } from './StopLossCard'

/** Picks the right card for a finding. */
export function FindingCard({ finding, actions }: { finding: Finding; actions?: RuleActions }) {
  if (finding.analysis_key === 'clock_profile')
    return <ClockProfileCard finding={finding} actions={actions} />
  if (finding.analysis_key === 'stop_loss_rules') return <StopLossCard finding={finding} actions={actions} />
  if (finding.kind === 'profile') return <ProfileCard finding={finding} />
  return <ContrastCard finding={finding} />
}

/** A descriptive card: the text and its charts (time of day, openings, premoves, form). */
export function ProfileCard({ finding }: { finding: Finding }) {
  return (
    <article className="finding finding--profile" aria-label={finding.title}>
      <CardHeader finding={finding} />
      {finding.summary && <p className="finding__summary">{finding.summary}</p>}
      <HabitCharts finding={finding} />
      <footer className="finding__foot">
        Based on {finding.sample_size} {finding.analysis_key === 'premoves' ? 'moves' : 'games'}
      </footer>
    </article>
  )
}

/** Group A vs group B with the effect, its 95% interval and the minimum detectable effect. */
export function ContrastCard({ finding }: { finding: Finding }) {
  const { label, metric, mde } = finding
  const effect = finding.effect ?? 0
  const ci_low = finding.ci_low ?? 0
  const ci_high = finding.ci_high ?? 0
  const hasAxis = label !== 'not_enough_data' && finding.effect !== null && finding.ci_low !== null
  const significant = label === 'finding' || label === 'exploratory'
  // Only results (score) are good or bad; a behaviour share is just a description.
  const tone = significant && metric === 'score' ? (effect < 0 ? 'bad' : 'good') : 'neutral'
  const range = metric === 'share' ? 0.5 : 0.4
  const fmt = (x: number) => (metric === 'score' ? `${elo(x)} Elo` : `${points(x)} pp`)

  return (
    <article className={`finding finding--${tone}`} aria-label={finding.title}>
      <CardHeader finding={finding} />
      <p className="finding__summary">{finding.summary}</p>
      {hasAxis && (
        <div
          className="effect"
          role="img"
          aria-label={`Difference ${fmt(effect)}, 95% interval ${fmt(ci_low)} to ${fmt(ci_high)}`}
        >
          <div className="effect__track">
            <div className="effect__zero" />
            <div
              className="effect__ci"
              style={{
                left: `${axisPosition(ci_low, range)}%`,
                width: `${Math.max(axisPosition(ci_high, range) - axisPosition(ci_low, range), 0.5)}%`,
              }}
            />
            <div
              className="effect__dot"
              style={{ left: `${axisPosition(effect, range)}%` }}
              title={`${fmt(effect)} (95% CI ${fmt(ci_low)} to ${fmt(ci_high)})`}
            />
          </div>
          <div className="effect__labels">
            <span>{fmt(-range)}</span>
            <span>
              <strong>{fmt(effect)}</strong>
            </span>
            <span>{fmt(range)}</span>
          </div>
        </div>
      )}
      {label !== 'not_enough_data' && <HabitCharts finding={finding} />}
      <footer className="finding__foot">
        Based on {finding.sample_size} games
        {mde !== null && label !== 'not_enough_data' && (
          <>
            {' '}
            · smallest effect this data can detect:{' '}
            {metric === 'score' ? `${elo(mde)} Elo` : `${points(mde)} pp`}
          </>
        )}
      </footer>
    </article>
  )
}
