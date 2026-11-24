// "Where you look": an opt-in prototype of webcam eye tracking while solving positions.
// Steps: consent -> camera -> 9-point calibration -> 4-point accuracy check -> 3 positions ->
// where your eyes went. Everything runs in the browser; nothing is stored or sent.
import { ArrowLeft, ScanEye } from 'lucide-react'
import { useEffect, useRef, useState, type RefObject } from 'react'
import {
  boardFromFen,
  features,
  fitRidge,
  kingsFromFen,
  predict,
  PUZZLES,
  regionName,
  smooth,
  squareName,
  summarise,
  type GazeSummary,
  type Point,
  type Ridge,
} from '../gaze/model'
import { startTracker, type Tracker } from '../gaze/tracker'

type Step = 'intro' | 'loading' | 'calibrate' | 'check' | 'solve' | 'results' | 'error'

// Calibration targets as fractions of the viewport.
const CALIBRATION: Point[] = [0.1, 0.5, 0.9].flatMap((y) => [0.1, 0.5, 0.9].map((x) => ({ x, y })))
const CHECK: Point[] = [
  { x: 0.3, y: 0.3 },
  { x: 0.7, y: 0.3 },
  { x: 0.3, y: 0.7 },
  { x: 0.7, y: 0.7 },
]
const CLICKS_PER_TARGET = 5
const MIN_FRAMES = 30

interface Result {
  puzzle: (typeof PUZZLES)[number]
  summary: GazeSummary
  seconds: number
  solved: boolean
}

