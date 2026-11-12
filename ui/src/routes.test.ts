import { describe, expect, it } from 'vitest'
import { href, parseRoute, type Route } from './routes'

describe('routes', () => {
  it('parses every page', () => {
    expect(parseRoute('#/')).toEqual({ page: 'players' })
    expect(parseRoute('')).toEqual({ page: 'players' })
    expect(parseRoute('#/players/12')).toEqual({ page: 'player', id: 12, view: 'overview' })
    expect(parseRoute('#/players/12/rapid')).toEqual({
      page: 'player',
      id: 12,
      view: 'overview',
      tc: 'rapid',
    })
    expect(parseRoute('#/players/12/rapid/clock_profile')).toEqual({
      page: 'player',
      id: 12,
      view: 'finding',
      tc: 'rapid',
      key: 'clock_profile',
    })
    expect(parseRoute('#/players/12/rules/3')).toEqual({ page: 'player', id: 12, view: 'rule', ruleId: 3 })
    expect(parseRoute('#/players/12/games')).toEqual({ page: 'player', id: 12, view: 'games' })
    expect(parseRoute('#/players/x')).toEqual({ page: 'players' })
  })

  it('builds links that parse back to the same route', () => {
    const routes: Route[] = [
      { page: 'players' },
      { page: 'player', id: 1, view: 'overview' },
      { page: 'player', id: 1, view: 'overview', tc: 'blitz' },
      { page: 'player', id: 1, view: 'finding', tc: 'blitz', key: 'after_loss_result' },
      { page: 'player', id: 1, view: 'rule', ruleId: 9 },
      { page: 'player', id: 1, view: 'games' },
    ]
    for (const r of routes) expect(parseRoute(href(r))).toEqual(r)
  })
})
