// Stockfish 19 lite (GPL-3.0, see public/engine/SOURCE.md) as a separate program in a Web Worker.
// We only exchange UCI text messages with it.

export interface Line {
  move: string
  /** Centipawns for the side to move; mates are +-(10000 - moves to mate). */
  cp: number
}

const MATE = 10000

/** Parses the score of a UCI "info" line, or null if it has none. */
export function parseInfo(line: string): { multipv: number; cp: number; move: string } | null {
  if (!line.startsWith('info') || !line.includes(' pv ')) return null
  const mpv = Number(/ multipv (\d+)/.exec(line)?.[1] ?? 1)
  const cp = / score cp (-?\d+)/.exec(line)
  const mate = / score mate (-?\d+)/.exec(line)
  const move = / pv (\S+)/.exec(line)?.[1]
  if (!move || (!cp && !mate)) return null
  let score: number
  if (cp) score = Number(cp[1])
  else {
    const n = Number(mate![1])
    score = n > 0 ? MATE - n : -MATE - n
  }
  return { multipv: mpv, cp: Math.max(-MATE, Math.min(MATE, score)), move }
}

export class Engine {
  private worker: Worker
  private listener: ((line: string) => void) | null = null

  constructor(url = `${import.meta.env.BASE_URL}engine/stockfish-19-lite-single.js`) {
    this.worker = new Worker(url)
    this.worker.onmessage = (e: MessageEvent<string>) => this.listener?.(String(e.data))
  }

  private until(command: string, done: (line: string) => boolean, onLine?: (line: string) => void) {
    return new Promise<void>((resolve) => {
      this.listener = (line) => {
        onLine?.(line)
        if (done(line)) {
          this.listener = null
          resolve()
        }
      }
      this.worker.postMessage(command)
    })
  }

  async init(): Promise<void> {
    await this.until('uci', (l) => l === 'uciok')
    this.worker.postMessage('setoption name Hash value 32')
    await this.until('isready', (l) => l === 'readyok')
  }

  /** The best `multipv` moves in a position, best first. */
  async analyse(fen: string, nodes: number, multipv = 2, searchmoves?: string): Promise<Line[]> {
    this.worker.postMessage(`setoption name MultiPV value ${multipv}`)
    this.worker.postMessage(`position fen ${fen}`)
    const lines = new Map<number, Line>()
    const go = `go nodes ${nodes}${searchmoves ? ` searchmoves ${searchmoves}` : ''}`
    await this.until(
      go,
      (l) => l.startsWith('bestmove'),
      (l) => {
        const info = parseInfo(l)
        if (info) lines.set(info.multipv, { move: info.move, cp: info.cp })
      },
    )
    return [...lines.entries()].sort((a, b) => a[0] - b[0]).map(([, line]) => line)
  }

  stop(): void {
    this.worker.terminate()
  }
}
