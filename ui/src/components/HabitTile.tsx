import { Lock } from 'lucide-react'
import type { TileModel } from '../tiles'
import { TileIcon } from './TileIcon'

/** A big clickable tile: icon, headline number, what it means. Opens the full card. */
export function HabitTile({ tile, icon, to }: { tile: TileModel; icon: string; to: string }) {
  return (
    <a href={to} className={`habit habit--${tile.tone}`}>
      <span className="habit__top">
        <span className="habit__icon">
          <TileIcon name={icon} />
        </span>
        <span className="habit__name">{tile.name}</span>
      </span>
      <span className="habit__mid">
        <span className="habit__value">{tile.value}</span>
        {tile.badge && <span className={`badge badge--${tile.badge.kind}`}>{tile.badge.text}</span>}
      </span>
      <span className="habit__caption">{tile.caption}</span>
    </a>
  )
}

/** A greyed-out tile for something on the roadmap. */
export function ComingSoonTile({ icon, name, caption }: { icon: string; name: string; caption: string }) {
  return (
    <div className="habit habit--soon" aria-disabled="true">
      <span className="habit__top">
        <span className="habit__icon">
          <TileIcon name={icon} />
        </span>
        <span className="habit__name">{name}</span>
      </span>
      <span className="habit__mid">
        <span className="badge badge--soon">
          <Lock size={12} aria-hidden="true" /> Coming soon
        </span>
      </span>
      <span className="habit__caption">{caption}</span>
    </div>
  )
}
