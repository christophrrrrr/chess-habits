// Gaze estimation maths, pure and unit tested. The webcam part lives in tracker.ts.
//
// Webcam eye tracking is coarse: 2-7 degrees in home use, about 1-3 squares on a laptop board
// (docs/research/gaze-tracking.md). So everything here works with coarse board regions, never
// single squares, and the page says so.

export interface Point {
  x: number
  y: number
}

/** MediaPipe Face Landmarker indices (478-point mesh with irises). */
const L = { outer: 263, inner: 362, top: 386, bottom: 374, iris: 473 }
const R = { outer: 33, inner: 133, top: 159, bottom: 145, iris: 468 }
const NOSE = 1

function eye(lm: Point[], e: typeof L): [number, number] {
  const a = lm[e.outer]
  const b = lm[e.inner]
  const i = lm[e.iris]
  const dx = b.x - a.x
  const dy = b.y - a.y
  const len2 = dx * dx + dy * dy || 1e-9
  // Iris position along the eye (0 = outer corner, 1 = inner) and between the lids.
  const h = ((i.x - a.x) * dx + (i.y - a.y) * dy) / len2
  const lid = lm[e.bottom].y - lm[e.top].y || 1e-9
  const v = (i.y - lm[e.top].y) / lid
  return [h, v]
}

/** Features of one video frame: iris position in each eye plus rough head pose. */
export function features(lm: Point[]): number[] {
  const [lh, lv] = eye(lm, L)
  const [rh, rv] = eye(lm, R)
  const left = lm[L.outer]
  const right = lm[R.outer]
  const scale = Math.hypot(left.x - right.x, left.y - right.y) || 1e-9
  const mid = { x: (left.x + right.x) / 2, y: (left.y + right.y) / 2 }
  const nose = lm[NOSE]
  const yaw = (nose.x - mid.x) / scale
  const pitch = (nose.y - mid.y) / scale
  const h = (lh + (1 - rh)) / 2 // both eyes on one scale (the right eye's corners are mirrored)
  const v = (lv + rv) / 2
  return [h, v, lh, rh, lv, rv, yaw, pitch, nose.x, nose.y, scale, h * h, v * v, h * v]
}

export interface Ridge {
  mean: number[]
  std: number[]
  wx: number[]
  wy: number[]
}

function solve(a: number[][], b: number[]): number[] {
  // Gaussian elimination with partial pivoting (the systems are ~15 x 15).
  const n = b.length
  const m = a.map((row, i) => [...row, b[i]])
  for (let c = 0; c < n; c++) {
    let p = c
    for (let r = c + 1; r < n; r++) if (Math.abs(m[r][c]) > Math.abs(m[p][c])) p = r
    ;[m[c], m[p]] = [m[p], m[c]]
    const d = m[c][c] || 1e-12
    for (let r = 0; r < n; r++) {
      if (r === c) continue
      const f = m[r][c] / d
      for (let k = c; k <= n; k++) m[r][k] -= f * m[c][k]
    }
  }
  return m.map((row, i) => row[n] / (row[i] || 1e-12))
}

/** Ridge regression from features to screen x and y (standardised features, intercept). */
export function fitRidge(xs: number[][], targets: Point[], lambda = 1): Ridge {
  const k = xs[0].length
  const mean = Array.from({ length: k }, (_, j) => xs.reduce((s, x) => s + x[j], 0) / xs.length)
  const std = Array.from({ length: k }, (_, j) => {
    const v = xs.reduce((s, x) => s + (x[j] - mean[j]) ** 2, 0) / xs.length
    return Math.sqrt(v) || 1
  })
  const z = xs.map((x) => [1, ...x.map((v, j) => (v - mean[j]) / std[j])])
  const p = k + 1
  const xtx = Array.from({ length: p }, (_, i) =>
    Array.from(
      { length: p },
      (_, j) => z.reduce((s, r) => s + r[i] * r[j], 0) + (i === j && i > 0 ? lambda : 0),
    ),
  )
  const xty = (ys: number[]) =>
    Array.from({ length: p }, (_, i) => z.reduce((s, r, n) => s + r[i] * ys[n], 0))
  return {
    mean,
    std,
    wx: solve(xtx, xty(targets.map((t) => t.x))),
    wy: solve(xtx, xty(targets.map((t) => t.y))),
  }
}

