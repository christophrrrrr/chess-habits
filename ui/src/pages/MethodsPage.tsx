import { useEffect } from 'react'
import { METHODS } from '../methods'
import { href } from '../routes'

/** Every definition and threshold behind the cards, one section per topic. */
export function MethodsPage({ section }: { section?: string }) {
  // A card links to one section: bring it into view (jsdom in tests has no scrollIntoView).
  useEffect(() => {
    if (section) document.getElementById(`methods-${section}`)?.scrollIntoView?.()
  }, [section])

  return (
    <div className="stack">
      <section className="hero">
        <h2>How it’s measured</h2>
        <p className="muted">
          Every number on a card follows these definitions. A card only makes a claim when the data is strong
          enough, and says so when it is not.
        </p>
        <nav className="methods__toc" aria-label="Sections">
          {METHODS.map((s) => (
            <a key={s.id} href={href({ page: 'methods', section: s.id })}>
              {s.title}
            </a>
          ))}
        </nav>
      </section>
      {METHODS.map((s) => (
        <section
          key={s.id}
          id={`methods-${s.id}`}
          className={
            s.id === section ? 'panel methods__section methods__section--active' : 'panel methods__section'
          }
          aria-labelledby={`methods-${s.id}-title`}
        >
          <h3 id={`methods-${s.id}-title`} className="section-title">
            {s.title}
          </h3>
          <p className="muted">{s.intro}</p>
          <dl className="methods__list">
            {s.entries.map((e) => (
              <div key={e.term} className="methods__entry">
                <dt>{e.term}</dt>
                <dd>{e.text}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </div>
  )
}