export function GazePage() {
  const [step, setStep] = useState<Step>('intro')
  const [error, setError] = useState<string | null>(null)
  const [target, setTarget] = useState(0)
  const [clicks, setClicks] = useState(0)
  const [errorPx, setErrorPx] = useState<number | null>(null)
  const [puzzle, setPuzzle] = useState(0)
  const [picked, setPicked] = useState<string | null>(null)
  const [results, setResults] = useState<Result[]>([])
  const [gaze, setGaze] = useState<Point | null>(null)
  const [face, setFace] = useState(false)

  const tracker = useRef<Tracker | null>(null)
  const latest = useRef<number[] | null>(null)
  const samples = useRef<{ x: number[]; t: Point }[]>([])
  const model = useRef<Ridge | null>(null)
  const checkErr = useRef<number[]>([])
  const smoothed = useRef<Point | null>(null)
  const trace = useRef<Point[]>([])
  const started = useRef(0)
  const board = useRef<HTMLDivElement | null>(null)

  useEffect(() => () => tracker.current?.stop(), [])

  async function start() {
    setStep('loading')
    try {
      tracker.current = await startTracker((lm) => {
        setFace(lm !== null)
        if (!lm) return
        const x = features(lm)
        latest.current = x
        if (model.current) {
          const p = smooth(smoothed.current, predict(model.current, x))
          smoothed.current = p
          setGaze(p)
          trace.current.push(p)
        }
      })
      setStep('calibrate')
    } catch (e) {
      setError(
        (e as Error).name === 'NotAllowedError'
          ? 'Camera access was blocked. Allow the camera for this site and try again.'
          : `The eye tracker could not start: ${(e as Error).message}`,
      )
      setStep('error')
    }
  }

  function targetPx(p: Point): Point {
    return { x: p.x * window.innerWidth, y: p.y * window.innerHeight }
  }

  function clickCalibration() {
    if (!latest.current) return
    samples.current.push({ x: latest.current, t: targetPx(CALIBRATION[target]) })
    if (clicks + 1 < CLICKS_PER_TARGET) return setClicks(clicks + 1)
    setClicks(0)
    if (target + 1 < CALIBRATION.length) return setTarget(target + 1)
    if (samples.current.length < MIN_FRAMES) return
    model.current = fitRidge(
      samples.current.map((s) => s.x),
      samples.current.map((s) => s.t),
    )
    setTarget(0)
    setStep('check')
  }

  function clickCheck() {
    const p = smoothed.current
    if (p) {
      const t = targetPx(CHECK[target])
      checkErr.current.push(Math.hypot(p.x - t.x, p.y - t.y))
    }
    if (target + 1 < CHECK.length) return setTarget(target + 1)
    const errs = checkErr.current
    setErrorPx(errs.length ? errs.reduce((a, b) => a + b, 0) / errs.length : null)
    beginPuzzle(0)
  }

  function beginPuzzle(i: number) {
    setPuzzle(i)
    setPicked(null)
    trace.current = []
    started.current = performance.now()
    setStep('solve')
  }

  function clickSquare(sq: string) {
    if (!picked) return setPicked(sq)
    const p = PUZZLES[puzzle]
    const rect = board.current!.getBoundingClientRect()
    const kings = kingsFromFen(p.fen)
    const summary = summarise(trace.current, rect, { own: kings.white, enemy: kings.black })
    const next = [
      ...results,
      {
        puzzle: p,
        summary,
        seconds: (performance.now() - started.current) / 1000,
        solved: picked + sq === p.move,
      },
    ]
    setResults(next)
    if (puzzle + 1 < PUZZLES.length) beginPuzzle(puzzle + 1)
    else {
      tracker.current?.stop()
      tracker.current = null
      setStep('results')
    }
  }

  const [squareSize, setSquareSize] = useState<number | null>(null)
  useEffect(() => {
    if (step === 'solve' && board.current) setSquareSize(board.current.getBoundingClientRect().width / 8)
  }, [step, puzzle])

  return (
    <div className="stack">
      <a href="#/" className="back">
        <ArrowLeft size={16} aria-hidden="true" /> All accounts
      </a>
      <header className="detail-head">
        <span className="habit__icon habit__icon--big">
          <ScanEye size={24} aria-hidden="true" />
        </span>
        <h2>Where you look</h2>
        <span className="badge badge--exploratory">Prototype</span>
      </header>

      {step === 'intro' && (
        <section className="panel stack">
          <p>
            Solve three positions while your webcam follows your eyes, then see where your attention went: the
            opponent’s half, the kings, and where you looked first.
          </p>
          <ul className="muted">
            <li>
              Everything runs in this browser tab. The video is never recorded, stored or sent anywhere.
            </li>
            <li>
              Webcam eye tracking is coarse (about 1–3 squares), so results are shown per 2×2 block of
              squares, never per square.
            </li>
            <li>
              This is a research prototype. It is not linked to your game statistics and makes no claims.
            </li>
            <li>Sit still, face the screen, with your face well lit. Calibration takes about a minute.</li>
          </ul>
          <button className="big-button" onClick={start}>
            Allow the camera and start
          </button>
        </section>
      )}

      {step === 'loading' && <p className="muted">Loading the eye tracker…</p>}
      {step === 'error' && <p className="error">{error}</p>}

      {(step === 'calibrate' || step === 'check') && (
        <div className="gaze-overlay" role="dialog" aria-label="Calibration">
          <p className="gaze-overlay__text">
            {step === 'calibrate'
              ? `Look at the dot and click it ${CLICKS_PER_TARGET} times (${target + 1} of ${CALIBRATION.length}).`
              : `Accuracy check: look at the dot and click it once (${target + 1} of ${CHECK.length}).`}
            {!face && ' No face found: move into the camera’s view.'}
          </p>
          <button
            className="gaze-dot"
            aria-label="Calibration point"
            style={{
              left: `${(step === 'calibrate' ? CALIBRATION : CHECK)[target].x * 100}%`,
              top: `${(step === 'calibrate' ? CALIBRATION : CHECK)[target].y * 100}%`,
              opacity: step === 'calibrate' ? 0.4 + (0.6 * (clicks + 1)) / CLICKS_PER_TARGET : 1,
            }}
            onClick={step === 'calibrate' ? clickCalibration : clickCheck}
          />
          {step === 'check' && gaze && (
            <span className="gaze-cursor" style={{ left: gaze.x, top: gaze.y }} aria-hidden="true" />
          )}
        </div>
      )}

      {step === 'solve' && (
        <section className="stack">
          <p>
            <strong>
              Position {puzzle + 1} of {PUZZLES.length}:
            </strong>{' '}
            {PUZZLES[puzzle].hint} Click the piece, then the square.
            {errorPx !== null && squareSize && (
              <span className="muted small">
                {' '}
                · tracking accuracy about {(errorPx / squareSize).toFixed(1)} squares
              </span>
            )}
          </p>
          <Board fen={PUZZLES[puzzle].fen} boardRef={board} picked={picked} onSquare={clickSquare} />
        </section>
      )}

      {step === 'results' && <Results results={results} errorPx={errorPx} />}
    </div>
  )
}

