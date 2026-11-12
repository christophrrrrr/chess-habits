import { useCallback, useEffect, useMemo, useState } from 'react'
import { ApiError, gamesApi, insightsApi, type Game, type PlayerDetail, type Run } from '../api'
import { FindingCard } from '../components/FindingCard'
import { ImportPanel } from '../components/ImportPanel'
import { capitalize, formatDate, sortTimeClasses } from '../format'

export function PlayerPage({ playerId }: { playerId: number }) {
  const [player, setPlayer] = useState<PlayerDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadPlayer = useCallback(() => {
    gamesApi
      .getPlayer(playerId)
      .then(setPlayer)
      .catch((e: Error) => setError(e.message))
  }, [playerId])

  useEffect(loadPlayer, [loadPlayer])

  if (error) return <p className="error">{error}</p>
  if (!player) return <p className="muted">Loading…</p>

  const total = Object.values(player.game_counts).reduce((a, b) => a + b, 0)

  return (
    <div className="stack">
      <a href="#/" className="back">
        ← All accounts
      </a>
      <section className="player-head">
        <h2>{player.display_name ?? player.username}</h2>
        <p className="muted">
          chess.com/{player.username} · {total} games · last import {formatDate(player.last_imported_at)}
        </p>
        <NotesEditor player={player} onSaved={loadPlayer} />
        <div className="chips">
          {sortTimeClasses(Object.keys(player.game_counts)).map((tc) => (
            <span key={tc} className="chip">
              {capitalize(tc)} <strong>{player.game_counts[tc]}</strong>
            </span>
          ))}
        </div>
      </section>
      <ImportPanel playerId={playerId} onImported={loadPlayer} />
      <InsightsPanel playerId={playerId} hasGames={total > 0} />
      <RecentGames playerId={playerId} key={total} />
    </div>
  )
}

function NotesEditor({ player, onSaved }: { player: PlayerDetail; onSaved: () => void }) {
  const [editing, setEditing] = useState(false)
  const [notes, setNotes] = useState(player.notes ?? '')
  const [error, setError] = useState<string | null>(null)

  async function save() {
    try {
      await gamesApi.updatePlayer(player.id, { notes: notes.trim() || null })
      setEditing(false)
      setError(null)
      onSaved()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  if (!editing)
    return (
      <p className="notes">
        {player.notes || <span className="muted">No notes.</span>}{' '}
        <button className="link" onClick={() => setEditing(true)}>
          Edit notes
        </button>
      </p>
    )
  return (
    <div className="notes-edit">
      <label htmlFor="notes" className="sr-only">
        Notes
      </label>
      <input id="notes" value={notes} maxLength={500} onChange={(e) => setNotes(e.target.value)} />
      <button onClick={save}>Save</button>
      <button className="link" onClick={() => setEditing(false)}>
        Cancel
      </button>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

function InsightsPanel({ playerId, hasGames }: { playerId: number; hasGames: boolean }) {
  const [run, setRun] = useState<Run | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [tab, setTab] = useState<string | null>(null)

  useEffect(() => {
    insightsApi
      .latestFindings(playerId)
      .then(setRun)
      .catch((e: ApiError) => {
        if (e.status !== 404) setError(e.message)
      })
  }, [playerId])

  async function analyse() {
    setBusy(true)
    setError(null)
    try {
      setRun(await insightsApi.runAnalyses(playerId))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const classes = useMemo(
    () => sortTimeClasses([...new Set(run?.findings.map((f) => f.time_class) ?? [])]),
    [run],
  )
  const active = tab && classes.includes(tab) ? tab : classes[0]

  return (
    <section className="panel">
      <div className="panel__row">
        <div>
          <h3>Insights</h3>
          <p className="muted">
            {run
              ? `Last analysis ${formatDate(run.finished_at)} over ${run.games_analyzed} games.`
              : 'Run an analysis after importing your games.'}
          </p>
        </div>
        <button onClick={analyse} disabled={busy || !hasGames}>
          {busy ? 'Analysing…' : run ? 'Re-run analysis' : 'Analyse my games'}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {run && classes.length > 0 && (
        <>
          <div className="tabs" role="tablist">
            {classes.map((tc) => (
              <button
                key={tc}
                role="tab"
                aria-selected={tc === active}
                className={tc === active ? 'tab tab--active' : 'tab'}
                onClick={() => setTab(tc)}
              >
                {capitalize(tc)}
              </button>
            ))}
          </div>
          <div className="findings">
            {run.findings
              .filter((f) => f.time_class === active)
              .map((f) => (
                <FindingCard key={f.id} finding={f} />
              ))}
          </div>
          <p className="muted small">
            Points = score percentage points against what the ratings predict (a win is 100, a draw 50). The
            bar shows the 95% interval: if it crosses the middle line, the effect may be chance.
          </p>
        </>
      )}
    </section>
  )
}

function RecentGames({ playerId }: { playerId: number }) {
  const [games, setGames] = useState<Game[]>([])

  useEffect(() => {
    gamesApi
      .listGames(playerId, { limit: 15 })
      .then((p) => setGames(p.items))
      .catch(() => setGames([]))
  }, [playerId])

  if (games.length === 0) return null
  return (
    <section className="panel">
      <h3>Recent games</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Opponent</th>
              <th>Result</th>
              <th>Opening</th>
            </tr>
          </thead>
          <tbody>
            {games.map((g) => (
              <tr key={g.id}>
                <td>{formatDate(g.ended_at)}</td>
                <td>{capitalize(g.time_class)}</td>
                <td>
                  {g.opponent_username} ({g.opponent_rating ?? '?'})
                </td>
                <td className={`result result--${g.result}`}>
                  {g.url ? (
                    <a href={g.url} target="_blank" rel="noreferrer">
                      {capitalize(g.result)}
                    </a>
                  ) : (
                    capitalize(g.result)
                  )}
                </td>
                <td className="muted">{g.opening ?? g.eco ?? ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
