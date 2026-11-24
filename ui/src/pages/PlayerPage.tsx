import { ArrowLeft, ChartColumn } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  ApiError,
  gamesApi,
  insightsApi,
  type Finding,
  type Game,
  type PlayerDetail,
  type Rule,
  type RuleDraft,
  type Run,
} from '../api'
import type { RuleActions } from '../components/AdoptButton'
import { FindingCard } from '../components/FindingCard'
import { HabitTile } from '../components/HabitTile'
import { DeepPanel } from '../components/DeepPanel'
import { ImportPanel } from '../components/ImportPanel'
import { RuleCard } from '../components/RuleCard'
import { TileIcon } from '../components/TileIcon'
import { capitalize, formatDate, sortTimeClasses } from '../format'
import { REFERENCE_MONTHS } from '../importer'
import { ComparePage } from './ComparePage'
import { PlanPage } from './PlanPage'
import { GazePage } from './GazePage'
import { ownPuzzles, PUZZLES } from '../gaze/model'
import { buildPlan } from '../plan'
import { href, type PlayerView } from '../routes'
import { findingTile, ruleTile, TILE_NAMES } from '../tiles'

type Props = { playerId: number; view: PlayerView }

/** One player: loads the account, the latest analysis and the rules once, then shows a view. */
export function PlayerPage({ playerId, view }: Props) {
  const [player, setPlayer] = useState<PlayerDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [run, setRun] = useState<Run | null>(null)
  const [runError, setRunError] = useState<string | null>(null)
  const [runLoaded, setRunLoaded] = useState(false)
  const [rules, setRules] = useState<Rule[]>([])
  const [busy, setBusy] = useState(false)

  const loadPlayer = useCallback(() => {
    gamesApi
      .getPlayer(playerId)
      .then(setPlayer)
      .catch((e: Error) => setError(e.message))
  }, [playerId])

  useEffect(loadPlayer, [loadPlayer])

  useEffect(() => {
    insightsApi
      .latestFindings(playerId)
      .then(setRun)
      .catch((e: ApiError) => {
        if (e.status !== 404) setRunError(e.message)
      })
      .finally(() => setRunLoaded(true))
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
    setRunError(null)
    try {
      setRun(await insightsApi.runAnalyses(playerId))
    } catch (e) {
      setRunError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  if (error) return <p className="error">{error}</p>
  if (!player) return <p className="muted">Loading…</p>

  const name = player.display_name ?? player.username
  const total = Object.values(player.game_counts).reduce((a, b) => a + b, 0)
  const checks = (run?.findings ?? []).filter((f) => f.analysis_key === 'rule_check')

  if (view.view === 'finding') {
    const finding = run?.findings.find((f) => f.time_class === view.tc && f.analysis_key === view.key)
    return (
      <Detail
        back={href({ page: 'player', id: playerId, view: 'overview', tc: view.tc })}
        backLabel={`${name} · ${capitalize(view.tc)}`}
        icon={view.key}
        title={TILE_NAMES[view.key] ?? capitalize(view.key.replace(/_/g, ' '))}
      >
        {finding ? (
          <>
            <FindingCard finding={finding} actions={actions} />
            <StatsNote />
          </>
        ) : (
          <p className="muted">{runLoaded ? 'This result is not in the latest analysis.' : 'Loading…'}</p>
        )}
      </Detail>
    )
  }

  if (view.view === 'rule') {
    const rule = rules.find((r) => r.id === view.ruleId)
    const back = href({ page: 'player', id: playerId, view: 'overview', tc: rule?.time_class })
    return (
      <Detail back={back} backLabel={name} icon="rule" title="Your rule">
        {rule ? (
          <RuleCard
            rule={rule}
            check={checks.find((f) => f.details.rule_id === rule.id)}
            onRetire={async (r) => {
              await retire(r)
              window.location.hash = back
            }}
          />
        ) : (
          <p className="muted">This rule is not tracked (any more).</p>
        )}
      </Detail>
    )
  }

  if (view.view === 'compare')
    return (
      <Detail
        back={href({ page: 'player', id: playerId, view: 'overview' })}
        backLabel={name}
        icon="grandmaster"
        title="You and a grandmaster"
      >
        {runLoaded ? (
          <ComparePage playerId={playerId} playerName={name} hasOwnRun={run !== null} refId={view.refId} />
        ) : (
          <p className="muted">Loading…</p>
        )}
      </Detail>
    )

  if (view.view === 'gaze') {
    const own = ownPuzzles(run?.findings ?? [])
    return (
      <GazePage
        puzzles={own.length > 0 ? own : PUZZLES}
        back={href({ page: 'player', id: playerId, view: 'overview' })}
      />
    )
  }

  if (view.view === 'plan')
    return (
      <Detail
        back={href({ page: 'player', id: playerId, view: 'overview' })}
        backLabel={name}
        icon="plan"
        title="Your plan"
      >
        {run ? (
          <PlanPage playerId={playerId} findings={run.findings} actions={actions} />
        ) : (
          <p className="muted">{runLoaded ? 'Run an analysis first.' : 'Loading…'}</p>
        )}
      </Detail>
    )

  if (view.view === 'games')
    return (
      <Detail
        back={href({ page: 'player', id: playerId, view: 'overview' })}
        backLabel={name}
        icon="games"
        title="Recent games"
      >
        <RecentGames playerId={playerId} />
      </Detail>
    )

  return (
    <div className="stack">
      <a href="#/" className="back">
        <ArrowLeft size={16} aria-hidden="true" /> All accounts
      </a>
      <section className="player-head">
        <span className="avatar avatar--big" aria-hidden="true">
          {name[0].toUpperCase()}
        </span>
        <div className="player-head__text">
          <h2>{name}</h2>
          <p className="muted">
            chess.com/{player.username} · {total} games · last import {formatDate(player.last_imported_at)}
          </p>
          <NotesEditor player={player} onSaved={loadPlayer} />
        </div>
      </section>
      <section className="actions">
        <ImportPanel
          playerId={playerId}
          onImported={loadPlayer}
          lastMonths={player.kind === 'reference' ? REFERENCE_MONTHS : undefined}
        />
        <div className="actions__analyse">
          <button className="big-button" onClick={analyse} disabled={busy || total === 0}>
            <ChartColumn size={18} aria-hidden="true" />
            {busy ? 'Analysing…' : run ? 'Re-run analysis' : 'Analyse my games'}
          </button>
          <p className="muted small">
            {run
              ? `Last analysis ${formatDate(run.finished_at)} over ${run.games_analyzed} games.`
              : 'Run an analysis after importing your games.'}
          </p>
        </div>
      </section>
      {player.kind !== 'reference' && total > 0 && <DeepPanel playerId={playerId} onDone={analyse} />}
      {runError && <p className="error">{runError}</p>}
      <Overview playerId={playerId} player={player} run={run} rules={rules} checks={checks} tc={view.tc} />
    </div>
  )
}

function Overview({
  playerId,
  player,
  run,
  rules,
  checks,
  tc,
}: {
  playerId: number
  player: PlayerDetail
  run: Run | null
  rules: Rule[]
  checks: Finding[]
  tc?: string
}) {
  const classes = useMemo(
    () => sortTimeClasses([...new Set(run?.findings.map((f) => f.time_class) ?? [])]),
    [run],
  )
  // Default to the time control with the most games.
  const busiest = [...classes].sort((a, b) => (player.game_counts[b] ?? 0) - (player.game_counts[a] ?? 0))[0]
  const active = tc && classes.includes(tc) ? tc : busiest
  const total = Object.values(player.game_counts).reduce((a, b) => a + b, 0)

  return (
    <>
      {run && classes.length > 0 && <PlanTile playerId={playerId} run={run} />}
      {run && classes.length > 0 && (
        <>
          <nav className="segmented" aria-label="Time control">
            {classes.map((c) => (
              <a
                key={c}
                href={href({ page: 'player', id: playerId, view: 'overview', tc: c })}
                className={c === active ? 'segmented__item segmented__item--active' : 'segmented__item'}
                aria-current={c === active ? 'page' : undefined}
              >
                {capitalize(c)}
                <span className="segmented__count">{player.game_counts[c] ?? 0}</span>
              </a>
            ))}
          </nav>

          <section aria-label="Your habits">
            <h3 className="section-title">Your habits in {active}</h3>
            <div className="habit-grid">
              {run.findings
                .filter((f) => f.time_class === active && f.analysis_key !== 'rule_check')
                .map((f) => (
                  <HabitTile
                    key={f.id}
                    tile={findingTile(f)}
                    icon={f.analysis_key}
                    to={href({
                      page: 'player',
                      id: playerId,
                      view: 'finding',
                      tc: active,
                      key: f.analysis_key,
                    })}
                  />
                ))}
            </div>
          </section>

          {rules.some((r) => r.time_class === active) && (
            <section aria-label="Your rules">
              <h3 className="section-title">Rules you track</h3>
              <div className="habit-grid">
                {rules
                  .filter((r) => r.time_class === active)
                  .map((r) => (
                    <HabitTile
                      key={r.id}
                      tile={ruleTile(
                        r,
                        checks.find((f) => f.details.rule_id === r.id),
                      )}
                      icon="rule"
                      to={href({ page: 'player', id: playerId, view: 'rule', ruleId: r.id })}
                    />
                  ))}
              </div>
            </section>
          )}
        </>
      )}

      <section aria-label="More">
        <h3 className="section-title">More</h3>
        <div className="habit-grid">
          {total > 0 && (
            <HabitTile
              tile={{
                name: 'Recent games',
                value: String(total),
                caption: 'Your latest games with results and openings',
                tone: 'neutral',
                badge: null,
              }}
              icon="games"
              to={href({ page: 'player', id: playerId, view: 'games' })}
            />
          )}
          {player.kind !== 'reference' && (
            <HabitTile
              tile={{
                name: 'Compare with a grandmaster',
                value: 'You vs. GM',
                caption:
                  'Your habits next to a grandmaster you pick, e.g. how Hikaru uses his clock compared with you.',
                tone: 'neutral',
                badge: null,
              }}
              icon="grandmaster"
              to={href({ page: 'player', id: playerId, view: 'compare' })}
            />
          )}
          <HabitTile
            icon="gaze"
            to={href({ page: 'player', id: playerId, view: 'gaze' })}
            tile={{
              name: 'Where you look',
              value: 'Try it',
              caption:
                'Prototype: webcam eye tracking on positions from your own games that you got wrong (after the deep analysis). Runs only in your browser.',
              tone: 'neutral',
              badge: { text: 'Prototype', kind: 'exploratory' },
            }}
          />
        </div>
      </section>
      {run && <StatsNote />}
    </>
  )
}

function PlanTile({ playerId, run }: { playerId: number; run: Run }) {
  const { items } = buildPlan(run.findings)
  const top = items[0]
  return (
    <section aria-label="Your plan">
      <div className="habit-grid habit-grid--wide">
        <HabitTile
          icon="plan"
          to={href({ page: 'player', id: playerId, view: 'plan' })}
          tile={{
            name: 'Your plan',
            value: items.length === 0 ? 'Nothing clear yet' : `${items.length} to work on`,
            caption: top
              ? `First: ${top.title.charAt(0).toLowerCase()}${top.title.slice(1)}`
              : 'No habit costs you points clearly yet',
            tone: items.length > 0 ? 'bad' : 'neutral',
            badge: null,
          }}
        />
      </div>
    </section>
  )
}

function Detail({
  back,
  backLabel,
  icon,
  title,
  children,
}: {
  back: string
  backLabel: string
  icon: string
  title: string
  children: ReactNode
}) {
  return (
    <div className="stack">
      <a href={back} className="back">
        <ArrowLeft size={16} aria-hidden="true" /> {backLabel}
      </a>
      <header className="detail-head">
        <span className="habit__icon habit__icon--big">
          <TileIcon name={icon} size={28} />
        </span>
        <h2>{title}</h2>
      </header>
      {children}
    </div>
  )
}

function StatsNote() {
  return (
    <p className="muted small">
      Results are compared with what your smoothed rating predicts, in Elo. Each comparison shows its 95%
      interval and the smallest effect your games could reveal. Labels are corrected for testing many things
      at once: “Finding” means strong evidence, “No clear effect” means nothing larger than the stated size.
    </p>
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

function RecentGames({ playerId }: { playerId: number }) {
  const [games, setGames] = useState<Game[] | null>(null)

  useEffect(() => {
    gamesApi
      .listGames(playerId, { limit: 30 })
      .then((p) => setGames(p.items))
      .catch(() => setGames([]))
  }, [playerId])

  if (games === null) return <p className="muted">Loading…</p>
  if (games.length === 0) return <p className="muted">No games imported yet.</p>
  return (
    <section className="panel">
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
