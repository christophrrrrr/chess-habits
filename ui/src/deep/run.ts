// The deep analysis, run in the player's browser:
//   1. positions: every game is replayed and the position before each of the player's first 20
//      moves is hashed (fast; feeds the opening autopilot);
//   2. endings: Stockfish evaluates the final position of resigned, timed-out and agreed games;
//   3. engine: Stockfish (MultiPV 2) on every own position of the most recent games.
// Results are uploaded as they come, so stopping and starting again continues where it left off.
import { deepApi, gamesApi, type DeepStatus, type EngineMove, type Game, type GameAnalysisIn } from '../api'
import { Engine, type Line } from './engine'
import { isRecapture, moveType, replay, winPct, type Replay } from './replay'

export const ENGINE_ID = 'sf19-lite-100k'
export const NODES = 100_000
const AUTOPILOT_MOVES = 20
const POSITION_BATCH = 200
const CRITICAL_GAP = 10 // keep the FEN of positions whose 2nd-best move loses 10+ win% points

export type Phase = 'games' | 'positions' | 'endings' | 'engine' | 'done'

export interface Progress {
  phase: Phase
  done: number
  total: number
  /** Seconds left in this phase, once it can be estimated. */
  eta?: number
}

export interface EngineLike {
  init(): Promise<void>
  analyse(fen: string, nodes: number, multipv?: number, searchmoves?: string): Promise<Line[]>
  stop(): void
}

export interface Deps {
  listGames: typeof gamesApi.listGames
  status: typeof deepApi.status
  save: typeof deepApi.save
  engine: () => EngineLike
}

const defaultDeps: Deps = {
  listGames: gamesApi.listGames,
  status: deepApi.status,
  save: deepApi.save,
  engine: () => new Engine(),
}

const ENDING = /resignation|won on time|agreement/i

async function allGames(playerId: number, deps: Deps, onProgress: (p: Progress) => void) {
  const games: Game[] = []
  for (let offset = 0; ;) {
    const page = await deps.listGames(playerId, { limit: 500, offset, include_pgn: true })
    games.push(...page.items)
    offset += page.items.length
    onProgress({ phase: 'games', done: games.length, total: page.total })
    if (page.items.length === 0 || offset >= page.total) return games
  }
}

function safeReplay(g: Game): Replay | null {
  if (!g.pgn || (g.player_color !== 'white' && g.player_color !== 'black')) return null
  try {
    return replay(g.pgn, g.player_color)
  } catch {
    return null // a PGN chess.js cannot read (e.g. a variant): leave the game out
  }
}

/** Stockfish rows for one game's own positions. */
export async function analyseGame(r: Replay, engine: EngineLike, nodes = NODES): Promise<EngineMove[]> {
  const rows: EngineMove[] = []
  for (const pos of r.positions) {
    if (pos.legal < 2) continue // a forced move is not a decision
    const lines = await engine.analyse(pos.fen, nodes, 2)
    if (lines.length === 0) continue
    const [best, second] = lines
    let played = best.cp
    if (pos.played === best.move) played = best.cp
    else if (second && pos.played === second.move) played = second.cp
    else played = (await engine.analyse(pos.fen, nodes, 1, pos.played))[0]?.cp ?? best.cp
    const critical = second !== undefined && winPct(best.cp) - winPct(second.cp) >= CRITICAL_GAP
    rows.push({
      k: pos.k,
      best: best.move,
      type: moveType(pos.fen, best.move),
      b: best.cp,
      s: second?.cp,
      p: played,
      legal: pos.legal,
      check: pos.check,
      recapture: isRecapture(pos.fen, best.move, pos.lastTo),
      fen: critical ? pos.fen : undefined,
    })
  }
  return rows
}

/** Final position from the player's side, or a fixed value when the game ended on the board. */
export async function finalEval(r: Replay, engine: EngineLike, nodes = NODES): Promise<number> {
  const lines = await engine.analyse(r.finalFen, nodes, 1)
  if (lines.length === 0) return 0 // mate or stalemate on the board: no evaluation needed here
  return r.playerToMoveAtEnd ? lines[0].cp : -lines[0].cp
}

export async function runDeep(
  playerId: number,
  opts: { engineGames: number; nodes?: number },
  onProgress: (p: Progress) => void,
  cancelled: () => boolean,
  deps: Deps = defaultDeps,
): Promise<DeepStatus> {
  const nodes = opts.nodes ?? NODES
  let status = await deps.status(playerId)
  const games = await allGames(playerId, deps, onProgress)
  const replays = new Map<number, Replay | null>()
  const get = (g: Game) => {
    if (!replays.has(g.id)) replays.set(g.id, safeReplay(g))
    return replays.get(g.id)!
  }

  // 1. positions
  const havePos = new Set(status.position_game_ids)
  const todo = games.filter((g) => !havePos.has(g.id))
  let batch: GameAnalysisIn[] = []
  for (let i = 0; i < todo.length; i++) {
    if (cancelled()) return status
    const r = get(todo[i])
    if (r)
      batch.push({
        game_id: todo[i].id,
        position_keys: r.positions.slice(0, AUTOPILOT_MOVES).map((p) => p.key),
      })
    if (batch.length >= POSITION_BATCH || i === todo.length - 1) {
      if (batch.length) status = await deps.save(playerId, batch)
      batch = []
      onProgress({ phase: 'positions', done: i + 1, total: todo.length })
    }
  }

  const engine = deps.engine()
  try {
    await engine.init()
    const timed = async (
      phase: Phase,
      items: Game[],
      work: (g: Game, r: Replay) => Promise<GameAnalysisIn>,
    ) => {
      const started = performance.now()
      for (let i = 0; i < items.length; i++) {
        if (cancelled()) return
        const r = get(items[i])
        if (r) status = await deps.save(playerId, [await work(items[i], r)])
        const per = (performance.now() - started) / 1000 / (i + 1)
        onProgress({ phase, done: i + 1, total: items.length, eta: per * (items.length - i - 1) })
      }
    }

    // 2. endings
    const haveFinal = new Set(status.final_game_ids)
    const endings = games.filter((g) => ENDING.test(g.termination ?? '') && !haveFinal.has(g.id))
    await timed('endings', endings, async (g, r) => ({
      game_id: g.id,
      final_cp: await finalEval(r, engine, nodes),
    }))

    // 3. engine on the most recent games
    const haveEngine = new Set(status.engine_game_ids)
    const recent = [...games]
      .filter((g) => g.time_class !== 'daily')
      .sort((a, b) => b.ended_at.localeCompare(a.ended_at))
      .slice(0, opts.engineGames)
      .filter((g) => !haveEngine.has(g.id))
    await timed('engine', recent, async (g, r) => ({
      game_id: g.id,
      engine: ENGINE_ID,
      moves: await analyseGame(r, engine, nodes),
    }))
  } finally {
    engine.stop()
  }
  onProgress({ phase: 'done', done: 1, total: 1 })
  return status
}
