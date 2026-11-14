import { describe, expect, it } from 'vitest'
import { axisPosition, capitalize, formatDate, points, sortTimeClasses } from './format'
import { parseRoute } from './routes'

describe('format helpers', () => {
  it('formats score points with sign', () => {
    expect(points(-0.061)).toBe('−6.1')
    expect(points(0.125)).toBe('+12.5')
    expect(points(0)).toBe('±0.0')
  })

  it('capitalizes', () => {
    expect(capitalize('blitz')).toBe('Blitz')
    expect(capitalize('')).toBe('')
  })

  it('formats dates and missing dates', () => {
    expect(formatDate(null)).toBe('never')
    expect(formatDate('2026-11-12T10:00:00')).toMatch(/2026/)
  })

  it('sorts time classes by speed', () => {
    expect(sortTimeClasses(['rapid', 'zzz', 'bullet', 'daily', 'blitz'])).toEqual([
      'bullet',
      'blitz',
      'rapid',
      'daily',
      'zzz',
    ])
  })

  it('maps values onto a clamped axis', () => {
    expect(axisPosition(0, 0.4)).toBe(50)
    expect(axisPosition(-0.4, 0.4)).toBe(0)
    expect(axisPosition(1, 0.4)).toBe(100)
  })

  it('parses hash routes', () => {
    expect(parseRoute('#/players/12')).toEqual({ page: 'player', id: 12 })
    expect(parseRoute('#/')).toEqual({ page: 'players' })
    expect(parseRoute('')).toEqual({ page: 'players' })
  })
})
