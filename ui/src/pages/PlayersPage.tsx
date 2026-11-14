import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { gamesApi, type Player } from '../api'
import { formatDate } from '../format'

export function PlayersPage() {
  const [players, setPlayers] = useState<Player[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [username, setUsername] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    gamesApi
      .listPlayers()
      .then((p) => {
        setPlayers(p)
        setError(null)
      })
      .catch((e: Error) => setError(e.message))
  }, [])

  useEffect(load, [load])

  async function add(e: FormEvent) {
    e.preventDefault()
    if (!username.trim()) return
    setBusy(true)
    try {
      const p = await gamesApi.createPlayer(username.trim())
      setUsername('')
      window.location.hash = `#/players/${p.id}`
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function remove(p: Player) {
    if (!window.confirm(`Stop tracking ${p.username}? Their imported games are deleted.`)) return
    try {
      await gamesApi.deletePlayer(p.id)
      load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="stack">
      <section className="hero">
        <h2>Find out how you lose points, not just where.</h2>
        <p className="muted">
          Kiebitz looks at hundreds of your games at once: your clock, your sessions, how you react to losses.
          Every finding comes with its sample size and how sure we are.
        </p>
      </section>

      <section className="panel">
        <h3>Track a chess.com account</h3>
        <form className="add-form" onSubmit={add}>
          <label htmlFor="username" className="sr-only">
            chess.com username
          </label>
          <input
            id="username"
            placeholder="chess.com username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="off"
          />
          <button type="submit" disabled={busy || !username.trim()}>
            {busy ? 'Checking…' : 'Add'}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      <section className="panel">
        <h3>Tracked accounts</h3>
        {players === null && !error && <p className="muted">Loading…</p>}
        {players?.length === 0 && <p className="muted">No accounts yet. Add one above.</p>}
        {players && players.length > 0 && (
          <ul className="player-list">
            {players.map((p) => (
              <li key={p.id}>
                <a href={`#/players/${p.id}`} className="player-list__name">
                  {p.display_name ? `${p.display_name} (${p.username})` : p.username}
                </a>
                <span className="muted">last import: {formatDate(p.last_imported_at)}</span>
                <button className="link danger" onClick={() => remove(p)} aria-label={`Delete ${p.username}`}>
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
