import type { Finding } from '../api'
import { LABEL_TEXT } from '../format'

export function CardHeader({ finding }: { finding: Finding }) {
  return (
    <header className="finding__head">
      <h4>{finding.title}</h4>
      {finding.label !== 'profile' && (
        <span className={`badge badge--${finding.label}`}>{LABEL_TEXT[finding.label]}</span>
      )}
    </header>
  )
}
