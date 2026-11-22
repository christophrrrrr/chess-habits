import { describe, expect, it } from 'vitest'
import type { Finding } from './api'
import { buildPlan } from './plan'
import { parseRoute, href } from './routes'
import { clockProfile, contrast } from './test/fixtures'

const base = { ...contrast, details: {} } as Finding

function f(over: Partial<Finding>): Finding {
  return { ...base, ...over } as Finding
}

describe('buildPlan', () => {
  it('ranks costs by Elo over an average game and keeps strengths apart', () => {
    const findings: Finding[] = [
      // Time trouble: -110 Elo in 19% of games -> about 21 Elo per game.
      f({ id: 1, analysis_key: 'time_trouble_score', effect: -0.158, label: 'finding' }),
      {
        ...clockProfile,
        id: 2,
        details: {
          ...clockProfile.details,
          entry: { rate: 0.19 },
          checkpoint: { move: 20, min_share: 0.3 },
        },
      } as Finding,
      // After a loss: -40 Elo in 30% of games -> 12 Elo per game.
      f({
        id: 3,
        analysis_key: 'after_loss_result',
        effect: -0.0576,
        label: 'exploratory',
        sample_size: 1000,
        details: { n_a: 300 },
      }),
      // Not significant: never in the plan.
      f({ id: 4, analysis_key: 'warm_up', effect: -0.2, label: 'no_effect' }),
      // A strength.
      f({ id: 5, analysis_key: 'warm_up', time_class: 'rapid', effect: 0.05, label: 'finding' }),
    ]
    const { items, strengths } = buildPlan(findings)
    expect(items.map((i) => i.analysisKey)).toEqual(['time_trouble_score', 'after_loss_result'])
    expect(items[0].costElo).toBeCloseTo(110, 0)
    expect(items[0].perGameElo).toBeCloseTo(110 * 0.19, 0)
    expect(items[0].draft).toEqual({
      time_class: 'bullet',
      kind: 'clock_checkpoint',
      move: 20,
      min_share: 0.3,
    })
    expect(items[0].action).toContain('Keep at least 30% of your clock after move 20')
    expect(items[1].evidence).toBe('exploratory')
    expect(strengths).toHaveLength(1)
    expect(strengths[0].timeClass).toBe('rapid')
  })

  it('turns a helpful stop-loss rule, a bad time window and a bad opening into items', () => {
    const { items } = buildPlan([
      f({
        id: 1,
        analysis_key: 'stop_loss_rules',
        kind: 'profile',
        label: 'profile',
        sample_size: 500,
        details: {
          rules: [
            {
              rule: 'two_in_a_row',
              name: 'Stop after 2 losses in a row',
              skipped_games: 100,
              difference_elo: -60,
              verdict: 'helps',
            },
            {
              rule: 'three_in_session',
              name: 'Stop after 3 losses in one session',
              skipped_games: 50,
              difference_elo: 10,
              verdict: 'no_difference',
            },
          ],
        },
      }),
      f({
        id: 2,
        analysis_key: 'time_of_day',
        kind: 'profile',
        label: 'profile',
        details: {
          windows: [
            { name: 'in the morning (6-12 h)', games: 200, verdict: 'worse', vs_rest_elo: -80 },
            { name: 'in the evening (18-24 h)', games: 600, verdict: 'no_difference', vs_rest_elo: 5 },
          ],
        },
      }),
      f({
        id: 3,
        analysis_key: 'opening_time',
        kind: 'profile',
        label: 'profile',
        sample_size: 400,
        details: {
          openings: [
            { opening: 'Caro-Kann Defense', games: 80, elo: -70, low: -120, high: -20, used: 0.2 },
            { opening: 'Italian Game', games: 120, elo: 10, low: -30, high: 50, used: 0.1 },
          ],
        },
      }),
    ])
    expect(items.map((i) => i.analysisKey).sort()).toEqual(['opening_time', 'stop_loss_rules', 'time_of_day'])
    const stop = items.find((i) => i.analysisKey === 'stop_loss_rules')!
    expect(stop.draft).toEqual({ time_class: 'bullet', kind: 'stop_loss', stop_rule: 'two_in_a_row' })
    expect(items.find((i) => i.analysisKey === 'time_of_day')!.action).toBe(
      'Avoid rated bullet games in the morning (6-12 h).',
    )
    expect(items.find((i) => i.analysisKey === 'opening_time')!.title).toContain('Caro-Kann Defense')
  })

  it('is empty without clear evidence', () => {
    expect(buildPlan([f({ label: 'no_effect' })])).toEqual({ items: [], strengths: [] })
  })
})

describe('plan route', () => {
  it('round-trips', () => {
    const route = { page: 'player', id: 3, view: 'plan' } as const
    expect(href(route)).toBe('#/players/3/plan')
    expect(parseRoute('#/players/3/plan')).toEqual(route)
  })
})
