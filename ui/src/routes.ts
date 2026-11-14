export type PlayerView =
  | { view: 'overview'; tc?: string }
  | { view: 'finding'; tc: string; key: string }
  | { view: 'rule'; ruleId: number }
  | { view: 'games' }
  | { view: 'compare'; refId?: number }

export type Route = { page: 'players' } | ({ page: 'player'; id: number } & PlayerView)

/**
 * Minimal hash router, works on any static host:
 *   #/                                  accounts
 *   #/players/1                         a player's overview (tiles)
 *   #/players/1/rapid                   overview for one time control
 *   #/players/1/rapid/clock_profile     one finding in full
 *   #/players/1/rules/11                one adopted rule
 *   #/players/1/games                   recent games
 *   #/players/1/compare                 pick a grandmaster to compare with
 *   #/players/1/compare/7               you next to player 7 (a grandmaster)
 */
export function parseRoute(hash: string): Route {
  const m = hash.match(/^#\/players\/(\d+)(?:\/([a-z_]+)(?:\/([a-z0-9_]+))?)?\/?$/)
  if (!m) return { page: 'players' }
  const id = Number(m[1])
  const [, , a, b] = m
  if (a === 'games' && !b) return { page: 'player', id, view: 'games' }
  if (a === 'compare' && !b) return { page: 'player', id, view: 'compare' }
  if (a === 'compare' && /^\d+$/.test(b)) return { page: 'player', id, view: 'compare', refId: Number(b) }
  if (a === 'rules' && b && /^\d+$/.test(b)) return { page: 'player', id, view: 'rule', ruleId: Number(b) }
  if (a && b) return { page: 'player', id, view: 'finding', tc: a, key: b }
  return { page: 'player', id, view: 'overview', tc: a }
}

export function href(route: Route): string {
  if (route.page === 'players') return '#/'
  const base = `#/players/${route.id}`
  switch (route.view) {
    case 'overview':
      return route.tc ? `${base}/${route.tc}` : base
    case 'finding':
      return `${base}/${route.tc}/${route.key}`
    case 'rule':
      return `${base}/rules/${route.ruleId}`
    case 'games':
      return `${base}/games`
    case 'compare':
      return route.refId ? `${base}/compare/${route.refId}` : `${base}/compare`
  }
}
