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
}

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
