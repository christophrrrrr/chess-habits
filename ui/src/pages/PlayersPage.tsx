import { Plus, Trash } from 'lucide-react'
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { gamesApi, insightsApi, type Finding, type Player } from '../api'
import { formatDate } from '../format'
import { headline } from '../tiles'

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
        <h2>Game review shows what you played. Chess Habits shows how you play.</h2>
        <p className="muted">
          How you spend your clock, how you react to a loss, whether you keep the rules you set yourself:
          habits that never show up in a move list. Chess Habits measures them across hundreds of your games,
          and every finding says how sure it is.
        </p>
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
          <button type="submit" className="big-button" disabled={busy || !username.trim()}>
            <Plus size={18} aria-hidden="true" />
            {busy ? 'Checking…' : 'Add'}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      <section aria-label="Tracked accounts">
        <h3 className="section-title">Tracked accounts</h3>
        {players === null && !error && <p className="muted">Loading…</p>}
        {players?.length === 0 && <p className="muted">No accounts yet. Add one above.</p>}
        {players && players.length > 0 && (
          <div className="account-grid">
            {players.map((p) => (
              <AccountTile key={p.id} player={p} onDelete={() => remove(p)} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

/** A big account tile: who, how many games, and the result most worth a look. */
function AccountTile({ player, onDelete }: { player: Player; onDelete: () => void }) {
  const [games, setGames] = useState<number | null>(null)
  const [top, setTop] = useState<Finding | null>(null)
  const name = player.display_name ?? player.username

  useEffect(() => {
    // Extras: the tile works without them if a service is slow or down.
    gamesApi
      .getPlayer(player.id)
      .then((d) => setGames(Object.values(d.game_counts).reduce((a, b) => a + b, 0)))
      .catch(() => setGames(null))
    insightsApi
      .latestFindings(player.id)
      .then((run) => setTop(headline(run.findings) ?? null))
      .catch(() => setTop(null))
  }, [player.id])

  return (
    <article className="account">
      <a href={`#/players/${player.id}`} className="account__link">
        <span className="avatar" aria-hidden="true">
          {name[0].toUpperCase()}
        </span>
        <span className="account__text">
          <span className="account__name">{player.username}</span>
          <span className="muted small">
            {games !== null ? `${games} games · ` : ''}last import {formatDate(player.last_imported_at)}
          </span>
        </span>
      </a>
      {top && <p className={`account__top account__top--${top.effect! < 0 ? 'bad' : 'good'}`}>{top.title}</p>}
      <button className="icon-button danger" onClick={onDelete} aria-label={`Delete ${player.username}`}>
        <Trash size={16} aria-hidden="true" />
      </button>
    </article>
  )
}
