import { Crown, RefreshCw, Search } from 'lucide-react'
import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { ApiError, gamesApi, insightsApi, type Comparison, type CompareRow, type Player } from '../api'
import {
  formatInterval,
  formatSide,
  formatValue,
  rowTone,
  SUGGESTED_GRANDMASTERS,
  VERDICT_TEXT,
} from '../compare'
import { MethodsLink } from '../components/MethodsLink'
import { capitalize } from '../format'
import { importMissing, REFERENCE_MONTHS, type ImportProgress } from '../importer'
import { href } from '../routes'

type Props = { playerId: number; playerName: string; hasOwnRun: boolean; refId?: number }

/** You next to a grandmaster: pick one, prepare their games once, then compare habit by habit. */
export function ComparePage({ playerId, playerName, hasOwnRun, refId }: Props) {
  if (!hasOwnRun)
    return (
      <p className="muted">
        Analyse your own games first, then come back to compare them.{' '}
        <a href={href({ page: 'player', id: playerId, view: 'overview' })}>Back to your habits</a>
      </p>
    )
  if (!refId) return <GrandmasterPicker playerId={playerId} />
  return <ComparisonView key={refId} playerId={playerId} playerName={playerName} refId={refId} />
}

function GrandmasterPicker({ playerId }: { playerId: number }) {
  const [players, setPlayers] = useState<Player[]>([])
  const [username, setUsername] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    gamesApi
      .listPlayers()
      .then(setPlayers)
      .catch((e: Error) => setError(e.message))
  }, [])

  const references = players.filter((p) => p.kind === 'reference')
  const open = (id: number) =>
    (window.location.hash = href({ page: 'player', id: playerId, view: 'compare', refId: id }))

  async function pick(name: string) {
    const wanted = name.trim().toLowerCase()
    if (!wanted) return
    const known = players.find((p) => p.username === wanted)
    if (known) return open(known.id)
    setBusy(wanted)
    setError(null)
    try {
      open((await gamesApi.createPlayer(wanted, undefined, 'reference')).id)
    } catch (e) {
      setError((e as Error).message)
      setBusy(null)
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    void pick(username)
  }

  return (
    <div className="stack">
      <p className="muted">
        Pick a grandmaster. Chess Habits imports their last {REFERENCE_MONTHS} months of public chess.com
        games once and runs the same analyses as on yours.
      </p>
      {references.length > 0 && (
        <section aria-label="Grandmasters you compared with">
          <h3 className="section-title">Already prepared</h3>
          <div className="gm-grid">
            {references.map((p) => (
              <button key={p.id} className="gm" onClick={() => open(p.id)}>
                <Crown size={20} aria-hidden="true" />
                <span className="gm__name">{p.display_name ?? p.username}</span>
                <span className="muted small">{p.username}</span>
              </button>
            ))}
          </div>
        </section>
      )}
      <section aria-label="Suggested grandmasters">
        <h3 className="section-title">Suggested</h3>
        <div className="gm-grid">
          {SUGGESTED_GRANDMASTERS.filter((g) => !references.some((p) => p.username === g.username)).map(
            (g) => (
              <button
                key={g.username}
                className="gm"
                onClick={() => pick(g.username)}
                disabled={busy !== null}
              >
                <Crown size={20} aria-hidden="true" />
                <span className="gm__name">{g.name}</span>
                <span className="muted small">{busy === g.username ? 'Adding…' : g.username}</span>
              </button>
            ),
          )}
        </div>
      </section>
      <form className="add-form" onSubmit={submit}>
        <label htmlFor="gm-username" className="sr-only">
          Another chess.com username
        </label>
        <input
          id="gm-username"
          placeholder="Another chess.com username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="off"
        />
        <button type="submit" className="big-button" disabled={busy !== null || !username.trim()}>
          <Search size={18} aria-hidden="true" />
          Compare
        </button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

type Status =
  | { kind: 'loading' }
  | { kind: 'ready'; comparison: Comparison }
  | { kind: 'not_prepared' }
  | { kind: 'error'; message: string }

function ComparisonView({
  playerId,
  playerName,
  refId,
}: {
  playerId: number
  playerName: string
  refId: number
}) {
  const [reference, setReference] = useState<Player | null>(null)
  const [status, setStatus] = useState<Status>({ kind: 'loading' })
  const [progress, setProgress] = useState<ImportProgress | 'analysing' | null>(null)
  const [prepError, setPrepError] = useState<string | null>(null)
  const [tc, setTc] = useState<string | null>(null)

  const load = useCallback(() => {
    insightsApi
      .compare(playerId, refId)
      .then((comparison) => setStatus({ kind: 'ready', comparison }))
      .catch((e: ApiError) =>
        setStatus(e.status === 404 ? { kind: 'not_prepared' } : { kind: 'error', message: e.message }),
      )
  }, [playerId, refId])

  useEffect(() => {
    gamesApi
      .getPlayer(refId)
      .then(setReference)
      .catch((e: Error) => setStatus({ kind: 'error', message: e.message }))
    load()
  }, [refId, load])

  async function prepare() {
    setPrepError(null)
    try {
      setProgress({ done: 0, total: 0, month: '', newGames: 0 })
      await importMissing(refId, setProgress, REFERENCE_MONTHS)
      setProgress('analysing')
      await insightsApi.runAnalyses(refId)
      load()
    } catch (e) {
      setPrepError((e as Error).message)
    } finally {
      setProgress(null)
    }
  }

  const gm = reference ? (reference.display_name ?? reference.username) : 'the grandmaster'
  const prepareButton = (label: string, Icon = Crown) => (
    <div className="import">
      <button className="big-button" onClick={prepare} disabled={progress !== null}>
        <Icon size={18} aria-hidden="true" />
        {progress ? 'Preparing…' : label}
      </button>
      <div className="import__status" aria-live="polite">
        {progress === 'analysing' && <span>Analysing {gm}’s games…</span>}
        {progress && progress !== 'analysing' && (
          <div className="progress">
            <progress value={progress.done} max={progress.total || 1} />
            <span>
              {progress.total
                ? `${progress.month} (${progress.done}/${progress.total} months, ${progress.newGames} new games)`
                : 'Looking up archives…'}
            </span>
          </div>
        )}
        {prepError && <p className="error">{prepError}</p>}
      </div>
    </div>
  )

  const pickAnother = (
    <a href={href({ page: 'player', id: playerId, view: 'compare' })} className="small">
      Pick another grandmaster
    </a>
  )

  if (status.kind === 'loading') return <p className="muted">Loading…</p>
  if (status.kind === 'error') return <p className="error">{status.message}</p>
  if (status.kind === 'not_prepared')
    return (
      <div className="stack">
        <p>
          {gm}’s games are not analysed yet. This imports their last {REFERENCE_MONTHS} months from chess.com
          (a few thousand games, about a minute) and runs the same analyses as on yours.
        </p>
        {prepareButton(`Prepare ${gm}`)}
        {pickAnother}
      </div>
    )

  const { comparison } = status
  const blocks = comparison.blocks
  // Default: the time control where both of you have the most games.
  const shared = (b: (typeof blocks)[number]) =>
    Math.min(b.rows[0]?.you?.n ?? 0, b.rows[0]?.reference?.n ?? 0)
  const active =
    blocks.find((b) => b.time_class === tc) ?? [...blocks].sort((a, b) => shared(b) - shared(a))[0]

  return (
    <div className="stack">
      <p className="muted">
        {playerName}: {comparison.player_run.games_analyzed} games · {gm}:{' '}
        {comparison.reference_run.games_analyzed} games from the last {REFERENCE_MONTHS} months.
      </p>
      {blocks.length === 0 ? (
        <p className="muted">You and {gm} have no time control with enough games in common.</p>
      ) : (
        <>
          <nav className="segmented" aria-label="Time control">
            {blocks.map((b) => (
              <button
                key={b.time_class}
                className={b === active ? 'segmented__item segmented__item--active' : 'segmented__item'}
                aria-pressed={b === active}
                onClick={() => setTc(b.time_class)}
              >
                {capitalize(b.time_class)}
              </button>
            ))}
          </nav>
          <div className="compare">
            {active.rows.map((row) => (
              <CompareCard key={row.key} row={row} gm={gm} />
            ))}
          </div>
        </>
      )}
      <p className="muted small">
        Both sides are measured against their own expected results, so the Elo rows compare habits, not
        playing strength. A grandmaster faces much stronger opponents, which changes some numbers on its own.
        Differences come with a 95% interval and are corrected for testing many rows at once.{' '}
        <MethodsLink section="compare" />
      </p>
      <div className="compare__actions">
        {prepareButton(`Update ${gm}’s games`, RefreshCw)}
        {pickAnother}
      </div>
    </div>
  )
}

function CompareCard({ row, gm }: { row: CompareRow; gm: string }) {
  const tone = rowTone(row)
  return (
    <article className={`compare__row habit--${tone}`} aria-label={row.name}>
      <h4 className="compare__name">{row.name}</h4>
      <div className="compare__sides">
        <Side label="You" unit={row.unit} side={row.you} />
        <Side label={gm} unit={row.unit} side={row.reference} />
      </div>
      {row.verdict !== 'descriptive' && (
        <p className="compare__verdict">
          <span className={`badge badge--${row.verdict === 'different' ? 'finding' : 'no_effect'}`}>
            {VERDICT_TEXT[row.verdict]}
          </span>{' '}
          {row.difference && (
            <span className="muted small">
              You {formatValue(row.unit, row.difference.value, true)} (95%{' '}
              {formatInterval(row.unit, row.difference, true)})
            </span>
          )}
        </p>
      )}
    </article>
  )
}

function Side({ label, unit, side }: { label: string; unit: CompareRow['unit']; side: CompareRow['you'] }) {
  return (
    <div className="compare__side">
      <span className="muted small">{label}</span>
      <span className="compare__value">{formatSide(unit, side)}</span>
      {side && formatInterval(unit, side) && (
        <span className="muted small">{formatInterval(unit, side)}</span>
      )}
    </div>
  )
}
