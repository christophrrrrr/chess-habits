export type Route = { page: 'players' } | { page: 'player'; id: number }

/** Minimal hash router: "#/" and "#/players/<id>". Works on any static host. */
export function parseRoute(hash: string): Route {
  const m = hash.match(/^#\/players\/(\d+)/)
  return m ? { page: 'player', id: Number(m[1]) } : { page: 'players' }
}
