import { useState } from 'react'
import type { Finding, Rule } from '../api'
import { formatDate, LABEL_TEXT, percent } from '../format'
import { MethodsLink } from './MethodsLink'
import { Tile } from './Tile'

interface Rate {
  count: number
  n: number
  rate: number | null
}

interface RuleCheckDetails {
  rule_id: number
  adopted_at: string
  needed: number
  after: Rate
  before: Rate
  strip: Array<{ date: string; kept: boolean }>
  trouble?: { before: Rate; after: Rate }
  games_past_stop?: { before: number; after: number }
}

/** An adopted rule and, once an analysis has run since adoption, whether it was kept. */
export function RuleCard({
  rule,
  check,
  onRetire,
}: {
  rule: Rule
  check?: Finding
  onRetire: (rule: Rule) => Promise<void>
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const d = check?.details as unknown as RuleCheckDetails | undefined
  // A check computed for an older version of the rule (threshold changed since) is stale.
  const current = d && d.adopted_at === rule.adopted_at ? d : undefined
  const label = current ? check!.label : 'not_enough_data'
  const unit = rule.kind === 'clock_checkpoint' ? 'games' : 'sessions'
  const tone =
    (label === 'finding' || label === 'exploratory') && check!.effect !== null
      ? check!.effect > 0
        ? 'good'
        : 'bad'
      : 'profile'

  async function retire() {
    setBusy(true)
    try {
      await onRetire(rule)
    } catch (e) {
      setError((e as Error).message)
      setBusy(false)
    }
  }

  return (
    <article className={`finding finding--${tone} rule`} aria-label={`Rule: ${rule.description}`}>
      <header className="finding__head">
        <h4>{current ? check!.title : `Your rule: ${rule.description}`}</h4>
        <span className="finding__meta">
          <span className={`badge badge--${label}`}>
            {label === 'not_enough_data' ? 'Too early' : LABEL_TEXT[label]}
          </span>
          <MethodsLink section="rules" />
        </span>
      </header>
      <p className="finding__summary">
        {current
          ? check!.summary
          : `Adopted ${formatDate(rule.adopted_at)}. Progress shows after your next import and analysis.`}
      </p>
      {current && (
        <>
          <div className="tiles">
            <Tile
              label={`kept since adoption`}
              value={percent(current.after.rate)}
              note={`${current.after.count} of ${current.after.n} ${unit}`}
            />
            <Tile
              label="kept before (baseline)"
              value={percent(current.before.rate)}
              note={`${current.before.n} ${unit}`}
            />
            {current.trouble && (
              <Tile
                label="games with time trouble"
                value={`${percent(current.trouble.before.rate)} → ${percent(current.trouble.after.rate)}`}
                note="before → since"
              />
            )}
            {current.games_past_stop && (
              <Tile
                label="games played past the stop"
                value={`${current.games_past_stop.before} → ${current.games_past_stop.after}`}
                note="before → since"
              />
            )}
          </div>
          {current.strip.length > 0 && <Strip strip={current.strip} unit={unit} />}
        </>
      )}
      <footer className="finding__foot rule__foot">
        <span>
          Adopted {formatDate(rule.adopted_at)}
          {current && current.after.n < current.needed && ` · verdict after ${current.needed} ${unit}`}
        </span>
        <button className="link danger" onClick={retire} disabled={busy}>
          Stop tracking
        </button>
      </footer>
      {error && <p className="error">{error}</p>}
    </article>
  )
}

function Strip({ strip, unit }: { strip: RuleCheckDetails['strip']; unit: string }) {
  const kept = strip.filter((s) => s.kept).length
  return (
    <div className="strip-wrap">
      <div
        className="strip"
        role="img"
        aria-label={`Last ${strip.length} ${unit}: kept ${kept}, broken ${strip.length - kept}`}
      >
        {strip.map((s, i) => (
          <span
            key={i}
            className={`strip__cell strip__cell--${s.kept ? 'kept' : 'broken'}`}
            title={`${formatDate(s.date)}: ${s.kept ? 'kept' : 'broken'}`}
          />
        ))}
      </div>
      <ul className="legend">
        <li>
          <span className="legend__swatch strip__cell--kept" aria-hidden="true" />
          kept
        </li>
        <li>
          <span className="legend__swatch strip__cell--broken" aria-hidden="true" />
          broken
        </li>
      </ul>
    </div>
  )
}
