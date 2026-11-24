import type { RefObject } from 'react'
import { boardFromFen, squareName } from '../gaze/model'

/** A plain chess board from a FEN. Black at the bottom with `flip`; optional heat per 2x2 block
 * (16 values) and highlighted squares (e.g. the best move's from and to squares). */
export function Board({
  fen,
  boardRef,
  picked,
  onSquare,
  heat,
  flip = false,
  highlight = [],
  label,
}: {
  fen: string
  boardRef?: RefObject<HTMLDivElement | null>
  picked?: string | null
  onSquare?: (sq: string) => void
  heat?: number[]
  flip?: boolean
  highlight?: string[]
  label?: string
}) {
  const pieces = boardFromFen(fen) // rank 8 first, a to h
  const max = heat ? Math.max(...heat, 1e-9) : 1
  const order = flip ? [...pieces.keys()].reverse() : [...pieces.keys()]
  return (
    <div className="board" ref={boardRef} role={onSquare ? undefined : 'img'} aria-label={label}>
      {order.map((i) => {
        const piece = pieces[i]
        const file = i % 8
        const rank = 7 - Math.floor(i / 8)
        const sq = squareName([file, rank])
        const dark = (file + rank) % 2 === 0
        const region = Math.floor(rank / 2) * 4 + Math.floor(file / 2)
        const cls = [
          'board__sq',
          dark ? 'board__sq--dark' : 'board__sq--light',
          picked === sq ? 'board__sq--picked' : '',
          highlight.includes(sq) ? 'board__sq--hl' : '',
        ]
          .filter(Boolean)
          .join(' ')
        return (
          <button
            key={sq}
            className={cls}
            onClick={onSquare ? () => onSquare(sq) : undefined}
            disabled={!onSquare}
            aria-label={`${sq}${piece ? ` ${piece}` : ''}`}
          >
            {heat && <span className="board__heat" style={{ opacity: (heat[region] / max) * 0.75 }} />}
            <span className="board__piece">{piece}</span>
          </button>
        )
      })}
    </div>
  )
}
