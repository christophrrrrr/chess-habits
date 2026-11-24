// Charts for every finding except the clock profile (which has its own card).
import type { Finding } from '../api'
import { percent, shortOpening } from '../format'
import { Board } from './Board'
import { ColumnChart, IntervalChart, LineChart } from './charts'

const signedElo = (v: number) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(Math.round(v))}`
const count = (v: number) => String(Math.round(v))

interface SessionPoint {
  game: number
  plus: boolean
  elo: number
  low: number
  high: number
  games: number
}

interface Window {
  window: string
  name: string
  games: number
  elo?: number
  low?: number
  high?: number
  verdict: string
}

interface Opening {
  opening: string
  games: number
  used: number | null
  elo: number | null
  low: number | null
  high: number | null
}

interface Month {
  month: string
  games: number
  rating: number | null
  elo: number | null
}

/** The charts that belong to a finding, or null when it has none. */
export function HabitCharts({ finding }: { finding: Finding }) {
  const d = finding.details as Record<string, unknown>
  const charts = (d.charts ?? {}) as Record<string, unknown>

  switch (finding.analysis_key) {
    case 'after_loss_result':
    case 'warm_up': {
      const points = (charts.by_session_game ?? []) as SessionPoint[]
      if (points.length === 0) return null
      return (
        <IntervalChart
          title="Your score by game in the session"
          note="Elo against your own level, game 1 = first game after a break of 30+ minutes. Bars are 95% intervals."
          rows={points.map((p) => ({
            label: `Game ${p.game}${p.plus ? '+' : ''}`,
            value: p.elo,
            low: p.low,
            high: p.high,
            note: `${p.games} games`,
            verdict: p.high < 0 ? 'bad' : p.low > 0 ? 'good' : null,
          }))}
          format={signedElo}
        />
      )
    }
    case 'after_loss_requeue': {
      const gap = charts.next_game_gap as
        { after_loss: Record<string, number> | null; after_win: Record<string, number> | null } | undefined
      if (!gap?.after_loss || !gap.after_win) return null
      const buckets = Object.keys(gap.after_loss)
      return (
        <ColumnChart
          title="Time before your next game"
          note="Share of losses and wins by how long you waited before starting the next game."
          categories={buckets}
          series={[
            { name: 'After a loss', values: buckets.map((b) => gap.after_loss![b]) },
            { name: 'After a win', values: buckets.map((b) => gap.after_win![b]) },
          ]}
          format={(v) => percent(v)}
        />
      )
    }
    case 'time_of_day': {
      const windows = (d.windows ?? []) as Window[]
      const hours = (d.games_by_hour ?? []) as number[]
      return (
        <>
          <IntervalChart
            title="Your score by time of day"
            note="Elo against your own level for games you start in each window. Darker dots differ clearly from the rest of the day."
            rows={windows.map((w) => ({
              label: w.name.replace(/^(at|in the) /, ''),
              value: w.elo ?? null,
              low: w.low ?? null,
              high: w.high ?? null,
              note: `${w.games} games`,
              verdict: w.verdict === 'worse' ? 'bad' : w.verdict === 'better' ? 'good' : null,
            }))}
            format={signedElo}
          />
          {hours.length === 24 && (
            <ColumnChart
              title="When you play"
              note="Games by the hour they started, in your time zone."
              categories={hours.map((_, h) => `${h}`)}
              series={[{ name: 'Games', values: hours }]}
              format={count}
              height={160}
            />
          )}
        </>
      )
    }
    case 'opening_time': {
      const ops = (d.openings ?? []) as Opening[]
      if (ops.length === 0) return null
      return (
        <div className="charts-grid">
          <ColumnChart
            title={`Clock used by move ${d.move as number}`}
            note="Median share of the expected game time, by opening."
            categories={ops.map((o) => shortOpening(o.opening))}
            series={[{ name: 'Clock used', values: ops.map((o) => o.used) }]}
            format={(v) => percent(v)}
          />
          <IntervalChart
            title="Your score by opening"
            note="Elo against your own level. Bars are 95% intervals."
            rows={ops.map((o) => ({
              label: shortOpening(o.opening),
              value: o.elo,
              low: o.low,
              high: o.high,
              note: `${o.games} games`,
              verdict: o.high !== null && o.high < 0 ? 'bad' : o.low !== null && o.low > 0 ? 'good' : null,
            }))}
            format={signedElo}
          />
        </div>
      )
    }
    case 'premoves': {
      const bands = (d.by_clock ?? []) as Array<{ clock_left: string; rate: number | null }>
      return (
        <ColumnChart
          title="Premoves by clock left"
          note="Share of your moves that were premoves, by how much of the expected game time you had left."
          categories={bands.map((b) => b.clock_left)}
          series={[{ name: 'Premoves', values: bands.map((b) => b.rate) }]}
          format={(v) => percent(v)}
        />
      )
    }
    case 'form': {
      const months = (d.months ?? []) as Month[]
      return (
        <>
          <LineChart
            title="Rating by month"
            note="Median of your ratings in each month."
            x={months.map((m) => m.month)}
            xLabel="Month"
            series={[{ name: 'Rating', values: months.map((m) => m.rating) }]}
            format={count}
            yMin={Math.min(...months.map((m) => m.rating ?? Infinity)) - 50}
          />
          <ColumnChart
            title="Games by month"
            categories={months.map((m) => m.month.slice(2))}
            series={[{ name: 'Games', values: months.map((m) => m.games) }]}
            format={count}
            height={160}
          />
        </>
      )
    }
    case 'critical_moments': {
      const c = d.critical as { rate: number | null } | undefined
      const overall = c?.rate ?? null
      const cells = (key: string) =>
        ((d[key] ?? []) as Array<{ name: string; n: number; rate: number | null; ci: [number, number] }>).map(
          (x) => ({
            label: x.name,
            value: x.rate,
            low: x.ci[0],
            high: x.ci[1],
            note: `${x.n} positions`,
            verdict:
              overall !== null && x.ci[1] < overall
                ? ('bad' as const)
                : overall !== null && x.ci[0] > overall
                  ? ('good' as const)
                  : null,
          }),
        )
      const ref = overall !== null ? { value: overall, label: `overall ${percent(overall)}` } : undefined
      const missed = (d.missed ?? []) as Array<{ fen: string; best: string; lost: number; k: number }>
      return (
        <>
          <IntervalChart
            title="Find rate by the kind of move needed"
            note="Share of critical positions where you found a good move, with 95% intervals. Darker dots differ clearly from your overall rate."
            rows={cells('by_type')}
            format={(v) => percent(v)}
            domain={[0, 1]}
            reference={ref}
          />
          <div className="charts-grid">
            <IntervalChart
              title="By clock left"
              rows={cells('by_clock')}
              format={(v) => percent(v)}
              domain={[0, 1]}
              reference={ref}
            />
            <IntervalChart
              title="By time you took, and what was at stake"
              rows={[...cells('by_speed'), ...cells('by_purpose')]}
              format={(v) => percent(v)}
              domain={[0, 1]}
              reference={ref}
            />
          </div>
          {missed.length > 0 && (
            <section className="missed" aria-label="Positions you missed">
              <h5>Positions you missed (biggest losses first)</h5>
              <p className="muted small">The best move is highlighted. Cover it and find the move first.</p>
              <div className="missed__grid">
                {missed.slice(0, 6).map((m) => (
                  <figure key={m.fen} className="missed__item">
                    <Board
                      fen={m.fen}
                      flip={m.fen.split(' ')[1] === 'b'}
                      highlight={[m.best.slice(0, 2), m.best.slice(2, 4)]}
                      label={`Your move ${m.k}; best move ${m.best}`}
                    />
                    <figcaption className="muted small">
                      Move {m.k} · best {m.best} · you lost {Math.round(m.lost)} win% points
                    </figcaption>
                  </figure>
                ))}
              </div>
            </section>
          )}
        </>
      )
    }
    case 'endings': {
      const r = d.resignations as { n: number; premature_by_threshold: Record<string, number> } | undefined
      const lost = (d.lost_on_time ?? {}) as Record<string, number>
      const won = (d.won_on_time ?? {}) as Record<string, number>
      const keys = ['winning', 'level', 'losing']
      return (
        <div className="charts-grid">
          {r && r.n > 0 && (
            <ColumnChart
              title="Resignations with score still left"
              note={`Share of your ${r.n} resignations where you still had at least this expected score.`}
              categories={['10%+', '15%+', '25%+']}
              series={[
                {
                  name: 'Resignations',
                  values: ['0.1', '0.15', '0.25'].map((t) => (r.premature_by_threshold[t] ?? 0) / r.n),
                },
              ]}
              format={(v) => percent(v)}
            />
          )}
          <ColumnChart
            title="Games decided on time, by the engine"
            note="Final position: winning or losing by 3+ pawns, otherwise level."
            categories={['Winning', 'Level', 'Losing']}
            series={[
              { name: 'Lost on time', values: keys.map((k) => lost[k] ?? 0) },
              { name: 'Won on time', values: keys.map((k) => won[k] ?? 0) },
            ]}
            format={count}
          />
        </div>
      )
    }
    case 'opening_autopilot': {
      const rows = (d.by_move ?? []) as Array<{ move: number; familiar: number | null; new: number | null }>
      return (
        <LineChart
          title="Time per move in known and new positions"
          note="Median share of the game time per move; known = reached 3+ times in earlier games."
          x={rows.map((r) => r.move)}
          xLabel="Move"
          series={[
            { name: 'Known position', values: rows.map((r) => r.familiar) },
            { name: 'New position', values: rows.map((r) => r.new) },
          ]}
          format={(v) => `${(v * 100).toFixed(1)}%`}
          yMin={0}
        />
      )
    }
    default:
      return null
  }
}
