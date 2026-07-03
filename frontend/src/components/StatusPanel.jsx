// 소스별 '저장된 CSV 파일 개수' + 하나로 통합(merge) 영역.

function fmtBytes(n) {
  if (!n) return '0 B'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0, v = n
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++ }
  return `${v.toFixed(1)} ${u[i]}`
}

export default function StatusPanel({ sources, job, onMerge, merging, mergeResult }) {
  return (
    <div className="status">
      {sources.map((s) => {
        const p = job?.sources?.[s.num]
        const mr = mergeResult?.[s.num]
        const busy = merging?.[s.num]
        return (
          <div className="status__item" key={s.num}>
            <div className="status__count">{s.fileCount}</div>
            <div className="status__unit">개 파일</div>
            <div className="status__name">{s.name}</div>

            {p && p.total > 0 && (
              <div className="status__live">
                이번 작업 +{p.saved}
                {p.done < p.total ? ` · 진행 ${p.done}/${p.total}` : ' · 완료'}
              </div>
            )}

            <button
              className="btn btn--merge"
              disabled={busy || s.fileCount === 0}
              onClick={() => onMerge(s.num)}
            >
              {busy ? '통합 중…' : '하나로 통합'}
            </button>

            {mr ? (
              <div className="status__merge">
                통합 완료 · {mr.files}개 → {mr.rows.toLocaleString()}행 ({fmtBytes(mr.bytes)})
              </div>
            ) : s.merged?.exists ? (
              <div className="status__merge">통합본 있음 ({fmtBytes(s.merged.bytes)})</div>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
