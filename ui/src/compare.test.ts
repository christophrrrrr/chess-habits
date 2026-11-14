import { describe, expect, it } from 'vitest'
import type { CompareRow } from './api'
import { formatInterval, formatSide, formatValue, rowTone } from './compare'

const row = (patch: Partial<CompareRow>): CompareRow => ({
  key: 'time_trouble',
  name: 'Games with time trouble',
  unit: 'share',
  better: 'lower',
  you: { value: 0.31, ci_low: 0.28, ci_high: 0.34, n: 900 },
  reference: { value: 0.08, ci_low: 0.07, ci_high: 0.09, n: 4000 },
  difference: { value: 0.23, ci_low: 0.2, ci_high: 0.26 },
  q_value: 0.001,
  verdict: 'different',
  ...patch,
})

describe('grandmaster comparison formatting', () => {
  it('formats values in their unit', () => {
    expect(formatValue('share', 0.314)).toBe('31%')
    expect(formatValue('share', 0.23, true)).toBe('+23 pts')
    expect(formatValue('points', -0.05)).toBe('−5 pts')
    expect(formatValue('elo', -45.4)).toBe('−45 Elo')
    expect(formatValue('elo', 0.2)).toBe('±0 Elo')
    expect(formatValue('move', 31.4)).toBe('move 31')
    expect(formatValue('move', -3, true)).toBe('−3 moves')
    expect(formatSide('share', null)).toBe('–')
  })

  it('formats intervals', () => {
    expect(formatInterval('share', { ci_low: 0.28, ci_high: 0.34 })).toBe('28–34%')
    expect(formatInterval('elo', { ci_low: -60, ci_high: 12 })).toBe('−60 Elo to +12 Elo')
    expect(formatInterval('share', { ci_low: 0.2, ci_high: 0.26 }, true)).toBe('+20 pts to +26 pts')
    expect(formatInterval('move', { ci_low: null, ci_high: null })).toBe('')
  })

  it('colours only clear differences, by which direction is better', () => {
    expect(rowTone(row({}))).toBe('bad')
    expect(rowTone(row({ difference: { value: -0.1, ci_low: -0.2, ci_high: -0.05 } }))).toBe('good')
    expect(rowTone(row({ better: 'higher', unit: 'elo' }))).toBe('good')
    expect(rowTone(row({ verdict: 'similar' }))).toBe('neutral')
    expect(rowTone(row({ better: null }))).toBe('neutral')
  })
})