function Board({
  fen,
  boardRef,
  picked,
  onSquare,
  heat,
}: {
  fen: string
  boardRef?: RefObject<HTMLDivElement | null>
  picked?: string | null
  onSquare?: (sq: string) => void
  heat?: number[]
}) {
  const pieces = boardFromFen(fen)
  const max = heat ? Math.max(...heat, 1e-9) : 1
  return (
    <div className="board" ref={boardRef}>
      {pieces.map((piece, i) => {
        const file = i % 8
        const rank = 7 - Math.floor(i / 8)
        const sq = squareName([file, rank])
        const dark = (file + rank) % 2 === 0
        const region = Math.floor(rank / 2) * 4 + Math.floor(file / 2)
        return (
          <button
            key={sq}
            className={`board__sq ${dark ? 'board__sq--dark' : 'board__sq--light'}${picked === sq ? ' board__sq--picked' : ''}`}
            onClick={onSquare ? () => onSquare(sq) : undefined}
            disabled={!onSquare}
            aria-label={`${sq}${piece ? ` ${piece}` : ''}`}
          >
            {heat && <span className="board__heat" style={{ opacity: (heat[region] / max) * 0.75 }} />}
            <span className="board__piece">{piece}</span>
          </button>
        )
      })}
    </div>
  )
}

const pct = (x: number) => `${Math.round(x * 100)}%`

function Results({ results, errorPx }: { results: Result[]; errorPx: number | null }) {
  return (
    <section className="stack">
      <p className="muted">
        Darker blocks got more of your gaze (2×2 squares each, because webcam tracking is only accurate to
        about 1–3 squares
        {errorPx !== null ? `; your accuracy check was off by about ${Math.round(errorPx)} px` : ''}). Nothing
        was stored.
      </p>
      <div className="gaze-results">
        {results.map((r) => (
          <article key={r.puzzle.id} className="finding finding--profile">
            <h4 className="finding__title">
              {r.puzzle.hint} {r.solved ? '✓ solved' : '✗ not solved'} in {r.seconds.toFixed(0)} s
            </h4>
            <Board fen={r.puzzle.fen} heat={r.summary.regions} />
            <ul className="gaze-stats">
              <li>
                On the board:{' '}
                <strong>{pct(r.summary.samples ? r.summary.onBoard / r.summary.samples : 0)}</strong> of the
                time
              </li>
              <li>
                Opponent’s half: <strong>{pct(r.summary.opponentHalf)}</strong>
              </li>
              <li>
                Near your king: <strong>{pct(r.summary.ownKing)}</strong> · near the opponent’s king:{' '}
                <strong>{pct(r.summary.enemyKing)}</strong>
              </li>
              <li>
                First looked at:{' '}
                <strong>{r.summary.firstRegion === null ? '–' : regionName(r.summary.firstRegion)}</strong>
              </li>
            </ul>
          </article>
        ))}
      </div>
      <p className="muted small">
        Research question for later: do strong players look at the opponent’s threats first, and do misses go
        with tunnel vision on one area? See docs/research/gaze-*.md.
      </p>
      <button onClick={() => window.location.reload()}>Try again</button>
    </section>
  )
}
