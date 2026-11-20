import type { Finding } from '../api'
import { LABEL_TEXT } from '../format'
import { methodsSectionFor } from '../methods'
import { MethodsLink } from './MethodsLink'

export function CardHeader({ finding }: { finding: Finding }) {
  return (
    <header className="finding__head">
      <h4>{finding.title}</h4>
      <span className="finding__meta">
        {finding.label !== 'profile' && (
          <span className={`badge badge--${finding.label}`}>{LABEL_TEXT[finding.label]}</span>
        )}
        <MethodsLink section={methodsSectionFor(finding.analysis_key)} />
      </span>
    </header>
  )
}
