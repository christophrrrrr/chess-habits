import { useEffect, useState } from 'react'
import { PlayerPage } from './pages/PlayerPage'
import { PlayersPage } from './pages/PlayersPage'
import { parseRoute } from './routes'

export default function App() {
  const [route, setRoute] = useState(() => parseRoute(window.location.hash))

  useEffect(() => {
    const onChange = () => setRoute(parseRoute(window.location.hash))
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  return (
    <>
      <header className="topbar">
        <a href="#/" className="brand">
          <span className="brand__mark" aria-hidden="true" />
          Kiebitz
        </a>
        <span className="muted small">the onlooker who tells you how you play</span>
      </header>
      <main className="container">
        {route.page === 'player' ? <PlayerPage playerId={route.id} key={route.id} /> : <PlayersPage />}
      </main>
    </>
  )
}