export function predict(model: Ridge, x: number[]): Point {
  const z = [1, ...x.map((v, j) => (v - model.mean[j]) / model.std[j])]
  return {
    x: z.reduce((s, v, i) => s + v * model.wx[i], 0),
    y: z.reduce((s, v, i) => s + v * model.wy[i], 0),
  }
}

/** Exponential smoothing for a jittery gaze point. */
export function smooth(prev: Point | null, next: Point, alpha = 0.3): Point {
  if (!prev) return next
  return { x: prev.x + alpha * (next.x - prev.x), y: prev.y + alpha * (next.y - prev.y) }
}

// ---- the board ---------------------------------------------------------------------------

export interface Rect {
  left: number
  top: number
  width: number
  height: number
}

/** Square under a screen point, as [file 0-7 (a-h), rank 0-7 (1-8)] with White at the bottom. */
export function squareAt(p: Point, board: Rect, flip = false): [number, number] | null {
  const fx = (p.x - board.left) / board.width
  const fy = (p.y - board.top) / board.height
  if (fx < 0 || fx >= 1 || fy < 0 || fy >= 1) return null
  const file = Math.floor(fx * 8)
  const rank = 7 - Math.floor(fy * 8)
  return flip ? [7 - file, 7 - rank] : [file, rank]
}

/** The coarse region (4 x 4 blocks of 2 x 2 squares) for a square. */
export function regionOf([file, rank]: [number, number]): number {
  return Math.floor(rank / 2) * 4 + Math.floor(file / 2)
}

/** "e4" style name of a region's lower-left square to its upper-right one, e.g. "e3-f4". */
export function regionName(r: number): string {
  const f = (r % 4) * 2
  const k = Math.floor(r / 4) * 2
  const files = 'abcdefgh'
  return `${files[f]}${k + 1}-${files[f + 1]}${k + 2}`
}

export interface GazeSummary {
  samples: number
  onBoard: number
  /** Share of on-board samples per region (16 values). */
  regions: number[]
  /** Share of on-board samples on the opponent's half (ranks 5-8, White to move). */
  opponentHalf: number
  /** Share near each king (the king's square and its neighbours). */
  ownKing: number
  enemyKing: number
  /** First region where the gaze stayed for 3 samples in a row. */
  firstRegion: number | null
  /** Share of on-board samples within one square of the key move's from or to square. */
  keySquares: number | null
}

function squareOf(name: string): [number, number] {
  return ['abcdefgh'.indexOf(name[0]), Number(name[1]) - 1]
}

