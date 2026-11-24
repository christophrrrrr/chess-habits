import { Cpu } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { deepApi, type DeepStatus } from '../api'
import { runDeep, type Progress } from '../deep/run'

const PHASE: Record<Progress['phase'], string> = {
  games: 'Loading your games',
  positions: 'Reading positions',
  endings: 'Stockfish: final positions',
  engine: 'Stockfish: your moves',
  done: 'Done',
}

const minutes = (s: number) => (s < 90 ? `${Math.round(s)} s` : `${Math.round(s / 60)} min`)

/** Runs the deep analysis (positions + Stockfish) in this browser and stores the results. */
export function DeepPanel({ playerId, onDone }: { playerId: number; onDone: () => void }) {
  const [status, setStatus] = useState<DeepStatus | null>(null)
  const [games, setGames] = useState(50)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [error, setError] = useState<string | null>(null)
  const stop = useRef(false)

  useEffect(() => {
    deepApi
      .status(playerId)
      .then(setStatus)
      .catch(() => setStatus(null))
  }, [playerId])

  async function start() {
    stop.current = false
    setError(null)
    try {
      setStatus(await runDeep(playerId, { engineGames: games }, setProgress, () => stop.current))
      if (!stop.current) onDone()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setProgress(null)
    }
  }

  const running = progress !== null
  return (
    <section className="deep panel" aria-label="Deep analysis">
      <div className="deep__head">
        <Cpu size={18} aria-hidden="true" />
        <strong>Deep analysis</strong>
        <span className="muted small">Stockfish 19 runs in this browser; nothing to install</span>
      </div>
      <p className="muted small">
        {status
          ? `${status.engine} games analysed by Stockfish, ${status.positions} games read for the opening autopilot.`
          : 'Not run yet.'}{' '}
        It takes about 15 s per game; you can stop and continue later.
      </p>
      {running ? (
        <div className="deep__progress">
          <span>
            {PHASE[progress.phase]}: {progress.done} of {progress.total}
            {progress.eta !== undefined && progress.done > 1 && ` · about ${minutes(progress.eta)} left`}
          </span>
          <progress value={progress.done} max={Math.max(progress.total, 1)} />
          <button className="small" onClick={() => (stop.current = true)}>
            Stop
          </button>
        </div>
      ) : (
        <div className="deep__start">
          <label>
            Stockfish on your last{' '}
            <select value={games} onChange={(e) => setGames(Number(e.target.value))}>
              {[25, 50, 100, 200].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>{' '}
            games
          </label>
          <button onClick={start}>Run deep analysis</button>
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </section>
  )
}
