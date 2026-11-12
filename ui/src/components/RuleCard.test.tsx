import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { RuleDraft } from '../api'
import { clockProfile, rule, ruleCheck, stopLoss } from '../test/fixtures'
import { FindingCard } from './FindingCard'
import { RuleCard } from './RuleCard'

describe('RuleCard', () => {
  it('shows adherence, baseline, time trouble and the kept/broken strip', () => {
    render(<RuleCard rule={rule} check={ruleCheck} onRetire={vi.fn()} />)
    expect(screen.getByRole('heading', { name: ruleCheck.title })).toBeInTheDocument()
    expect(screen.getByText('Finding')).toBeInTheDocument()
    expect(screen.getByRole('article')).toHaveClass('finding--good')
    expect(screen.getByText('93%')).toBeInTheDocument()
    expect(screen.getByText('595 of 640 games')).toBeInTheDocument()
    expect(screen.getByText('18% → 21%')).toBeInTheDocument()
    expect(screen.getByRole('img')).toHaveAccessibleName('Last 3 games: kept 2, broken 1')
  })

  it('says "too early" before the first check and lets the player stop tracking', async () => {
    const onRetire = vi.fn().mockResolvedValue(undefined)
    render(<RuleCard rule={rule} onRetire={onRetire} />)
    expect(screen.getByText('Too early')).toBeInTheDocument()
    expect(screen.getByText(/Progress shows after your next import and analysis/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Stop tracking' }))
    expect(onRetire).toHaveBeenCalledWith(rule)
  })

  it('ignores a check made for an older threshold and shows retire errors', async () => {
    const stale = { ...ruleCheck, details: { ...ruleCheck.details, adopted_at: '2026-09-01T00:00:00' } }
    const onRetire = vi.fn().mockRejectedValue(new Error('insights is down'))
    render(<RuleCard rule={rule} check={stale} onRetire={onRetire} />)
    expect(screen.getByRole('heading', { name: `Your rule: ${rule.description}` })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Stop tracking' }))
    expect(await screen.findByText('insights is down')).toBeInTheDocument()
  })

  it('shows games played past the stop for a stop-loss rule', () => {
    const stop = {
      ...rule,
      kind: 'stop_loss' as const,
      move: null,
      min_share: null,
      stop_rule: 'two_in_a_row',
    }
    const check = {
      ...ruleCheck,
      label: 'not_enough_data' as const,
      details: { ...ruleCheck.details, trouble: undefined, games_past_stop: { before: 80, after: 3 } },
    }
    render(<RuleCard rule={stop} check={check} onRetire={vi.fn()} />)
    expect(screen.getByText('80 → 3')).toBeInTheDocument()
    expect(screen.getByText('Too early')).toBeInTheDocument()
    expect(screen.getByRole('img')).toHaveAccessibleName(/Last 3 sessions/)
  })
})

describe('adopting a rule from a card', () => {
  it('adopts the suggested clock checkpoint', async () => {
    const adopt = vi.fn().mockResolvedValue(undefined)
    render(<FindingCard finding={clockProfile} actions={{ rules: [], adopt }} />)
    expect(
      screen.getByText(/Suggested rule: keep at least 45% of your clock after move 20/),
    ).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Adopt this rule' }))
    expect(adopt).toHaveBeenCalledWith({
      time_class: 'bullet',
      kind: 'clock_checkpoint',
      move: 20,
      min_share: 0.45,
    } satisfies RuleDraft)
  })

  it('shows "tracking" for the adopted rule and blocks a second one of the same kind', () => {
    const { unmount } = render(
      <FindingCard finding={clockProfile} actions={{ rules: [rule], adopt: vi.fn() }} />,
    )
    expect(screen.getByText('Tracking ✓')).toBeInTheDocument()
    unmount()
    const other = { ...rule, min_share: 0.3, description: 'Keep at least 30% of your clock after move 20' }
    render(<FindingCard finding={clockProfile} actions={{ rules: [other], adopt: vi.fn() }} />)
    expect(screen.getByRole('button', { name: 'Adopt this rule' })).toBeDisabled()
  })

  it('adopts a stop-loss rule from the table and reports errors', async () => {
    const adopt = vi.fn().mockRejectedValue(new Error('already tracking one'))
    render(<FindingCard finding={stopLoss} actions={{ rules: [], adopt }} />)
    const buttons = screen.getAllByRole('button', { name: 'Adopt' })
    expect(buttons).toHaveLength(2)
    await userEvent.click(buttons[0])
    expect(adopt).toHaveBeenCalledWith({ time_class: 'bullet', kind: 'stop_loss', stop_rule: 'two_in_a_row' })
    await waitFor(() => expect(screen.getByText('already tracking one')).toBeInTheDocument())
  })

  it('shows no adopt buttons without actions', () => {
    render(<FindingCard finding={stopLoss} />)
    expect(screen.queryByRole('button', { name: 'Adopt' })).not.toBeInTheDocument()
  })
})
