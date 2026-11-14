import { Download } from 'lucide-react'
import { useState } from 'react'
import { gamesApi } from '../api'

interface Props {
  playerId: number
  onImported: () => void
}

type State =
  | { kind: 'idle' }
  | { kind: 'running'; done: number; total: number; month: string; newGames: number }
  | { kind: 'done'; newGames: number; months: number }
  | { kind: 'error'; message: string }

/** Imports every month that is not fully imported yet (full chess.com history), one request per month. */
export function ImportPanel({ playerId, onImported }: Props) {
  const [state, setState] = useState<State>({ kind: 'idle' })

  async function importAll() {
    try {
      setState({ kind: 'running', done: 0, total: 0, month: '', newGames: 0 })
      const months = (await gamesApi.listArchives(playerId)).filter((m) => !m.complete)
      let newGames = 0
      for (const [i, m] of months.entries()) {
        setState({ kind: 'running', done: i, total: months.length, month: m.month, newGames })
        const r = await gamesApi.importMonth(playerId, m.month)
        newGames += r.new_games
      }
      setState({ kind: 'done', newGames, months: months.length })
      onImported()
    } catch (e) {
      setState({ kind: 'error', message: (e as Error).message })
      onImported()
    }
  }

  const running = state.kind === 'running'
  return (
    <div className="import">
      <button className="big-button" onClick={importAll} disabled={running}>
        <Download size={18} aria-hidden="true" />
        {running ? 'Importing…' : 'Import from chess.com'}
      </button>
      <div className="import__status">
        {state.kind === 'running' && (
          <div className="progress" aria-live="polite">
            <progress value={state.done} max={state.total || 1} />
            <span>
              {state.total
                ? `${state.month} (${state.done}/${state.total} months, ${state.newGames} new games)`
                : 'Looking up archives…'}
            </span>
          </div>
        )}
        {state.kind === 'done' && (
          <p className="ok" aria-live="polite">
            Imported {state.newGames} new games from {state.months} month{state.months === 1 ? '' : 's'}.
          </p>
        )}
        {state.kind === 'error' && <p className="error">{state.message}</p>}
      </div>
    </div>
  )
}
