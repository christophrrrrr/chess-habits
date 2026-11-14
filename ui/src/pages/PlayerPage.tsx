import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ApiError,
  gamesApi,
  insightsApi,
  type Game,
  type PlayerDetail,
  type Rule,
  type RuleDraft,
  type Run,
} from '../api'
import type { RuleActions } from '../components/AdoptButton'
import { FindingCard } from '../components/FindingCard'
import { ImportPanel } from '../components/ImportPanel'
import { RuleCard } from '../components/RuleCard'
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
  const [rules, setRules] = useState<Rule[]>([])

  useEffect(() => {
    insightsApi
      .latestFindings(playerId)
      .then(setRun)
      .catch((e: ApiError) => {
        if (e.status !== 404) setError(e.message)
      })
    // Rules are an extra: if they fail to load, the findings still show.
    insightsApi
      .listRules(playerId)
      .then(setRules)
      .catch(() => setRules([]))
  }, [playerId])

  const actions: RuleActions = useMemo(
    () => ({
      rules,
      adopt: async (draft: RuleDraft) => {
        const rule = await insightsApi.createRule(playerId, draft)
        setRules((rs) => [...rs, rule])
      },
    }),
    [rules, playerId],
  )

  async function retire(rule: Rule) {
    await insightsApi.retireRule(rule.id)
    setRules((rs) => rs.filter((r) => r.id !== rule.id))
  }

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
  const checks = useMemo(() => (run?.findings ?? []).filter((f) => f.analysis_key === 'rule_check'), [run])
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
            {rules
              .filter((r) => r.time_class === active)
              .map((r) => (
                <RuleCard
                  key={`rule-${r.id}`}
                  rule={r}
                  check={checks.find((f) => f.details.rule_id === r.id)}
                  onRetire={retire}
                />
              ))}
            {run.findings
              .filter((f) => f.time_class === active && f.analysis_key !== 'rule_check')
              .map((f) => (
                <FindingCard key={f.id} finding={f} actions={actions} />
              ))}
          </div>
          <p className="muted small">
            Results are compared with what your smoothed rating predicts, in Elo. Each comparison shows its
            95% interval (the bar) and the smallest effect your games could reveal. Labels are corrected for
            testing many things at once: “Finding” means strong evidence, “No clear effect” means nothing
            larger than the stated size.
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
