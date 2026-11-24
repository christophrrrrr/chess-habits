// Small SVG charts for the finding cards. No chart library: three forms cover every card.
//   LineChart       change along moves or months, up to 3 series, crosshair + tooltip
//   ColumnChart     counts or shares per bucket, 1-2 series, tooltip per column
//   IntervalChart   an estimate with its 95% interval per row, around a zero line
// Colors are the validated --series-* tokens; text always uses text tokens. Every chart has
// a table view under "Show as table", so nothing depends on seeing the marks.
import { useEffect, useId, useRef, useState, type PointerEvent, type ReactNode, type RefObject } from 'react'

const DEFAULT_WIDTH = 640

/** The plot's real width in CSS pixels, so text and marks keep their size on any screen. */
function useWidth(): [RefObject<HTMLDivElement | null>, number] {
  const ref = useRef<HTMLDivElement | null>(null)
  const [width, setWidth] = useState(DEFAULT_WIDTH)
  useEffect(() => {
    const el = ref.current
    if (!el || typeof ResizeObserver === 'undefined') return
    const measure = () => el.clientWidth > 0 && setWidth(Math.max(260, Math.round(el.clientWidth)))
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return [ref, width]
}

/** Show every n-th label so labels of about `chars` characters never overlap. */
function labelStep(count: number, room: number, chars: number): number {
  return Math.max(1, Math.ceil(count / Math.max(1, Math.floor(room / (chars * 6.5 + 10)))))
}
const PAD = { top: 16, right: 16, bottom: 30, left: 48 }
const SERIES = ['var(--series-1)', 'var(--series-2)', 'var(--series-3)']

export interface Series {
  name: string
  values: Array<number | null>
}

function niceTicks(lo: number, hi: number, count = 4): number[] {
  if (hi <= lo) hi = lo + 1
  const raw = (hi - lo) / count
  const mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? raw
  const out = []
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(+v.toFixed(10))
  return out
}

function Legend({ series }: { series: string[] }) {
  if (series.length < 2) return null
  return (
    <ul className="chart__legend">
      {series.map((name, i) => (
        <li key={name}>
          <span className="chart__key" style={{ background: SERIES[i] }} aria-hidden="true" />
          {name}
        </li>
      ))}
    </ul>
  )
}

function TableView({ head, rows }: { head: string[]; rows: Array<Array<string | number>> }) {
  return (
    <details className="chart__table">
      <summary>Show as table</summary>
      <table className="mini">
        <thead>
          <tr>
            {head.map((h) => (
              <th key={h} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {r.map((c, j) =>
                j === 0 ? (
                  <th key={j} scope="row">
                    {c}
                  </th>
                ) : (
                  <td key={j}>{c}</td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  )
}

function Frame({
  title,
  note,
  legend,
  children,
  table,
  plotRef,
}: {
  title: string
  note?: string
  legend?: string[]
  children: ReactNode
  table: ReactNode
  plotRef: RefObject<HTMLDivElement | null>
}) {
  return (
    <figure className="chart">
      <figcaption>
        <span className="chart__title">{title}</span>
        {note && <span className="chart__note">{note}</span>}
      </figcaption>
      {legend && <Legend series={legend} />}
      <div className="chart__plot" ref={plotRef}>
        {children}
      </div>
      {table}
    </figure>
  )
}

const dash = (v: number | null, fmt: (v: number) => string) => (v === null ? '–' : fmt(v))

export function LineChart({
  title,
  note,
  x,
  xLabel,
  series,
  format,
  yMin,
  yMax,
  height = 220,
  marker,
}: {
  title: string
  note?: string
  x: Array<number | string>
  xLabel: string
  series: Series[]
  format: (v: number) => string
  yMin?: number
  yMax?: number
  height?: number
  /** A vertical reference line at this x value, e.g. the suggested checkpoint move. */
  marker?: { at: number | string; label: string }
}) {
  const [hover, setHover] = useState<number | null>(null)
  const [plotRef, W] = useWidth()
  const values = series.flatMap((s) => s.values).filter((v): v is number => v !== null)
  if (values.length === 0) return null
  const lo = yMin ?? Math.min(0, ...values)
  const hi = yMax ?? Math.max(...values)
  const ticks = niceTicks(lo, hi)
  const top = Math.max(hi, ticks[ticks.length - 1])
  const bottom = Math.min(lo, ticks[0])
  const iw = W - PAD.left - PAD.right
  const ih = height - PAD.top - PAD.bottom
  const sx = (i: number) => PAD.left + (x.length === 1 ? iw / 2 : (i / (x.length - 1)) * iw)
  const sy = (v: number) => PAD.top + ih - ((v - bottom) / (top - bottom || 1)) * ih
  const every = labelStep(x.length, iw, Math.max(...x.map((v) => String(v).length)))
  const markerIndex = marker ? x.indexOf(marker.at) : -1

  function path(vals: Array<number | null>) {
    let d = ''
    let pen = false
    vals.forEach((v, i) => {
      if (v === null) {
        pen = false
        return
      }
      d += `${pen ? 'L' : 'M'}${sx(i).toFixed(1)},${sy(v).toFixed(1)}`
      pen = true
    })
    return d
  }

  function onMove(e: PointerEvent<SVGRectElement>) {
    const box = e.currentTarget.getBoundingClientRect()
    const px = ((e.clientX - box.left) / box.width) * iw
    setHover(Math.max(0, Math.min(x.length - 1, Math.round((px / iw) * (x.length - 1)))))
  }

  const tip = hover !== null && (
    <div
      className="chart__tip"
      style={{ left: `${(sx(hover) / W) * 100}%`, top: 0 }}
      role="status"
      aria-live="polite"
    >
      <strong>
        {xLabel} {x[hover]}
      </strong>
      {series.map((s, i) => (
        <span key={s.name}>
          <span className="chart__key" style={{ background: SERIES[i] }} aria-hidden="true" />
          {s.name}: {dash(s.values[hover], format)}
        </span>
      ))}
    </div>
  )

  return (
    <Frame
      plotRef={plotRef}
      title={title}
      note={note}
      legend={series.map((s) => s.name)}
      table={
        <TableView
          head={[xLabel, ...series.map((s) => s.name)]}
          rows={x.map((xv, i) => [xv, ...series.map((s) => dash(s.values[i], format))])}
        />
      }
    >
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label={title}>
        {ticks.map((t) => (
          <g key={t}>
            <line className="chart__grid" x1={PAD.left} x2={W - PAD.right} y1={sy(t)} y2={sy(t)} />
            <text className="chart__axis" x={PAD.left - 6} y={sy(t)} dy="0.32em" textAnchor="end">
              {format(t)}
            </text>
          </g>
        ))}
        {x.map((xv, i) =>
          i % every === 0 || i === x.length - 1 ? (
            <text key={i} className="chart__axis" x={sx(i)} y={height - 8} textAnchor="middle">
              {xv}
            </text>
          ) : null,
        )}
        {markerIndex >= 0 && (
          <g>
            <line
              className="chart__marker"
              x1={sx(markerIndex)}
              x2={sx(markerIndex)}
              y1={PAD.top}
              y2={PAD.top + ih}
            />
            <text className="chart__axis" x={sx(markerIndex) + 4} y={PAD.top + 10}>
              {marker!.label}
            </text>
          </g>
        )}
        {series.map((s, i) => (
          <path key={s.name} d={path(s.values)} className="chart__line" style={{ stroke: SERIES[i] }} />
        ))}
        {hover !== null && (
          <g>
            <line className="chart__cross" x1={sx(hover)} x2={sx(hover)} y1={PAD.top} y2={PAD.top + ih} />
            {series.map((s, i) =>
              s.values[hover] === null ? null : (
                <circle
                  key={s.name}
                  className="chart__dot"
                  cx={sx(hover)}
                  cy={sy(s.values[hover]!)}
                  r={4}
                  style={{ fill: SERIES[i] }}
                />
              ),
            )}
          </g>
        )}
        <rect
          x={PAD.left}
          y={PAD.top}
          width={iw}
          height={ih}
          fill="transparent"
          onPointerMove={onMove}
          onPointerLeave={() => setHover(null)}
        />
      </svg>
      {tip}
    </Frame>
  )
}

export function ColumnChart({
  title,
  note,
  categories,
  series,
  format,
  height = 200,
}: {
  title: string
  note?: string
  categories: string[]
  series: Series[]
  format: (v: number) => string
  height?: number
}) {
  const [hover, setHover] = useState<number | null>(null)
  const [plotRef, W] = useWidth()
  const values = series.flatMap((s) => s.values).filter((v): v is number => v !== null)
  if (values.length === 0) return null
  const ticks = niceTicks(0, Math.max(...values))
  const top = Math.max(...values, ticks[ticks.length - 1])
  const iw = W - PAD.left - PAD.right
  const ih = height - PAD.top - PAD.bottom
  const band = iw / categories.length
  const barW = Math.min(24, (band - 8) / series.length - 2)
  const sy = (v: number) => PAD.top + ih - (v / (top || 1)) * ih
  const every = labelStep(categories.length, iw, Math.max(...categories.map((c) => c.length)))

  return (
    <Frame
      plotRef={plotRef}
      title={title}
      note={note}
      legend={series.map((s) => s.name)}
      table={
        <TableView
          head={['', ...series.map((s) => s.name)]}
          rows={categories.map((c, i) => [c, ...series.map((s) => dash(s.values[i], format))])}
        />
      }
    >
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label={title}>
        {ticks.map((t) => (
          <g key={t}>
            <line className="chart__grid" x1={PAD.left} x2={W - PAD.right} y1={sy(t)} y2={sy(t)} />
            <text className="chart__axis" x={PAD.left - 6} y={sy(t)} dy="0.32em" textAnchor="end">
              {format(t)}
            </text>
          </g>
        ))}
        {categories.map((c, ci) => {
          const x0 = PAD.left + ci * band + (band - series.length * (barW + 2)) / 2
          return (
            <g
              key={c}
              onPointerEnter={() => setHover(ci)}
              onPointerLeave={() => setHover(null)}
              className={hover === ci ? 'chart__band chart__band--on' : 'chart__band'}
            >
              <rect x={PAD.left + ci * band} y={PAD.top} width={band} height={ih} fill="transparent" />
              {series.map((s, si) => {
                const v = s.values[ci]
                if (v === null || v <= 0) return null
                const y = sy(v)
                const h = PAD.top + ih - y
                const r = Math.min(4, h, barW / 2)
                const bx = x0 + si * (barW + 2)
                // Rounded data end, square at the baseline.
                const d = `M${bx},${PAD.top + ih}V${y + r}Q${bx},${y} ${bx + r},${y}H${bx + barW - r}Q${bx + barW},${y} ${bx + barW},${y + r}V${PAD.top + ih}Z`
                return <path key={s.name} d={d} style={{ fill: SERIES[si] }} />
              })}
              {(ci % every === 0 || ci === categories.length - 1) && (
                <text
                  className="chart__axis"
                  x={PAD.left + ci * band + band / 2}
                  y={height - 8}
                  textAnchor="middle"
                >
                  {c}
                </text>
              )}
            </g>
          )
        })}
        <line className="chart__base" x1={PAD.left} x2={W - PAD.right} y1={PAD.top + ih} y2={PAD.top + ih} />
      </svg>
      {hover !== null && (
        <div
          className="chart__tip"
          style={{ left: `${((PAD.left + (hover + 0.5) * band) / W) * 100}%`, top: 0 }}
          role="status"
          aria-live="polite"
        >
          <strong>{categories[hover]}</strong>
          {series.map((s, i) => (
            <span key={s.name}>
              {series.length > 1 && (
                <span className="chart__key" style={{ background: SERIES[i] }} aria-hidden="true" />
              )}
              {series.length > 1 ? `${s.name}: ` : ''}
              {dash(s.values[hover], format)}
            </span>
          ))}
        </div>
      )}
    </Frame>
  )
}

export interface IntervalRow {
  label: string
  value: number | null
  low: number | null
  high: number | null
  note?: string
  /** "bad" / "good" when the row is a clear result; drawn darker, never by color alone. */
  verdict?: 'bad' | 'good' | null
}

/** Estimates with 95% intervals around zero, one row each (e.g. Elo by game in the session). */
export function IntervalChart({
  title,
  note,
  rows,
  format,
  range,
  domain,
  reference,
}: {
  title: string
  note?: string
  rows: IntervalRow[]
  format: (v: number) => string
  /** Half-width of an axis centred on zero; defaults to fit the widest interval. */
  range?: number
  /** A fixed axis instead, e.g. [0, 1] for rates. */
  domain?: [number, number]
  /** A dashed reference line, e.g. the overall rate. */
  reference?: { value: number; label: string }
}) {
  const id = useId()
  const [plotRef, W] = useWidth()
  const shown = rows.filter((r) => r.value !== null)
  if (shown.length === 0) return null
  const extent =
    range ?? Math.max(...shown.flatMap((r) => [Math.abs(r.low ?? r.value!), Math.abs(r.high ?? r.value!)]), 1)
  const ticks = domain ? niceTicks(domain[0], domain[1], 4) : niceTicks(-extent, extent, 4)
  const span = Math.max(Math.abs(ticks[0]), Math.abs(ticks[ticks.length - 1]), extent)
  const [lo, hi] = domain ?? [-span, span]
  const LEFT = Math.round(Math.min(160, W * 0.36))
  const rowH = 30
  const height = PAD.top + rows.length * rowH + PAD.bottom
  const iw = W - LEFT - PAD.right
  const sx = (v: number) => LEFT + ((Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo || 1)) * iw

  return (
    <Frame
      plotRef={plotRef}
      title={title}
      note={note}
      table={
        <TableView
          head={['', 'Estimate', '95% interval', '']}
          rows={rows.map((r) => [
            r.label,
            dash(r.value, format),
            r.low === null || r.high === null ? '–' : `${format(r.low)} to ${format(r.high)}`,
            r.note ?? '',
          ])}
        />
      }
    >
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-labelledby={id}>
        <title id={id}>{title}</title>
        {reference && (
          <g>
            <line
              className="chart__marker"
              x1={sx(reference.value)}
              x2={sx(reference.value)}
              y1={PAD.top - 6}
              y2={height - PAD.bottom}
            />
            <text className="chart__axis" x={sx(reference.value) + 4} y={PAD.top - 8}>
              {reference.label}
            </text>
          </g>
        )}
        {ticks.map((t) => (
          <g key={t}>
            <line
              className={t === 0 && !domain ? 'chart__zero' : 'chart__grid'}
              x1={sx(t)}
              x2={sx(t)}
              y1={PAD.top}
              y2={height - PAD.bottom}
            />
            <text className="chart__axis" x={sx(t)} y={height - 8} textAnchor="middle">
              {format(t)}
            </text>
          </g>
        ))}
        {rows.map((r, i) => {
          const cy = PAD.top + i * rowH + rowH / 2
          return (
            <g key={r.label}>
              <title>
                {r.label}: {dash(r.value, format)}
                {r.low !== null && r.high !== null ? ` (95% CI ${format(r.low)} to ${format(r.high)})` : ''}
                {r.note ? ` · ${r.note}` : ''}
              </title>
              <text className="chart__label" x={LEFT - 10} y={cy} dy="0.32em" textAnchor="end">
                {r.label}
              </text>
              {r.value !== null && r.low !== null && r.high !== null && (
                <line className="chart__ci" x1={sx(r.low)} x2={sx(r.high)} y1={cy} y2={cy} />
              )}
              {r.value !== null && (
                <circle
                  className={`chart__dot chart__dot--${r.verdict ?? 'plain'}`}
                  cx={sx(r.value)}
                  cy={cy}
                  r={5}
                />
              )}
            </g>
          )
        })}
      </svg>
    </Frame>
  )
}
