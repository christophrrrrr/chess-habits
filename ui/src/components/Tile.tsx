export function Tile({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="tile">
      <div className="tile__value">{value}</div>
      <div className="tile__label">{label}</div>
      {note && <div className="tile__note">{note}</div>}
    </div>
  )
}
