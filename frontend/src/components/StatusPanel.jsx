// 소스별 '저장된 CSV 파일 개수'를 크게 보여주는 별도 영역.
export default function StatusPanel({ sources, job }) {
  return (
    <div className="status">
      {sources.map((s) => {
        const p = job?.sources?.[s.num]
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
          </div>
        )
      })}
    </div>
  )
}
