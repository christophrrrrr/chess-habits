// What a tile on the player overview shows for a finding or a rule (pure, unit tested).
import type { Finding, FindingLabel, Rule } from './api'
import { capitalize, elo, LABEL_TEXT, percent } from './format'

export type Tone = 'good' | 'bad' | 'neutral'

export interface TileModel {
  name: string
  value: string
  caption: string
  tone: Tone
  badge: { text: string; kind: FindingLabel } | null
}

export const TILE_NAMES: Record<string, string> = {
  clock_profile: 'Time trouble',
  time_trouble_score: 'Cost of time trouble',
  after_loss_requeue: 'Next game after a loss',
  after_loss_result: 'Play after a loss',
  stop_loss_rules: 'Stop-loss rules',
  warm_up: 'First game of a session',
  time_of_day: 'Time of day',
  opening_time: 'Opening time',
  premoves: 'Premoves',
  form: 'Form over time',
  critical_moments: 'Critical moments',
  endings: 'How your games end',
  opening_autopilot: 'Opening autopilot',
}

const signed = (v: number) => `${v >= 0 ? '+' : '−'}${Math.abs(Math.round(v))}`

/** "Rapid: time trouble costs you about 61 Elo" -> "Time trouble costs you about 61 Elo". */
export function stripTimeClass(title: string): string {
  return capitalize(title.replace(/^[A-Z][a-z]+:\s*/, ''))
}

function badge(label: FindingLabel): TileModel['badge'] {
  return label === 'profile' ? null : { text: LABEL_TEXT[label], kind: label }
}

export function findingTile(f: Finding): TileModel {
  const name = TILE_NAMES[f.analysis_key] ?? capitalize(f.analysis_key.replace(/_/g, ' '))
  const caption = stripTimeClass(f.title)
  const significant = f.label === 'finding' || f.label === 'exploratory'
  const base = { name, caption, badge: badge(f.label) }

  if (f.label === 'not_enough_data') return { ...base, value: '–', tone: 'neutral' }

  if (f.analysis_key === 'clock_profile') {
    const rate = (f.details.entry as { rate: number | null } | undefined)?.rate
    return { ...base, value: percent(rate), tone: 'neutral' }
  }
  if (f.analysis_key === 'stop_loss_rules') {
    const rules = (f.details.rules ?? []) as Array<{ verdict: string }>
    const helps = rules.filter((r) => r.verdict === 'helps').length
    return { ...base, value: `${helps}/${rules.length}`, tone: helps > 0 ? 'good' : 'neutral' }
  }
  if (f.analysis_key === 'time_of_day') {
    const ws = (f.details.windows ?? []) as Array<{ verdict: string; vs_rest_elo?: number }>
    const worst = ws.filter((w) => w.verdict === 'worse').sort((a, b) => a.vs_rest_elo! - b.vs_rest_elo!)[0]
    const best = ws.filter((w) => w.verdict === 'better').sort((a, b) => b.vs_rest_elo! - a.vs_rest_elo!)[0]
    const pick = worst ?? best
    if (!pick) return { ...base, value: '–', tone: 'neutral' }
    return { ...base, value: `${signed(pick.vs_rest_elo!)} Elo`, tone: worst ? 'bad' : 'good' }
  }
  if (f.analysis_key === 'opening_time') {
    return { ...base, value: percent(f.details.used_median as number | null), tone: 'neutral' }
  }
  if (f.analysis_key === 'premoves') {
    return { ...base, value: percent(f.details.rate as number | null), tone: 'neutral' }
  }
  if (f.analysis_key === 'critical_moments') {
    const c = f.details.critical as { rate: number | null; n: number } | undefined
    return { ...base, value: c && c.n >= 30 ? percent(c.rate) : '–', tone: 'neutral' }
  }
  if (f.analysis_key === 'endings') {
    const r = f.details.resignations as { n: number; premature: { rate: number | null } } | undefined
    return { ...base, value: r && r.n > 0 ? percent(r.premature.rate) : '–', tone: 'neutral' }
  }
  if (f.analysis_key === 'opening_autopilot') {
    const a = f.details.think_familiar as number | null
    const b = f.details.think_new as number | null
    return { ...base, value: a && b ? `${(b / a).toFixed(1)}×` : '–', tone: 'neutral' }
  }
  if (f.analysis_key === 'form') {
    const months = (f.details.months ?? []) as Array<{ rating: number | null }>
    const last = [...months].reverse().find((m) => m.rating !== null)
    return { ...base, value: last ? String(Math.round(last.rating!)) : '–', tone: 'neutral' }
  }
  if (f.metric === 'share') {
    const a = f.details.mean_a as number | undefined
    const b = f.details.mean_b as number | undefined
    const value = a !== undefined && b !== undefined ? `${percent(a)} vs ${percent(b)}` : percent(f.effect)
    return { ...base, value, tone: 'neutral' }
  }
  if (f.metric === 'score' && f.effect !== null) {
    const tone: Tone = significant ? (f.effect < 0 ? 'bad' : 'good') : 'neutral'
    return { ...base, value: `${elo(f.effect)} Elo`, tone }
  }
  return { ...base, value: '–', tone: 'neutral' }
}

/** A rule tile: how often it was kept since adoption, once a check exists for its current version. */
export function ruleTile(rule: Rule, check?: Finding): TileModel {
  // A check computed for an older version of the rule (threshold changed since) is stale.
  const current = check && check.details.adopted_at === rule.adopted_at ? check : undefined
  const after = current?.details.after as { rate: number | null } | undefined
  const label = current ? current.label : 'not_enough_data'
  const significant = label === 'finding' || label === 'exploratory'
  const tone: Tone =
    significant && current!.effect !== null ? (current!.effect > 0 ? 'good' : 'bad') : 'neutral'
  return {
    name: 'Your rule',
    value: current && after ? percent(after.rate) : '–',
    caption: capitalize(rule.description),
    tone,
    badge: { text: label === 'not_enough_data' ? 'Too early' : LABEL_TEXT[label], kind: label },
  }
}

/** The finding most worth a look on an account tile: the largest significant result in Elo. */
export function headline(findings: Finding[]): Finding | undefined {
  return findings
    .filter((f) => f.label === 'finding' && f.metric === 'score' && f.effect !== null)
    .sort((a, b) => Math.abs(b.effect!) - Math.abs(a.effect!))[0]
}
