// Typed clients for the two backend services. The browser calls both directly.

export const GAMES_API = (import.meta.env.VITE_GAMES_API_URL ?? 'http://localhost:8001').replace(/\/$/, '')
export const INSIGHTS_API = (import.meta.env.VITE_INSIGHTS_API_URL ?? 'http://localhost:8002').replace(
  /\/$/,
  '',
)

// Services scale to zero and the databases auto-pause: the first request after idle can take
// up to a minute or more. Wait long enough, and tell the user why it is slow.
const TIMEOUT_MS = 90_000
const SLOW_MS = 4_000
export const SLOW_EVENT = 'chess-habits:slow-requests'
let slowRequests = 0

function setSlow(delta: number) {
  slowRequests += delta
  window.dispatchEvent(new CustomEvent(SLOW_EVENT, { detail: slowRequests }))
}

/** "player": an account you track; "reference": a grandmaster to compare with. */
export type PlayerKind = 'player' | 'reference'

export interface Player {
  id: number
  platform: string
  username: string
  kind: PlayerKind
  display_name: string | null
  notes: string | null
  created_at: string
  updated_at: string
  last_imported_at: string | null
}

export interface PlayerDetail extends Player {
  game_counts: Record<string, number>
}

export interface ArchiveMonth {
  month: string
  imported: boolean
  complete: boolean
  game_count: number | null
}

export interface ImportResult {
  month: string
  fetched: number
  new_games: number
  skipped: boolean
  complete: boolean
}

export interface Game {
  id: number
  url: string | null
  time_class: string
  time_control: string
  ended_at: string
  player_color: string
  player_rating: number | null
  opponent_username: string
  opponent_rating: number | null
  result: 'win' | 'loss' | 'draw'
  result_detail: string
  eco: string | null
  opening: string | null
  ply_count: number
  termination?: string | null
  /** Only when listed with include_pgn. */
  pgn?: string
}

export interface GamePage {
  items: Game[]
  total: number
  limit: number
  offset: number
}

export type FindingLabel = 'finding' | 'exploratory' | 'no_effect' | 'not_enough_data' | 'profile'

export interface Finding {
  id: number
  analysis_key: string
  time_class: string
  kind: 'contrast' | 'profile'
  metric: 'score' | 'share' | 'profile'
  label: FindingLabel
  title: string
  summary: string
  effect: number | null
  ci_low: number | null
  ci_high: number | null
  mde: number | null
  p_value: number | null
  sample_size: number
  details: Record<string, unknown>
}

export interface Run {
  id: number
  player_id: number
  status: string
  games_analyzed: number
  created_at: string
  finished_at: string | null
  findings: Finding[]
}

export type CompareUnit = 'share' | 'points' | 'elo' | 'move'
export type CompareVerdict = 'different' | 'maybe_different' | 'similar' | 'not_enough_data' | 'descriptive'

export interface CompareSide {
  value: number
  ci_low: number | null
  ci_high: number | null
  n: number
}

export interface CompareRow {
  key: string
  name: string
  unit: CompareUnit
  better: 'lower' | 'higher' | null
  you: CompareSide | null
  reference: CompareSide | null
  difference: { value: number; ci_low: number; ci_high: number } | null
  q_value: number | null
  verdict: CompareVerdict
}

/** Your habits next to a grandmaster's, per time control (from both latest analysis runs). */
export interface Comparison {
  player_id: number
  reference_id: number
  player_run: Omit<Run, 'findings'>
  reference_run: Omit<Run, 'findings'>
  blocks: { time_class: string; rows: CompareRow[] }[]
}

export type RuleKind = 'clock_checkpoint' | 'stop_loss'

/** A rule the player adopted from a card; every analysis run checks whether it was kept. */
export interface Rule {
  id: number
  player_id: number
  time_class: string
  kind: RuleKind
  move: number | null
  min_share: number | null
  stop_rule: string | null
  note: string | null
  description: string
  adopted_at: string
  retired_at: string | null
  created_at: string
}

export interface RuleDraft {
  time_class: string
  kind: RuleKind
  move?: number
  min_share?: number
  stop_rule?: string
}

