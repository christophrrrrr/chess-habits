import type { Finding } from '../api'
import { percent } from '../format'
import { CardHeader } from './CardHeader'

interface Rate {
  count: number
  n: number
  rate: number | null
  ci: [number, number]
}

interface Flags {
  winning: number
  level: number
  losing: number
}

export interface ClockDetails {
  games_with_clock: number
  early_estimate: boolean
  entry: Rate
  scramble: Rate
  onset_move: { median: number | null; iqr: [number, number] | null }
  self_inflicted: Rate
  time_sinks: {
    entry_games?: number
    main_cause_share?: Record<'opening' | 'spikes' | 'drain', number>
  }
  pace: { wins: Record<string, number | null>; losses: Record<string, number | null> }
  flags: { lost_on_time: Flags; won_on_time: Flags; net_points_per_100: number }
}

const CAUSES: Array<{ key: 'opening' | 'spikes' | 'drain'; label: string }> = [
  { key: 'opening', label: 'Opening (moves 2–12)' },
  { key: 'spikes', label: 'Single long thinks' },
  { key: 'drain', label: 'Steady drain' },
]

function Tile({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="tile">
      <div className="tile__value">{value}</div>
      <div className="tile__label">{label}</div>
      {note && <div className="tile__note">{note}</div>}
    </div>
  )
}

export function ClockProfileCard({ finding }: { finding: Finding }) {
  const d = finding.details as unknown as ClockDetails
  const causes = d.time_sinks.main_cause_share
  const onset = d.onset_move.median
  const lost = d.flags.lost_on_time
  const won = d.flags.won_on_time
  const paceMoves = Object.keys(d.pace.wins)

  return (
    <article className="finding finding--profile" aria-label={finding.title}>
      <CardHeader finding={finding} />
      <p className="finding__summary">{finding.summary}</p>

      <div className="tiles">
        <Tile
          label="games with time trouble"
          value={percent(d.entry.rate)}
          note={`95% CI ${percent(d.entry.ci[0])}–${percent(d.entry.ci[1])}`}
        />
        <Tile label="starts around move" value={onset === null ? '–' : String(Math.round(onset))} />
        <Tile label="self-inflicted" value={percent(d.self_inflicted.rate)} note="opponent had more time" />
        <Tile label="lost on time while 3+ up" value={`≥ ${lost.winning}`} note="material count" />
      </div>

      {causes && (
        <section className="sinks" aria-label="Where the time went before time trouble">
          <h5>Main cause of time trouble ({d.time_sinks.entry_games} games)</h5>
          <div
            className="stack-bar"
            role="img"
            aria-label={CAUSES.map((c) => `${c.label} ${percent(causes[c.key])}`).join(', ')}
          >
            {CAUSES.filter((c) => causes[c.key] > 0).map((c) => (
              <div
                key={c.key}
                className={`stack-bar__seg stack-bar__seg--${c.key}`}
                style={{ flexGrow: causes[c.key] }}
                title={`${c.label}: ${percent(causes[c.key])}`}
              />
            ))}
          </div>
          <ul className="legend">
            {CAUSES.map((c) => (
              <li key={c.key}>
                <span className={`legend__swatch stack-bar__seg--${c.key}`} aria-hidden="true" />
                {c.label} <strong>{percent(causes[c.key])}</strong>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="two-col">
        <table className="mini">
          <caption>Clock left (share of expected game time)</caption>
          <thead>
            <tr>
              <th scope="col">After move</th>
              {paceMoves.map((m) => (
                <th key={m} scope="col">
                  {m}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Wins</th>
              {paceMoves.map((m) => (
                <td key={m}>{percent(d.pace.wins[m])}</td>
              ))}
            </tr>
            <tr>
              <th scope="row">Losses</th>
              {paceMoves.map((m) => (
                <td key={m}>{percent(d.pace.losses[m])}</td>
              ))}
            </tr>
          </tbody>
        </table>
        <table className="mini">
          <caption>Games decided on time, by final material</caption>
          <thead>
            <tr>
              <th scope="col" />
              <th scope="col">3+ up</th>
              <th scope="col">level</th>
              <th scope="col">3+ down</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Lost on time</th>
              <td>{lost.winning}</td>
              <td>{lost.level}</td>
              <td>{lost.losing}</td>
            </tr>
            <tr>
              <th scope="row">Won on time</th>
              <td>{won.winning}</td>
              <td>{won.level}</td>
              <td>{won.losing}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <footer className="finding__foot">
        Based on {d.games_with_clock} games with clock data · net clock points per 100 games:{' '}
        {d.flags.net_points_per_100 >= 0 ? '+' : '−'}
        {Math.abs(d.flags.net_points_per_100).toFixed(1)}
        {d.early_estimate && ' · early estimate'}
      </footer>
    </article>
  )
}
