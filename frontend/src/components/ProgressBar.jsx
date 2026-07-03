export default function ProgressBar({ percent = 0, big = false }) {
  const pct = Math.max(0, Math.min(100, percent))
  return (
    <div className={`bar ${big ? 'bar--big' : ''}`}>
      <div className="bar__fill" style={{ width: `${pct}%` }} />
      {big && <span className="bar__text">{pct.toFixed(1)}%</span>}
    </div>
  )
}
