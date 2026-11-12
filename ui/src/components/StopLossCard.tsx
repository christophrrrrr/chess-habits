import type { Finding } from '../api'
import { AdoptButton, type RuleActions } from './AdoptButton'
import { CardHeader } from './CardHeader'

interface RuleRow {
  rule: string
  name: string
  skipped_games: number
  difference_elo: number | null
  ci_elo: [number, number] | null
  verdict: 'helps' | 'costs' | 'no_difference' | 'not_enough_data'
}

const VERDICT: Record<RuleRow['verdict'], string> = {
  helps: 'Would have helped',
  costs: 'Would have cost you',
  no_difference: 'No clear difference',
  not_enough_data: 'Not enough data',
}

function signed(x: number): string {
  const v = Math.round(x)
  return `${v > 0 ? '+' : v < 0 ? '−' : '±'}${Math.abs(v)}`
}

export function StopLossCard({ finding, actions }: { finding: Finding; actions?: RuleActions }) {
  const rules = (finding.details.rules ?? []) as RuleRow[]
  return (
    <article className="finding finding--profile" aria-label={finding.title}>
      <CardHeader finding={finding} />
      <p className="finding__summary">{finding.summary}</p>
      <div className="table-wrap">
        <table className="mini">
          <caption>Games each rule would have skipped, compared with your other games</caption>
          <thead>
            <tr>
              <th scope="col">Rule</th>
              <th scope="col">Skipped games</th>
              <th scope="col">Their level vs. the rest</th>
              <th scope="col">Verdict</th>
              {actions && <th scope="col">Track it</th>}
            </tr>
          </thead>
          <tbody>
            {rules.map((r) => (
              <tr key={r.rule}>
                <th scope="row">{r.name}</th>
                <td>{r.skipped_games}</td>
                <td>
                  {r.difference_elo === null
                    ? '–'
                    : `${signed(r.difference_elo)} Elo (${signed(r.ci_elo![0])} to ${signed(r.ci_elo![1])})`}
                </td>
                <td className={`verdict verdict--${r.verdict}`}>{VERDICT[r.verdict]}</td>
                {actions && (
                  <td>
                    <AdoptButton
                      actions={actions}
                      compact
                      draft={{ time_class: finding.time_class, kind: 'stop_loss', stop_rule: r.rule }}
                    />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <footer className="finding__foot">Based on {finding.sample_size} games played in sessions</footer>
    </article>
  )
}
