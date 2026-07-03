import ProgressBar from './ProgressBar.jsx'

const pct = (p) => (p && p.total ? (p.done / p.total) * 100 : 0)

export default function SourceCard({ source, sel, onChange, progress, disabledAll }) {
  const unavailable = !source.minDate
  const on = sel.enabled && !unavailable

  return (
    <div className={`card ${on ? 'card--on' : ''}`}>
      <div className="card__head">
        <label className="chk">
          <input
            type="checkbox"
            checked={sel.enabled}
            disabled={unavailable || disabledAll}
            onChange={(e) => onChange({ enabled: e.target.checked })}
          />
          <span className="card__name">{source.name}</span>
        </label>
        <span className="badge">#{source.num}</span>
      </div>

      <div className="card__range">
        {unavailable
          ? '사용 불가'
          : `가능 기간  ${source.minDate} ~ ${source.maxDate}`}
      </div>

      <div className="card__dates">
        <label>
          시작일
          <input
            type="date"
            value={sel.start || ''}
            min={source.minDate || undefined}
            max={source.maxDate || undefined}
            disabled={!on || disabledAll}
            onChange={(e) => onChange({ start: e.target.value })}
          />
        </label>
        <label>
          종료일
          <input
            type="date"
            value={sel.end || ''}
            min={source.minDate || undefined}
            max={source.maxDate || undefined}
            disabled={!on || disabledAll}
            onChange={(e) => onChange({ end: e.target.value })}
          />
        </label>
      </div>

      {progress && progress.total > 0 && (
        <div className="card__prog">
          <ProgressBar percent={pct(progress)} />
          <div className="card__progmeta">
            {progress.current ? (
              <span className="dot" />
            ) : null}
            {progress.current ? `${progress.current} 처리 중` : '완료'} ·
            저장 {progress.saved} / 건너뜀 {progress.skipped} / 실패 {progress.failed}
            {'  '}({progress.done}/{progress.total})
          </div>
          {progress.error && <div className="card__err">{progress.error}</div>}
        </div>
      )}
    </div>
  )
}
