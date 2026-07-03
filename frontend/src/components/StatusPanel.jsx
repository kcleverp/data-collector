// 소스별 '통합본에 담긴 일수'와 통합 파일 정보를 보여주는 영역.

function fmtBytes(n) {
  if (!n) return '0 B'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0, v = n
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++ }
  return `${v.toFixed(1)} ${u[i]}`
}

export default function StatusPanel({ sources, job }) {
  return (
    <div className="status">
      {sources.map((s) => {
        const p = job?.sources?.[s.num]
        const f = s.file
        return (
          <div className="status__item" key={s.num}>
            <div className="status__count">{s.dayCount}</div>
            <div className="status__unit">일치 저장</div>
            <div className="status__name">{s.name}</div>

            {p && p.total > 0 && (
              <div className="status__live">
                이번 작업 +{p.saved}
                {p.done < p.total ? ` · 진행 ${p.done}/${p.total}` : ' · 완료'}
              </div>
            )}

            <div className="status__file">
              {f?.exists ? `통합본 ${fmtBytes(f.bytes)}` : '아직 없음'}
            </div>
          </div>
        )
      })}
    </div>
  )
}
