// 백엔드 API 래퍼. (개발 시 /api 는 vite 프록시가 8000으로 전달)

function formatErrorDetail(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((e) => e.msg || JSON.stringify(e)).join('; ')
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail)
  return null
}

async function json(res) {
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try {
      const body = await res.json()
      msg = formatErrorDetail(body.detail) || msg
    } catch {}
    throw new Error(msg)
  }
  return res.json()
}

export const getSources = () => fetch('/api/sources').then(json)

export const getCounts = () => fetch('/api/counts').then(json)

export const getSurveyOptions = () => fetch('/api/survey-options').then(json)

export const getInfo = () => fetch('/api/info').then(json)

export const startDownload = (selections, survey) =>
  fetch('/api/download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selections, survey }),
  }).then(json)

export const getJob = (id) => fetch(`/api/jobs/${id}`).then(json)

export const cancelJob = (id) =>
  fetch(`/api/jobs/${id}/cancel`, { method: 'POST' }).then(json)
