import { useState } from 'react'
import type { Rule, RuleDraft } from '../api'

/** What a card needs to let the player adopt one of its suggestions as a rule. */
export interface RuleActions {
  rules: Rule[]
  adopt: (draft: RuleDraft) => Promise<void>
}

function sameRule(rule: Rule, draft: RuleDraft): boolean {
  return draft.kind === 'stop_loss'
    ? rule.stop_rule === draft.stop_rule
    : rule.move === draft.move && rule.min_share === draft.min_share
}

/** "Adopt this rule", or the state if a rule of this kind is already tracked. */
export function AdoptButton({
  actions,
  draft,
  compact = false,
}: {
  actions: RuleActions
  draft: RuleDraft
  compact?: boolean
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const active = actions.rules.find((r) => r.time_class === draft.time_class && r.kind === draft.kind)

  if (active && sameRule(active, draft)) return <span className="tracking">Tracking ✓</span>

  async function adopt() {
    setBusy(true)
    setError(null)
    try {
      await actions.adopt(draft)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const blocked = active !== undefined
  return (
    <span className="adopt">
      <button
        className={compact ? 'small' : undefined}
        onClick={adopt}
        disabled={busy || blocked}
        title={blocked ? `You already track “${active.description}”. Stop tracking it first.` : undefined}
      >
        {busy ? 'Adopting…' : compact ? 'Adopt' : 'Adopt this rule'}
      </button>
      {error && <span className="error">{error}</span>}
    </span>
  )
}
