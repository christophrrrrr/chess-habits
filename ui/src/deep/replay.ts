// Replays a game's PGN and lists the player's own positions, for the deep analysis.
// chess.js (BSD-2-Clause) does the chess rules. Pure and unit tested.
import { Chess, type Move } from 'chess.js'

export type MoveType = 'capture' | 'check' | 'quiet' | 'retreat' | 'pawn' | 'king' | 'castle'

export interface OwnPosition {
  /** Own move number, 1 = the player's first move. */
  k: number
  fen: string
  key: string
  /** The move the player made, UCI. */
  played: string
  legal: number
  check: boolean
  /** Square the opponent's last move went to (for spotting recaptures). */
  lastTo: string | null
}

export interface Replay {
  positions: OwnPosition[]
  finalFen: string
  /** Side to move in the final position is the player. */
  playerToMoveAtEnd: boolean
}

/** FNV-1a over pieces, side to move, castling and en passant: 8 lowercase hex characters. */
export function positionKey(fen: string): string {
  const s = fen.split(' ').slice(0, 4).join(' ')
  let h = 0x811c9dc5
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 0x01000193)
  }
  return (h >>> 0).toString(16).padStart(8, '0')
}

const uci = (m: Pick<Move, 'from' | 'to' | 'promotion'>) => `${m.from}${m.to}${m.promotion ?? ''}`

export function replay(pgn: string, color: 'white' | 'black'): Replay {
  const game = new Chess()
  game.loadPgn(pgn)
  const history = game.history({ verbose: true })
  const board = new Chess()
  const mine = color === 'white' ? 'w' : 'b'
  const positions: OwnPosition[] = []
  let lastTo: string | null = null
  for (const m of history) {
    if (board.turn() === mine) {
      positions.push({
        k: positions.length + 1,
        fen: board.fen(),
        key: positionKey(board.fen()),
        played: uci(m),
        legal: board.moves().length,
        check: board.inCheck(),
        lastTo,
      })
    }
    board.move(m.san)
    lastTo = m.to
  }
  return { positions, finalFen: board.fen(), playerToMoveAtEnd: board.turn() === mine }
}

/** What kind of move a UCI move is in a position (the research's move-type breakdown). */
export function moveType(fen: string, move: string): MoveType {
  const board = new Chess(fen)
  const m = board.move({ from: move.slice(0, 2), to: move.slice(2, 4), promotion: move[4] || undefined })
  if (m.san.includes('+') || m.san.includes('#')) return 'check'
  if (m.captured) return 'capture'
  if (m.flags.includes('k') || m.flags.includes('q')) return 'castle'
  if (m.piece === 'k') return 'king'
  if (m.piece === 'p') return 'pawn'
  const fromRank = Number(m.from[1])
  const toRank = Number(m.to[1])
  const back = m.color === 'w' ? toRank < fromRank : toRank > fromRank
  return back ? 'retreat' : 'quiet'
}

/** The best move recaptures on the square the opponent's last move went to. */
export function isRecapture(fen: string, move: string, lastTo: string | null): boolean {
  if (!lastTo || move.slice(2, 4) !== lastTo) return false
  const board = new Chess(fen)
  return board.get(lastTo as Parameters<Chess['get']>[0]) !== undefined
}

/** Lichess win% for the side to move (0-100). */
export function winPct(cp: number): number {
  return 50 + 50 * (2 / (1 + Math.exp(-0.00368208 * cp)) - 1)
}
