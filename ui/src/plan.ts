// "Your plan": the habits that cost the most points, ranked, each with one concrete thing to do.
// Pure and unit tested. Only findings with real evidence (Finding or Exploratory, or a stop-loss
// rule / time window whose interval excludes zero) become plan items.
import type { Finding, FindingLabel, RuleDraft } from './api'
import { ELO_PER_SCORE_POINT } from './format'

export interface PlanItem {
  id: string
  timeClass: string
  /** The card the item comes from (for the link). */
  analysisKey: string
  title: string
  /** Elo lost in the games it affects (always positive for a cost). */
  costElo: number
  /** Share of this time control's games the habit affects (0..1). */
  affects: number
  /** costElo x affects: Elo over an average game, what the ranking uses. */
  perGameElo: number
  evidence: FindingLabel | 'clear'
  action: string
  draft?: RuleDraft
}

export interface Strength {
  id: string
  timeClass: string
  analysisKey: string
  title: string
  gainElo: number
}

const significant = (f: Finding) => f.label === 'finding' || f.label === 'exploratory'
const toElo = (points: number) => points * ELO_PER_SCORE_POINT
const pct = (x: number) => `${Math.round(x * 100)}%`

function find(findings: Finding[], tc: string, key: string) {
  return findings.find((f) => f.time_class === tc && f.analysis_key === key)
}

function item(
  f: Finding,
  fields: Omit<PlanItem, 'id' | 'timeClass' | 'analysisKey' | 'perGameElo' | 'evidence'> & {
    evidence?: PlanItem['evidence']
  },
): PlanItem {
  const affects = Math.min(1, Math.max(0, fields.affects))
  return {
    id: `${f.time_class}:${f.analysis_key}:${fields.title}`,
    timeClass: f.time_class,
    analysisKey: f.analysis_key,
    evidence: fields.evidence ?? f.label,
    ...fields,
    affects,
    perGameElo: fields.costElo * affects,
  }
}

/** Ranked costs (largest Elo per average game first) and strengths, over all time controls. */
export function buildPlan(findings: Finding[]): { items: PlanItem[]; strengths: Strength[] } {
  const items: PlanItem[] = []
  const strengths: Strength[] = []

  for (const f of findings) {
    const tc = f.time_class
    const n = (k: string) => (f.details[k] as number | undefined) ?? 0

    if (f.kind === 'contrast' && f.metric === 'score' && significant(f) && f.effect !== null) {
      const elo = toElo(f.effect)
      if (elo > 0) {
        strengths.push({
          id: `${tc}:${f.analysis_key}`,
          timeClass: tc,
          analysisKey: f.analysis_key,
          title: f.title,
          gainElo: elo,
        })
        continue
      }
      if (f.analysis_key === 'time_trouble_score') {
        const profile = find(findings, tc, 'clock_profile')
        const entry = profile?.details.entry as { rate: number | null } | undefined
        const cp = profile?.details.checkpoint as { move: number; min_share: number } | null | undefined
        items.push(
          item(f, {
            title: `Time trouble costs you ${Math.round(-elo)} Elo in ${tc}`,
            costElo: -elo,
            affects: entry?.rate ?? n('n_a') / Math.max(1, n('n_a') + n('n_b')),
            action: cp
              ? `Keep at least ${pct(cp.min_share)} of your clock after move ${cp.move}. Three in four of your wins do.`
              : 'Spend less time on the moves before the clock gets low: see where your time goes on the card.',
            draft: cp
              ? { time_class: tc, kind: 'clock_checkpoint', move: cp.move, min_share: cp.min_share }
              : undefined,
          }),
        )
      } else if (f.analysis_key === 'after_loss_result') {
        items.push(
          item(f, {
            title: `You play ${Math.round(-elo)} Elo below your level right after a loss in ${tc}`,
            costElo: -elo,
            affects: n('n_a') / Math.max(1, f.sample_size),
            action:
              'After a loss, take a 5-minute break before the next game (check the stop-loss card for a rule that would have helped).',
          }),
        )
      } else if (f.analysis_key === 'warm_up') {
        items.push(
          item(f, {
            title: `Your first game of a session costs you ${Math.round(-elo)} Elo in ${tc}`,
            costElo: -elo,
            affects: n('n_a') / Math.max(1, f.sample_size),
            action: 'Warm up before the first rated game: a few puzzles or one unrated game.',
          }),
        )
      }
    }

    if (f.analysis_key === 'stop_loss_rules') {
      const rules = (f.details.rules ?? []) as Array<{
        rule: string
        name: string
        skipped_games: number
        difference_elo: number | null
        verdict: string
      }>
      const helps = rules
        .filter((r) => r.verdict === 'helps' && r.difference_elo !== null)
        .sort((a, b) => a.difference_elo! - b.difference_elo!)[0]
      if (helps) {
        items.push(
          item(f, {
            title: `${helps.name}: the games it skips cost you ${Math.round(-helps.difference_elo!)} Elo in ${tc}`,
            costElo: -helps.difference_elo!,
            affects: helps.skipped_games / Math.max(1, f.sample_size),
            evidence: 'clear',
            action: `${helps.name}.`,
            draft: { time_class: tc, kind: 'stop_loss', stop_rule: helps.rule },
          }),
        )
      }
    }

    if (f.analysis_key === 'time_of_day') {
      const ws = (f.details.windows ?? []) as Array<{
        name: string
        games: number
        verdict: string
        vs_rest_elo?: number
      }>
      const total = ws.reduce((a, w) => a + w.games, 0)
      for (const w of ws) {
        if (w.verdict === 'worse' && w.vs_rest_elo !== undefined)
          items.push(
            item(f, {
              title: `You play ${Math.round(-w.vs_rest_elo)} Elo below your level ${w.name.split(' (')[0]} in ${tc}`,
              costElo: -w.vs_rest_elo,
              affects: w.games / Math.max(1, total),
              evidence: 'clear',
              action: `Avoid rated ${tc} games ${w.name}.`,
            }),
          )
        if (w.verdict === 'better' && w.vs_rest_elo !== undefined)
          strengths.push({
            id: `${tc}:time_of_day:${w.name}`,
            timeClass: tc,
            analysisKey: 'time_of_day',
            title: `You play your best ${w.name}`,
            gainElo: w.vs_rest_elo,
          })
      }
    }

    if (f.analysis_key === 'opening_time') {
      const ops = (f.details.openings ?? []) as Array<{
        opening: string
        games: number
        elo: number | null
        high: number | null
        used: number | null
      }>
      const total = f.sample_size
      for (const o of ops) {
        if (o.elo !== null && o.high !== null && o.high < 0)
          items.push(
            item(f, {
              title: `The ${o.opening} costs you ${Math.round(-o.elo)} Elo in ${tc}`,
              costElo: -o.elo,
              affects: o.games / Math.max(1, total),
              evidence: 'exploratory',
              action: `Review your ${o.opening} games, or switch to a line you know better (you use ${o.used === null ? '–' : pct(o.used)} of your clock by move 12 in it).`,
            }),
          )
      }
    }
  }

  items.sort((a, b) => b.perGameElo - a.perGameElo)
  strengths.sort((a, b) => b.gainElo - a.gainElo)
  return { items, strengths }
}
