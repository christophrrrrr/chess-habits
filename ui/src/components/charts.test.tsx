import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Finding } from '../api'
import { contrast } from '../test/fixtures'
import { ColumnChart, IntervalChart, LineChart } from './charts'
import { FindingCard } from './FindingCard'
import { PlanPage } from '../pages/PlanPage'

describe('charts', () => {
  it('draws a line chart with a legend, a hover tooltip and a table view', () => {
    const { container } = render(
      <LineChart
        title="Clock left"
        x={[10, 20, 30]}
        xLabel="Move"
        series={[
          { name: 'Wins', values: [0.8, 0.6, null] },
          { name: 'Losses', values: [0.7, 0.4, 0.2] },
        ]}
        format={(v) => `${Math.round(v * 100)}%`}
        yMin={0}
        yMax={1}
      />,
    )
    expect(screen.getByRole('img', { name: 'Clock left' })).toBeInTheDocument()
    expect(screen.getAllByText('Wins').length).toBeGreaterThan(0)
    expect(container.querySelectorAll('path.chart__line')).toHaveLength(2)
    const table = screen.getByRole('table')
    expect(within(table).getAllByRole('row')).toHaveLength(4)
    expect(table).toHaveTextContent('30–20%')

    const hit = container.querySelector('rect[fill="transparent"]')!
    hit.getBoundingClientRect = () => ({ left: 0, width: 576 }) as DOMRect
    fireEvent.pointerMove(hit, { clientX: 0 })
    expect(screen.getByRole('status')).toHaveTextContent('Move 10')
  })

  it('draws columns and intervals, and nothing without data', () => {
    const { container } = render(
      <>
        <ColumnChart
          title="Onset"
          categories={['1–5', '6–10']}
          series={[{ name: 'Games', values: [3, 0] }]}
          format={String}
        />
        <IntervalChart
          title="By game"
          rows={[
            { label: 'Game 1', value: -40, low: -70, high: -10, verdict: 'bad' },
            { label: 'Game 2', value: 5, low: -20, high: 30 },
          ]}
          format={String}
        />
        <LineChart
          title="Empty"
          x={[1]}
          xLabel="x"
          series={[{ name: 'a', values: [null] }]}
          format={String}
        />
      </>,
    )
    expect(container.querySelectorAll('.chart')).toHaveLength(2)
    expect(container.querySelector('.chart__dot--bad')).not.toBeNull()
    expect(screen.queryByText('Empty')).not.toBeInTheDocument()
  })
})

describe('habit cards with charts', () => {
  it('shows the time-of-day card with its windows', () => {
    const finding = {
      ...contrast,
      analysis_key: 'time_of_day',
      kind: 'profile',
      metric: 'profile',
      label: 'profile',
      title: 'Blitz: you play about 80 Elo below your level in the morning',
      summary: 'Games you start in the morning score -80 Elo.',
      details: {
        windows: [
          {
            window: 'morning',
            name: 'in the morning (6-12 h)',
            games: 200,
            elo: -60,
            low: -90,
            high: -30,
            verdict: 'worse',
          },
          {
            window: 'evening',
            name: 'in the evening (18-24 h)',
            games: 600,
            elo: 10,
            low: -5,
            high: 25,
            verdict: 'no_difference',
          },
        ],
        games_by_hour: Array.from({ length: 24 }, (_, h) => (h > 6 ? 30 : 0)),
      },
    } as unknown as Finding
    render(<FindingCard finding={finding} />)
    expect(screen.getByRole('img', { name: 'Your score by time of day' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'When you play' })).toBeInTheDocument()
  })

  it('adds the session chart under the after-loss result', () => {
    const finding = {
      ...contrast,
      analysis_key: 'after_loss_result',
      details: {
        charts: {
          by_session_game: [
            { game: 1, plus: false, elo: -20, low: -50, high: 10, games: 300 },
            { game: 8, plus: true, elo: 5, low: -30, high: 40, games: 90 },
          ],
        },
      },
    } as unknown as Finding
    render(<FindingCard finding={finding} />)
    expect(screen.getAllByText('Game 8+').length).toBeGreaterThan(0)
  })
})

describe('plan page', () => {
  it('lists the costly habit with its action and a rule to adopt', () => {
    const findings = [
      {
        ...contrast,
        id: 1,
        analysis_key: 'time_trouble_score',
        effect: -0.158,
        label: 'finding',
        details: {},
      },
      {
        ...contrast,
        id: 2,
        analysis_key: 'clock_profile',
        kind: 'profile',
        label: 'profile',
        details: { entry: { rate: 0.2 }, checkpoint: { move: 20, min_share: 0.3 } },
      },
      {
        ...contrast,
        id: 3,
        analysis_key: 'warm_up',
        time_class: 'rapid',
        effect: 0.05,
        label: 'finding',
        details: {},
      },
      { ...contrast, id: 4, analysis_key: 'after_loss_result', label: 'no_effect', details: {} },
    ] as unknown as Finding[]
    render(<PlanPage playerId={1} findings={findings} actions={{ rules: [], adopt: async () => {} }} />)
    expect(screen.getByRole('link', { name: /Time trouble costs you 110 Elo in bullet/ })).toBeInTheDocument()
    expect(screen.getByText(/Keep at least 30% of your clock after move 20/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Adopt this rule' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Keep doing' })).toBeInTheDocument()
    expect(screen.getByText(/1 other checks found no clear effect/)).toBeInTheDocument()
  })

  it('says so when nothing is clear', () => {
    render(<PlanPage playerId={1} findings={[]} actions={{ rules: [], adopt: async () => {} }} />)
    expect(screen.getByText(/No habit costs you points clearly yet/)).toBeInTheDocument()
  })
})
