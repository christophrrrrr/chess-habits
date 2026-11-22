import type { Finding } from '../api'
import { AdoptButton, type RuleActions } from '../components/AdoptButton'
import { TileIcon } from '../components/TileIcon'
import { capitalize, LABEL_TEXT } from '../format'
import { buildPlan } from '../plan'
import { href } from '../routes'

const elo = (v: number) => `${Math.round(v)} Elo`
const perGame = (v: number) => (v >= 1 ? `≈ ${v.toFixed(0)} Elo per game` : '< 1 Elo per game')

/** The habits that cost the most, ranked by Elo over an average game, with one thing to do. */
export function PlanPage({
  playerId,
  findings,
  actions,
}: {
  playerId: number
  findings: Finding[]
  actions: RuleActions
}) {
  const { items, strengths } = buildPlan(findings)
  const unclear = findings.filter((f) => f.label === 'no_effect').length

  return (
    <div className="stack">
      <p className="muted">
        Ranked by how many points each habit costs you over an <strong>average</strong> game: the cost in the
        games it affects times how often it happens. Only habits with clear evidence are listed.
      </p>

      {items.length === 0 ? (
        <p className="panel">
          No habit costs you points clearly yet. That is a result too: with more games the cards can detect
          smaller effects.
        </p>
      ) : (
        <ol className="plan">
          {items.map((it, i) => (
            <li key={it.id} className="plan__item">
              <span className="plan__rank" aria-hidden="true">
                {i + 1}
              </span>
              <div className="plan__body">
                <div className="plan__head">
                  <span className="plan__icon">
                    <TileIcon name={it.analysisKey} size={18} />
                  </span>
                  <a
                    href={href({
                      page: 'player',
                      id: playerId,
                      view: 'finding',
                      tc: it.timeClass,
                      key: it.analysisKey,
                    })}
                    className="plan__title"
                  >
                    {it.title}
                  </a>
                </div>
                <p className="plan__numbers">
                  <strong>{perGame(it.perGameElo)}</strong> · {elo(it.costElo)} in{' '}
                  {Math.round(it.affects * 100)}% of your {it.timeClass} games ·{' '}
                  <span className={`badge badge--${it.evidence === 'clear' ? 'finding' : it.evidence}`}>
                    {it.evidence === 'clear' ? 'Clear' : LABEL_TEXT[it.evidence]}
                  </span>
                </p>
                <p className="plan__action">
                  <strong>Do this:</strong> {it.action}
                </p>
                {it.draft && <AdoptButton actions={actions} draft={it.draft} />}
              </div>
            </li>
          ))}
        </ol>
      )}

      {strengths.length > 0 && (
        <section aria-label="Keep doing">
          <h3 className="section-title">Keep doing</h3>
          <ul className="plan plan--good">
            {strengths.map((s) => (
              <li key={s.id} className="plan__item">
                <div className="plan__body">
                  <a
                    href={href({
                      page: 'player',
                      id: playerId,
                      view: 'finding',
                      tc: s.timeClass,
                      key: s.analysisKey,
                    })}
                    className="plan__title"
                  >
                    {capitalize(s.title.replace(/^[A-Z][a-z]+:\s*/, ''))}
                  </a>
                  <p className="plan__numbers">
                    +{elo(s.gainElo)} · {s.timeClass}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {unclear > 0 && (
        <p className="muted small">
          {unclear} other checks found no clear effect. Each card says how large an effect your games could
          have shown.
        </p>
      )}
    </div>
  )
}
