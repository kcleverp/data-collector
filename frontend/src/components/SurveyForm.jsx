// 다운로드 신청자(받는 주체) 폼 — 사이트 원본 필수 항목 5개.
export default function SurveyForm({ fields, survey, onChange, disabled }) {
  return (
    <div className="survey">
      {fields.map((f) => (
        <label className="survey__field" key={f.key}>
          <span className="survey__label">{f.label}</span>
          <select
            className="survey__select"
            value={survey[f.key] || ''}
            disabled={disabled}
            onChange={(e) => onChange(f.key, e.target.value)}
          >
            <option value="">선택</option>
            {f.options.map((o) => (
              <option key={o.code} value={o.code}>{o.name}</option>
            ))}
          </select>
        </label>
      ))}
    </div>
  )
}