/** Summarises gaze samples over a board; kings as [file, rank], own = side to move. */
export function summarise(
  points: Point[],
  board: Rect,
  kings: { own: [number, number] | null; enemy: [number, number] | null },
  opts: { flip?: boolean; side?: 'w' | 'b'; keyMove?: string } = {},
): GazeSummary {
  const key = opts.keyMove ? [squareOf(opts.keyMove.slice(0, 2)), squareOf(opts.keyMove.slice(2, 4))] : null
  let onKey = 0
  const counts = new Array(16).fill(0)
  let onBoard = 0
  let opp = 0
  let ownK = 0
  let enemyK = 0
  let firstRegion: number | null = null
  let run: { region: number; n: number } | null = null
  const near = (sq: [number, number], k: [number, number] | null) =>
    k !== null && Math.abs(sq[0] - k[0]) <= 1 && Math.abs(sq[1] - k[1]) <= 1
  for (const p of points) {
    const sq = squareAt(p, board, opts.flip)
    if (!sq) {
      run = null
      continue
    }
    onBoard++
    const r = regionOf(sq)
    counts[r]++
    if (opts.side === 'b' ? sq[1] <= 3 : sq[1] >= 4) opp++
    if (key && key.some((k) => near(sq, k))) onKey++
    if (near(sq, kings.own)) ownK++
    if (near(sq, kings.enemy)) enemyK++
    if (firstRegion === null) {
      run = run && run.region === r ? { region: r, n: run.n + 1 } : { region: r, n: 1 }
      if (run.n >= 3) firstRegion = r
    }
  }
  const share = (x: number) => (onBoard ? x / onBoard : 0)
  return {
    samples: points.length,
    onBoard,
    regions: counts.map(share),
    opponentHalf: share(opp),
    ownKing: share(ownK),
    enemyKing: share(enemyK),
    firstRegion,
    keySquares: key ? share(onKey) : null,
  }
}

// ---- positions -----------------------------------------------------------------------------

export interface Puzzle {
  id: string
  fen: string
  /** Solution as from-to squares, e.g. "h5f7". */
  move: string
  hint: string
}

export const PUZZLES: Puzzle[] = [
  {
    id: 'scholar',
    fen: 'r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
    move: 'h5f7',
    hint: 'White to move and mate in one.',
  },
  {
    id: 'back-rank',
    fen: '6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1',
    move: 'd1d8',
    hint: 'White to move and mate in one.',
  },
  {
    id: 'fork',
    fen: 'r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1',
    move: 'b5c7',
    hint: 'White to move and win material.',
  },
]

const GLYPH: Record<string, string> = {
  K: '♔',
  Q: '♕',
  R: '♖',
  B: '♗',
  N: '♘',
  P: '♙',
  k: '♚',
  q: '♛',
  r: '♜',
  b: '♝',
  n: '♞',
  p: '♟',
}

/** Pieces from a FEN, rank 8 first (row 0) as the board is drawn: 64 glyphs or ''. */
export function boardFromFen(fen: string): string[] {
  const out: string[] = []
  for (const row of fen.split(' ')[0].split('/')) {
    for (const ch of row) {
      if (/\d/.test(ch)) out.push(...Array(Number(ch)).fill(''))
      else out.push(GLYPH[ch] ?? '')
    }
  }
  return out
}

/** King squares as [file, rank] (rank 0 = rank 1). */
export function kingsFromFen(fen: string): {
  white: [number, number] | null
  black: [number, number] | null
} {
  const board = fen.split(' ')[0].split('/')
  let white: [number, number] | null = null
  let black: [number, number] | null = null
  board.forEach((row, i) => {
    let file = 0
    for (const ch of row) {
      if (/\d/.test(ch)) file += Number(ch)
      else {
        if (ch === 'K') white = [file, 7 - i]
        if (ch === 'k') black = [file, 7 - i]
        file++
      }
    }
  })
  return { white, black }
}

export function squareName([file, rank]: [number, number]): string {
  return `${'abcdefgh'[file]}${rank + 1}`
}

/** Puzzles from a player's own missed critical moments (critical_moments card), if any. */
export function ownPuzzles(
  findings: Array<{ analysis_key: string; time_class: string; details: Record<string, unknown> }>,
): Puzzle[] {
  const out: Puzzle[] = []
  for (const f of findings) {
    if (f.analysis_key !== 'critical_moments') continue
    for (const m of (f.details.missed ?? []) as Array<{ fen: string; best: string; k: number }>) {
      const side = m.fen.split(' ')[1] === 'b' ? 'Black' : 'White'
      out.push({
        id: `${f.time_class}-${m.k}-${m.fen}`,
        fen: m.fen,
        move: m.best,
        hint: `From your ${f.time_class} games: ${side} to move. You missed the best move here.`,
      })
    }
  }
  return out.slice(0, 5)
}
