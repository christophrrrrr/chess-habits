import { describe, expect, it } from 'vitest'
import { clockProfile, contrast, notEnough, requeue, rule, ruleCheck, stopLoss } from './test/fixtures'
import { findingTile, headline, ruleTile, stripTimeClass } from './tiles'

describe('tiles', () => {
  it('strips the time control from a title', () => {
    expect(stripTimeClass('Rapid: time trouble costs you about 61 Elo')).toBe(
      'Time trouble costs you about 61 Elo',
    )
    expect(stripTimeClass('no prefix here')).toBe('No prefix here')
  })

  it('shows the time-trouble rate for the clock profile', () => {
    expect(findingTile(clockProfile)).toMatchObject({
      name: 'Time trouble',
      value: '19%',
      tone: 'neutral',
      badge: null,
    })
  })

  it('shows a result in Elo, coloured by direction when significant', () => {
    expect(findingTile(contrast)).toMatchObject({
      name: 'Cost of time trouble',
      value: '−110 Elo',
      tone: 'bad',
      badge: { text: 'Finding', kind: 'finding' },
    })
    expect(findingTile({ ...contrast, label: 'no_effect' }).tone).toBe('neutral')
  })

  it('shows both rates for a behaviour share', () => {
    expect(findingTile({ ...requeue, details: { mean_a: 0.33, mean_b: 0.23 } }).value).toBe('33% vs 23%')
    expect(findingTile(requeue).value).toBe('11%')
  })

  it('counts stop-loss rules that would have helped', () => {
    expect(findingTile(stopLoss)).toMatchObject({ value: '0/2', tone: 'neutral' })
  })

  it('shows a dash when there is not enough data', () => {
    expect(findingTile(notEnough)).toMatchObject({ value: '–', badge: { text: 'Not enough data' } })
  })

  it('shows how often a rule was kept, or "too early" without a current check', () => {
    expect(ruleTile(rule, ruleCheck)).toMatchObject({
      value: '93%',
      tone: 'good',
      badge: { text: 'Finding' },
    })
    expect(ruleTile(rule)).toMatchObject({ value: '–', tone: 'neutral', badge: { text: 'Too early' } })
    const stale = { ...ruleCheck, details: { ...ruleCheck.details, adopted_at: '2026-01-01T00:00:00' } }
    expect(ruleTile(rule, stale).value).toBe('–')
  })

  it('picks the largest significant Elo result as the headline', () => {
    const big = { ...contrast, id: 9, effect: -0.3 }
    expect(headline([contrast, big, clockProfile, requeue])?.id).toBe(9)
    expect(headline([clockProfile])).toBeUndefined()
  })
})
