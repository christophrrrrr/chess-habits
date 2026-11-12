import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { clockProfile, contrast, notEnough, requeue, stopLoss } from '../test/fixtures'
import { FindingCard } from './FindingCard'

describe('FindingCard', () => {
  it('shows a contrast with label, Elo effect, interval and detectable size', () => {
    render(<FindingCard finding={contrast} />)
    expect(screen.getByRole('heading', { name: contrast.title })).toBeInTheDocument()
    expect(screen.getByText('Finding')).toBeInTheDocument()
    expect(screen.getByText('−110 Elo')).toBeInTheDocument()
    expect(screen.getByRole('img')).toHaveAccessibleName(/95% interval −164 Elo to −50 Elo/)
    expect(screen.getByText(/smallest effect this data can detect: \+83 Elo/)).toBeInTheDocument()
    expect(screen.getByRole('article')).toHaveClass('finding--bad')
  })

  it('keeps behaviour shares neutral and shows percentage points', () => {
    render(<FindingCard finding={requeue} />)
    expect(screen.getByRole('article')).toHaveClass('finding--neutral')
    expect(screen.getByText('+10.7 pp')).toBeInTheDocument()
  })

  it('hides the bar when there is not enough data', () => {
    render(<FindingCard finding={notEnough} />)
    expect(screen.getByText('Not enough data')).toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(screen.queryByText(/smallest effect/)).not.toBeInTheDocument()
  })

  it('renders the clock profile with tiles, causes, pace and flags', () => {
    render(<FindingCard finding={clockProfile} />)
    expect(screen.getByText('19%')).toBeInTheDocument()
    expect(screen.getByText('77%')).toBeInTheDocument()
    expect(screen.getByText('≥ 45')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /Steady drain 67%/ })).toBeInTheDocument()
    expect(screen.getByRole('table', { name: /Clock left/ })).toHaveTextContent('Losses84%52%22%–')
    expect(screen.getByRole('table', { name: /decided on time/ })).toHaveTextContent('Lost on time459386')
    expect(screen.getByText(/net clock points per 100 games: −3.8/)).toBeInTheDocument()
    expect(screen.queryByText('Profile')).not.toBeInTheDocument()
  })

  it('renders the clock profile without causes for small samples', () => {
    const details = { ...clockProfile.details, time_sinks: {}, early_estimate: true }
    render(<FindingCard finding={{ ...clockProfile, details }} />)
    expect(screen.queryByText(/Main cause/)).not.toBeInTheDocument()
    expect(screen.getByText(/early estimate/)).toBeInTheDocument()
  })

  it('renders the stop-loss rule table', () => {
    render(<FindingCard finding={stopLoss} />)
    expect(screen.getByText('Would have cost you')).toBeInTheDocument()
    expect(screen.getByText('+69 Elo (+20 to +118)')).toBeInTheDocument()
    expect(screen.getByText('Not enough data')).toBeInTheDocument()
  })
})
