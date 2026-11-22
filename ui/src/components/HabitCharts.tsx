// Charts for every finding except the clock profile (which has its own card).
import type { Finding } from '../api'
import { percent, shortOpening } from '../format'
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
    default:
      return null
  }
}