export class ApiError extends Error {
  readonly status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(base: string, path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  let isSlow = false
  const slowTimer = setTimeout(() => {
    isSlow = true
    setSlow(+1)
  }, SLOW_MS)
  let resp: Response
  try {
    resp = await fetch(`${base}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
      signal: controller.signal,
    })
  } catch {
    const service = base === GAMES_API ? 'games' : 'insights'
    throw new ApiError(0, `The ${service} service is not reachable right now. Please try again later.`)
  } finally {
    clearTimeout(timer)
    clearTimeout(slowTimer)
    if (isSlow) setSlow(-1)
  }
  if (resp.status === 204) return undefined as T
  const body = await resp.json().catch(() => null)
  if (!resp.ok) {
    const detail = body?.detail
    const message = typeof detail === 'string' ? detail : `Request failed (HTTP ${resp.status})`
    throw new ApiError(resp.status, message)
  }
  return body as T
}

export const gamesApi = {
  listPlayers: () => request<Player[]>(GAMES_API, '/players'),
  getPlayer: (id: number) => request<PlayerDetail>(GAMES_API, `/players/${id}`),
  createPlayer: (username: string, notes?: string, kind: PlayerKind = 'player') =>
    request<Player>(GAMES_API, '/players', {
      method: 'POST',
      body: JSON.stringify({ platform: 'chesscom', username, kind, notes: notes || null }),
    }),
  updatePlayer: (id: number, patch: { display_name?: string | null; notes?: string | null }) =>
    request<Player>(GAMES_API, `/players/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
  deletePlayer: (id: number) => request<void>(GAMES_API, `/players/${id}`, { method: 'DELETE' }),
  listArchives: (id: number) => request<ArchiveMonth[]>(GAMES_API, `/players/${id}/archives`),
  importMonth: (id: number, month: string) =>
    request<ImportResult>(GAMES_API, `/players/${id}/imports`, {
      method: 'POST',
      body: JSON.stringify({ month }),
    }),
  listGames: (
    id: number,
    params: { limit?: number; offset?: number; time_class?: string; include_pgn?: boolean } = {},
  ) => {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => v !== undefined && v !== '' && q.set(k, String(v)))
    return request<GamePage>(GAMES_API, `/players/${id}/games?${q}`)
  },
}

export const insightsApi = {
  latestFindings: (playerId: number) => request<Run>(INSIGHTS_API, `/players/${playerId}/findings`),
  // The browser's time zone, so the time-of-day card uses local hours.
  runAnalyses: (playerId: number) =>
    request<Run>(
      INSIGHTS_API,
      `/players/${playerId}/runs?utc_offset_minutes=${-new Date().getTimezoneOffset()}`,
      { method: 'POST' },
    ),
  listRules: (playerId: number) => request<Rule[]>(INSIGHTS_API, `/players/${playerId}/rules`),
  createRule: (playerId: number, draft: RuleDraft) =>
    request<Rule>(INSIGHTS_API, `/players/${playerId}/rules`, {
      method: 'POST',
      body: JSON.stringify(draft),
    }),
  compare: (playerId: number, referenceId: number) =>
    request<Comparison>(INSIGHTS_API, `/players/${playerId}/compare/${referenceId}`),
  retireRule: (ruleId: number) =>
    request<Rule>(INSIGHTS_API, `/rules/${ruleId}`, {
      method: 'PATCH',
      body: JSON.stringify({ retired: true }),
    }),
}

// ---- deep analysis (computed in the browser, stored by the insights service) ---------------

export interface EngineMove {
  k: number
  best: string
  type: string
  b: number
  s?: number
  p: number
  legal: number
  check?: boolean
  recapture?: boolean
  fen?: string
}

export interface GameAnalysisIn {
  game_id: number
  position_keys?: string[]
  engine?: string
  final_cp?: number
  moves?: EngineMove[]
}

export interface DeepStatus {
  positions: number
  engine: number
  engine_game_ids: number[]
  position_game_ids: number[]
  final_game_ids: number[]
}

export const deepApi = {
  status: (playerId: number) =>
    request<DeepStatus>(INSIGHTS_API, `/players/${playerId}/game-analyses/status`),
  save: (playerId: number, games: GameAnalysisIn[]) =>
    request<DeepStatus>(INSIGHTS_API, `/players/${playerId}/game-analyses`, {
      method: 'PUT',
      body: JSON.stringify({ games }),
    }),
}
