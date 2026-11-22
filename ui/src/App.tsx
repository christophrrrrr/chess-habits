import { useEffect, useState } from 'react'
import { SLOW_EVENT } from './api'
import { MethodsPage } from './pages/MethodsPage'
import { PlayerPage } from './pages/PlayerPage'
import { PlayersPage } from './pages/PlayersPage'
import { parseRoute } from './routes'

export default function App() {
  const [route, setRoute] = useState(() => parseRoute(window.location.hash))
  const [slow, setSlow] = useState(0)

  useEffect(() => {
    const onSlow = (e: Event) => setSlow((e as CustomEvent<number>).detail)
    window.addEventListener(SLOW_EVENT, onSlow)
    return () => window.removeEventListener(SLOW_EVENT, onSlow)
  }, [])

  useEffect(() => {
    const onChange = () => {
      setRoute(parseRoute(window.location.hash))
      document.documentElement.scrollTop = 0
    }
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  return (
    <>
      <header className="topbar">
        <a href="#/" className="brand">
          <span className="brand__mark" aria-hidden="true" />
          Chess Habits
        </a>
        <span className="muted small">your habits at the board, measured</span>
        <a href="#/methods" className="topbar__link small">
          How it’s measured
        </a>
      </header>
      {slow > 0 && (
        <div className="wake-banner" role="status">
          Waking up the servers. They sleep when nobody uses them, so the first request can take up to a
          minute.
        </div>
      )}
      <main className="container">
        {route.page === 'player' ? (
          <PlayerPage playerId={route.id} view={route} key={route.id} />
        ) : route.page === 'methods' ? (
          <MethodsPage section={route.section} />
        ) : (
          <PlayersPage />
        )}
      </main>
    </>
  )
}
