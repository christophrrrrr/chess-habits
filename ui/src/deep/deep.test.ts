import { describe, expect, it, vi } from 'vitest'
import type { Game, GameAnalysisIn } from '../api'
import { parseInfo, type Line } from './engine'
import { isRecapture, moveType, positionKey, replay, winPct } from './replay'
import { analyseGame, finalEval, runDeep, type EngineLike } from './run'

// 1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Bxc6 dxc6, with chess.com clock comments.
const PGN = `[Event "Live Chess"]
[White "me"]
[Black "opp"]
[Result "0-1"]
[Termination "opp won by resignation"]

1. e4 {[%clk 0:03:00]} 1... e5 {[%clk 0:02:59]} 2. Nf3 {[%clk 0:02:58]} 2... Nc6 {[%clk 0:02:57]}
3. Bb5 {[%clk 0:02:56]} 3... a6 {[%clk 0:02:55]} 4. Bxc6 {[%clk 0:02:50]} 4... dxc6 {[%clk 0:02:49]} 0-1`

describe('replay', () => {
  it('lists own positions with the move played, legal moves and the last move', () => {
    const r = replay(PGN, 'white')
    expect(r.positions.map((p) => p.played)).toEqual(['e2e4', 'g1f3', 'f1b5', 'b5c6'])
    expect(r.positions[0].legal).toBe(20)
    expect(r.positions[1].lastTo).toBe('e5')
    expect(r.playerToMoveAtEnd).toBe(true)
    const black = replay(PGN, 'black')
    expect(black.positions.map((p) => p.played)).toEqual(['e7e5', 'b8c6', 'a7a6', 'd7c6'])
    expect(black.playerToMoveAtEnd).toBe(false)
  })

  it('hashes positions without the move counters', () => {
    const a = positionKey('rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1')
    const b = positionKey('rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 5 9')
    expect(a).toMatch(/^[0-9a-f]{8}$/)
    expect(a).toBe(b)
  })

  it('classifies moves and recaptures', () => {
    const r = replay(PGN, 'black')
    const last = r.positions[3] // after 4.Bxc6, black recaptures
    expect(moveType(last.fen, 'd7c6')).toBe('capture')
    expect(isRecapture(last.fen, 'd7c6', last.lastTo)).toBe(true)
    expect(isRecapture(last.fen, 'a6a5', last.lastTo)).toBe(false)
    const start = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    expect(moveType(start, 'e2e4')).toBe('pawn')
    expect(moveType(start, 'g1f3')).toBe('quiet')
    expect(moveType('4k3/8/8/8/8/5N2/8/4K3 w - - 0 1', 'f3g1')).toBe('retreat')
    expect(moveType('4k3/8/8/8/8/8/8/4K2R w K - 0 1', 'e1g1')).toBe('castle')
    expect(moveType('4k3/8/8/8/8/8/8/R3K3 w - - 0 1', 'a1a8')).toBe('check')
    expect(moveType('4k3/8/8/8/8/8/8/4K3 w - - 0 1', 'e1d2')).toBe('king')
  })

  it('uses the Lichess win% curve', () => {
    expect(winPct(0)).toBe(50)
    expect(winPct(400)).toBeGreaterThan(80)
  })
})

describe('UCI', () => {
  it('parses centipawn and mate scores', () => {
    expect(parseInfo('info depth 12 multipv 2 score cp -35 nodes 1 pv e7e5 g1f3')).toEqual({
      multipv: 2,
      cp: -35,
      move: 'e7e5',
    })
    expect(parseInfo('info depth 9 score mate 3 pv d1h5')?.cp).toBe(9997)
    expect(parseInfo('info depth 9 score mate -2 pv e8f7')?.cp).toBe(-9998)
    expect(parseInfo('info string NNUE loaded')).toBeNull()
  })
})

/** A fake engine: the best move is always the played one unless told otherwise. */
function fakeEngine(lines: (fen: string, searchmoves?: string) => Line[]): EngineLike {
  return {
    init: vi.fn(async () => {}),
    analyse: vi.fn(async (fen: string, _n: number, _m?: number, s?: string) => lines(fen, s)),
    stop: vi.fn(),
  }
}

describe('engine pass', () => {
  it('records best, second and played evaluations, and keeps the FEN of critical positions', async () => {
    const r = replay(PGN, 'white')
    const engine = fakeEngine((_fen, s) =>
      s
        ? [{ move: s, cp: -150 }]
        : [
            { move: 'a2a3', cp: 50 },
            { move: 'h2h3', cp: -200 },
          ],
    )
    const rows = await analyseGame(r, engine, 1000)
    expect(rows).toHaveLength(4)
    expect(rows[0]).toMatchObject({ k: 1, best: 'a2a3', b: 50, s: -200, p: -150, type: 'pawn' })
    expect(rows[0].fen).toBeDefined() // gap ~ 23 win% points
    expect(
      await finalEval(
        r,
        fakeEngine(() => [{ move: 'a2a3', cp: 120 }]),
      ),
    ).toBe(120)
    expect(
      await finalEval(
        replay(PGN, 'black'),
        fakeEngine(() => [{ move: 'a2a3', cp: 120 }]),
      ),
    ).toBe(-120)
  })

  it('runs all three passes, skips what is done and uploads as it goes', async () => {
    const game = (id: number, ended: string): Game =>
      ({
        id,
        pgn: PGN,
        player_color: 'white',
        time_class: 'blitz',
        ended_at: ended,
        termination: 'opp won by resignation',
      }) as Game
    const games = [game(1, '2026-01-01'), game(2, '2026-02-01'), game(3, '2026-03-01')]
    const saved: number[][] = []
    const status = {
      positions: 1,
      engine: 1,
      position_game_ids: [1],
      engine_game_ids: [3],
      final_game_ids: [1],
    }
    const progress: string[] = []
    await runDeep(
      7,
      { engineGames: 2, nodes: 10 },
      (p) => progress.push(p.phase),
      () => false,
      {
        listGames: vi.fn(async () => ({ items: games, total: 3, limit: 500, offset: 0 })),
        status: vi.fn(async () => status),
        save: vi.fn(async (_id: number, batch: GameAnalysisIn[]) => {
          saved.push(batch.map((b) => b.game_id))
          return status
        }),
        engine: () => fakeEngine(() => [{ move: 'a2a3', cp: 0 }]),
      },
    )
    expect(saved[0]).toEqual([2, 3]) // positions for the two new games, one batch
    expect(saved.slice(1, 3)).toEqual([[2], [3]]) // final evals for games 2 and 3
    expect(saved.slice(3)).toEqual([[2]]) // engine: the 2 most recent are 3 (done) and 2
    expect(progress).toContain('done')
  })
})
