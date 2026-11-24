// Small pure formatting helpers (unit tested).

export const TIME_CLASS_ORDER = ['bullet', 'blitz', 'rapid', 'classical', 'daily']

/** Score points (0..1 scale) as signed percentage points: -0.061 -> "-6.1". */
export function points(x: number): string {
  const v = Math.round(x * 1000) / 10
  return `${v > 0 ? '+' : v < 0 ? '−' : '±'}${Math.abs(v).toFixed(1)}`
}

export function capitalize(s: string): string {
  return s ? s[0].toUpperCase() + s.slice(1) : s
}

export function formatDate(iso: string | null): string {
  if (!iso) return 'never'
  const d = new Date(iso.endsWith('Z') ? iso : `${iso}Z`)
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function sortTimeClasses(classes: string[]): string[] {
  const rank = (c: string) => {
    const i = TIME_CLASS_ORDER.indexOf(c)
    return i === -1 ? 99 : i
  }
  return [...classes].sort((a, b) => rank(a) - rank(b) || a.localeCompare(b))
}

export const LABEL_TEXT: Record<string, string> = {
  finding: 'Finding',
  exploratory: 'Exploratory',
  no_effect: 'No clear effect',
  not_enough_data: 'Not enough data',
  profile: 'Profile',
}

/** Score points -> Elo near an expected score of 0.5 (same constant as the insights service). */
export const ELO_PER_SCORE_POINT = 400 / (Math.log(10) * 0.25)

export function elo(scorePoints: number): string {
  const v = Math.round(scorePoints * ELO_PER_SCORE_POINT)
  return `${v > 0 ? '+' : v < 0 ? '−' : '±'}${Math.abs(v)}`
}

export function percent(x: number | null | undefined, digits = 0): string {
  return x === null || x === undefined ? '–' : `${(x * 100).toFixed(digits)}%`
}

/**
 * Position (0..100 %) of a value on a symmetric axis [-range, +range], clamped.
 * Used to draw the effect and its confidence interval.
 */
export function axisPosition(value: number, range: number): number {
  const clamped = Math.max(-range, Math.min(range, value))
  return ((clamped + range) / (2 * range)) * 100
}

/** Short axis label for an opening family: "Queens Pawn Opening Chigorin Variation" ->
 * "Queens Pawn Chigorin", "Caro Kann Defense" -> "Caro Kann". */
export function shortOpening(name: string): string {
  const short = name
    .split(' ')
    .filter((w) => !['Opening', 'Defense', 'Defence', 'Game', 'Variation', 'Attack', 'System'].includes(w))
    .join(' ')
  return (short || name).slice(0, 24)
}
