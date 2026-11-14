// How the grandmaster comparison shows its numbers (pure, unit tested).
import type { CompareRow, CompareSide, CompareUnit, CompareVerdict } from './api'
import type { Tone } from './tiles'

/** Suggested grandmasters: active on chess.com with thousands of public games a year. */
export const SUGGESTED_GRANDMASTERS = [
  { username: 'hikaru', name: 'Hikaru Nakamura' },
  { username: 'magnuscarlsen', name: 'Magnus Carlsen' },
  { username: 'fabianocaruana', name: 'Fabiano Caruana' },
  { username: 'firouzja2003', name: 'Alireza Firouzja' },
  { username: 'gmwso', name: 'Wesley So' },
  { username: 'lachesisq', name: 'Ian Nepomniachtchi' },
]

function signed(v: number, digits = 0): string {
  const r = Number(v.toFixed(digits))
  return `${r > 0 ? '+' : r < 0 ? '−' : '±'}${Math.abs(r).toFixed(digits)}`
}

/** One value in its unit: 0.31 share -> "31%", 0.12 points -> "+12 pts", -45.2 elo -> "−45 Elo". */
export function formatValue(unit: CompareUnit, v: number, isDifference = false): string {
  switch (unit) {
    case 'share':
      return isDifference ? `${signed(v * 100)} pts` : `${Math.round(v * 100)}%`
    case 'points':
      return `${signed(v * 100)} pts`
    case 'elo':
      return `${signed(v)} Elo`
    case 'move':
      return isDifference ? `${signed(v)} moves` : `move ${Math.round(v)}`
  }
}

/** "25–37%" for a value, "+20 pts to +26 pts" for a difference, or '' when there is none. */
export function formatInterval(
  unit: CompareUnit,
  side: { ci_low: number | null; ci_high: number | null },
  isDifference = false,
): string {
  if (side.ci_low === null || side.ci_high === null) return ''
  if (unit === 'share' && !isDifference)
    return `${Math.round(side.ci_low * 100)}–${Math.round(side.ci_high * 100)}%`
  return `${formatValue(unit, side.ci_low, true)} to ${formatValue(unit, side.ci_high, true)}`
}

export function formatSide(unit: CompareUnit, side: CompareSide | null): string {
  return side ? formatValue(unit, side.value) : '–'
}

export const VERDICT_TEXT: Record<CompareVerdict, string> = {
  different: 'Clearly different',
  maybe_different: 'Maybe different',
  similar: 'No clear difference',
  not_enough_data: 'Not enough data',
  descriptive: '',
}

/** Green when you do clearly better than the grandmaster, red when clearly worse. */
export function rowTone(row: CompareRow): Tone {
  if (row.verdict !== 'different' || !row.difference || !row.better) return 'neutral'
  const youHigher = row.difference.value > 0
  return youHigher === (row.better === 'higher') ? 'good' : 'bad'
}
