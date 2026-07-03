import { useEffect, useState, useMemo } from 'react'
import {
  getSources, getCounts, getSurveyOptions, getInfo,
  startDownload, getJob, cancelJob, mergeSource,
} from './api.js'
import SourceCard from './components/SourceCard.jsx'
import SurveyForm from './components/SurveyForm.jsx'
import StatusPanel from './components/StatusPanel.jsx'
import ProgressBar from './components/ProgressBar.jsx'

export default function App() {
  const [sources, setSources] = useState([])
  const [sel, setSel] = useState({})            // num -> { enabled, start, end }
  const [surveyFields, setSurveyFields] = useState([])
  const [survey, setSurvey] = useState({})      // key -> code
  const [info, setInfo] = useState(null)        // { dataDir }
  const [job, setJob] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [merging, setMerging] = useState({})    // num -> bool
  const [mergeResult, setMergeResult] = useState({})
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)

  const running = job?.status === 'running'

  // 최초 로드: 소스·설문 옵션·서버정보
  useEffect(() => {
    Promise.all([getSources(), getSurveyOptions(), getInfo()])
      .then(([list, fields, serverInfo]) => {
        setSources(list)
        const initSel = {}
        list.forEach((s) => {
          initSel[s.num] = { enabled: false, start: s.maxDate || '', end: s.maxDate || '' }
        })
        setSel(initSel)
        setSurveyFields(fields)
        setInfo(serverInfo)
      })
      .catch((e) => setErr('초기 데이터를 불러오지 못했습니다: ' + e.message))
      .finally(() => setLoading(false))
  }, [])

  // 작업 진행 중 폴링
  useEffect(() => {
    if (!jobId) return
    let stop = false
    const iv = setInterval(async () => {
      try {
        const snap = await getJob(jobId)
        if (stop) return
        setJob(snap)
        if (snap.status !== 'running') {
          clearInterval(iv)
          refreshCounts()
        }
      } catch { /* 일시적 오류 무시 */ }
    }, 700)
    return () => { stop = true; clearInterval(iv) }
  }, [jobId])

  const refreshCounts = async () => {
    try {
      const counts = await getCounts()
      setSources((prev) => prev.map((s) => ({ ...s, fileCount: counts[s.num] ?? s.fileCount })))
    } catch {}
  }

  const updateSel = (num, patch) =>
    setSel((prev) => ({ ...prev, [num]: { ...prev[num], ...patch } }))

  const updateSurvey = (key, code) =>
    setSurvey((prev) => ({ ...prev, [key]: code }))

  const chosen = useMemo(
    () => sources.filter((s) => sel[s.num]?.enabled && sel[s.num].start && sel[s.num].end),
    [sources, sel],
  )

  // 받는 주체(신청자) 라벨
  const surveyComplete = surveyFields.length > 0 && surveyFields.every((f) => survey[f.key])
  const recipient = useMemo(() => {
    if (!surveyComplete) return ''
    return surveyFields
      .map((f) => f.options.find((o) => o.code === survey[f.key])?.name)
      .join(' / ')
  }, [surveyFields, survey, surveyComplete])

  const onStart = async () => {
    setErr(null)
    if (!surveyComplete) { setErr('신청자 정보(받는 주체)를 모두 선택하세요.'); return }
    const selections = chosen.map((s) => ({ num: s.num, start: sel[s.num].start, end: sel[s.num].end }))
    for (const x of selections) {
      if (x.start > x.end) { setErr('시작일이 종료일보다 뒤인 소스가 있습니다.'); return }
    }
    try {
      setJob(null)
      const { jobId } = await startDownload(selections, survey)
      setJobId(jobId)
    } catch (e) {
      setErr('시작 실패: ' + e.message)
    }
  }

  const onCancel = () => jobId && cancelJob(jobId).catch(() => {})

  const onMerge = async (num) => {
    setErr(null)
    setMerging((m) => ({ ...m, [num]: true }))
    try {
      const res = await mergeSource(num)
      setMergeResult((m) => ({ ...m, [num]: res }))
      setSources(await getSources())   // merged 정보/개수 갱신
    } catch (e) {
      setErr('통합 실패: ' + e.message)
    } finally {
      setMerging((m) => ({ ...m, [num]: false }))
    }
  }

  const overall = job?.overall
  const statusText = !job
    ? ''
    : job.status === 'running'
      ? `수집 중… ${overall.done}/${overall.total}`
      : job.status === 'done'
        ? `완료 — 새로 저장 ${overall.saved}건`
        : job.status === 'cancelled'
          ? '취소됨'
          : '오류: ' + (job.error || '')

  return (
    <div className="app">
      <header className="hero">
        <h1>고속도로 VDS 데이터 수집기</h1>
        <p>data.ex.co.kr · 데이터 소스별 기간을 골라 CSV로 저장합니다</p>
      </header>

      <main className="wrap">
        <ol className="steps">
          <li><b>①</b> 소스·기간 선택</li>
          <li><b>②</b> 신청자 정보</li>
          <li><b>③</b> 수집 시작</li>
          <li><b>④</b> 하나로 통합</li>
        </ol>

        {err && <div className="alert">{err}</div>}

        <section className="panel">
          <h2 className="panel__title">데이터 소스 &amp; 기간</h2>
          {loading ? (
            <div className="muted">불러오는 중…</div>
          ) : (
            <div className="grid">
              {sources.map((s) => (
                <SourceCard
                  key={s.num}
                  source={s}
                  sel={sel[s.num] || { enabled: false, start: '', end: '' }}
                  onChange={(patch) => updateSel(s.num, patch)}
                  progress={job?.sources?.[s.num]}
                  disabledAll={running}
                />
              ))}
            </div>
          )}
        </section>

        <section className="panel">
          <h2 className="panel__title">신청자 정보 (받는 주체)</h2>
          <p className="muted small">
            이 데이터를 받는 주체로 서버에 기록되는 필수 정보입니다. 5개 항목을 모두 선택하세요.
          </p>
          <SurveyForm
            fields={surveyFields}
            survey={survey}
            onChange={updateSurvey}
            disabled={running}
          />
          <div className={`recipient ${recipient ? 'recipient--on' : ''}`}>
            <span className="recipient__k">받는 주체</span>
            <b>{recipient || '— 모든 항목을 선택하세요 —'}</b>
          </div>
        </section>

        <section className="actionbar">
          <div className="actionbar__info">
            <ProgressBar percent={overall?.percent || 0} big />
            <div className="actionbar__status">
              {statusText || `${chosen.length}개 소스 선택됨${surveyComplete ? '' : ' · 신청자 정보 미입력'}`}
            </div>
          </div>
          <div className="actionbar__btns">
            {running && <button className="btn btn--ghost" onClick={onCancel}>취소</button>}
            <button
              className="btn btn--primary"
              onClick={onStart}
              disabled={running || chosen.length === 0 || !surveyComplete}
            >
              {running ? '수집 중…' : '수집 시작'}
            </button>
          </div>
        </section>

        <section className="panel">
          <h2 className="panel__title">저장 현황</h2>
          <StatusPanel
            sources={sources}
            job={job}
            onMerge={onMerge}
            merging={merging}
            mergeResult={mergeResult}
          />
          <p className="muted small">
            저장 위치: <code>{info?.dataDir || 'backend/data'}</code>
            {'  '}· 파일명 <code>&lt;소스&gt;_&lt;날짜&gt;.csv</code> · 통합본 <code>_merged/&lt;소스&gt;_통합.csv</code>
          </p>
        </section>
      </main>
    </div>
  )
}
