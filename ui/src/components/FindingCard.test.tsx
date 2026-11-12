import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Finding } from '../api'
import { FindingCard } from './FindingCard'

const base: Finding = {
  id: 1,
  analysis_key: 'time_trouble',
  time_class: 'blitz',
  title: 'Blitz: time trouble costs you points (22% of games)',
  summary: 'Your clock drops below 10%...',
  effect: -0.25,
  ci_low: -0.35,
  ci_high: -0.14,
  sample_size: 437,
  confidence: 'high',
  details: {},
}

describe('FindingCard', () => {
  it('shows title, evidence label, effect and sample size', () => {
    render(<FindingCard finding={base} />)
    expect(screen.getByRole('heading', { name: base.title })).toBeInTheDocument()
    expect(screen.getByText('Strong evidence')).toBeInTheDocument()
    expect(screen.getByText('−25.0')).toBeInTheDocument()
    expect(screen.getByText('Based on 437 games')).toBeInTheDocument()
    expect(screen.getByRole('article')).toHaveClass('finding--bad')
  })

  it('hides the effect bar when there are not enough games', () => {
    render(<FindingCard finding={{ ...base, confidence: 'insufficient' }} />)
    expect(screen.getByText('Not enough games')).toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(screen.getByRole('article')).toHaveClass('finding--neutral')
  })

  it('marks a significant positive effect as good', () => {
    render(<FindingCard finding={{ ...base, effect: 0.1, ci_low: 0.02, ci_high: 0.18 }} />)
    expect(screen.getByRole('article')).toHaveClass('finding--good')
  })
})
