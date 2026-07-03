import { useEffect, useState, useMemo } from 'react'
import { getSources, getCounts, startDownload, getJob, cancelJob } from './api.js'
import SourceCard from './components/SourceCard.jsx'
import StatusPanel from './components/StatusPanel.jsx'
import ProgressBar from './components/ProgressBar.jsx'

export default function App() {
  const [sources, setSources] = useState([])
  const [sel, setSel] = useState({})       // num -> { enabled, start, end }
  const [job, setJob] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)

  const running = job?.status === 'running'

  // 최초: 소스 목록 로드 + 기본 기간(최신 1일) 세팅
  useEffect(() => {
    getSources()
      .then((list) => {
        setSources(list)
        const init = {}
        list.forEach((s) => {
          init[s.num] = { enabled: false, start: s.maxDate || '', end: s.maxDate || '' }
        })
        setSel(init)
      })
      .catch((e) => setErr('소스 목록을 불러오지 못했습니다: ' + e.message))
      .finally(() => setLoading(false))
  }, [])

  // 작업 진행 중이면 폴링
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
      } catch {
        /* 일시적 오류 무시 */
      }
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

  const chosen = useMemo(
    () => sources.filter((s) => sel[s.num]?.enabled && sel[s.num].start && sel[s.num].end),
    [sources, sel],
  )

  const onStart = async () => {
    setErr(null)
    const selections = chosen.map((s) => ({
      num: s.num,
      start: sel[s.num].start,
      end: sel[s.num].end,
    }))
    // 기간 유효성 간단 체크
    for (const x of selections) {
      if (x.start > x.end) { setErr('시작일이 종료일보다 뒤인 소스가 있습니다.'); return }
    }
    try {
      setJob(null)
      const { jobId } = await startDownload(selections)
      setJobId(jobId)
    } catch (e) {
      setErr('시작 실패: ' + e.message)
    }
  }

  const onCancel = () => jobId && cancelJob(jobId).catch(() => {})

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
          <li><b>①</b> 소스 선택</li>
          <li><b>②</b> 기간 지정</li>
          <li><b>③</b> 수집 시작</li>
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

        <section className="actionbar">
          <div className="actionbar__info">
            <ProgressBar percent={overall?.percent || 0} big />
            <div className="actionbar__status">
              {statusText || `${chosen.length}개 소스 선택됨`}
            </div>
          </div>
          <div className="actionbar__btns">
            {running ? (
              <button className="btn btn--ghost" onClick={onCancel}>취소</button>
            ) : null}
            <button
              className="btn btn--primary"
              onClick={onStart}
              disabled={running || chosen.length === 0}
            >
              {running ? '수집 중…' : '수집 시작'}
            </button>
          </div>
        </section>

        <section className="panel">
          <h2 className="panel__title">저장 현황</h2>
          <StatusPanel sources={sources} job={job} />
          <p className="muted small">파일은 <code>backend/data/&lt;소스&gt;/</code> 에 CSV로 저장됩니다.</p>
        </section>
      </main>
    </div>
  )
}
