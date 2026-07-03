"""FastAPI 서버 — 수집 API 제공 + 빌드된 React 프론트엔드 서빙.

실행:  uvicorn app:app --port 8000   (또는 python app.py)
"""

import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import storage
from ex_client import ExClient
from jobs import manager

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# data 폴더는 런타임에 생성된다(.gitignore 로 저장소에서는 제외). 서버 시작 시 보장.
os.makedirs(config.DATA_DIR, exist_ok=True)
# 예전 num 폴더(84/87/F5)를 소스 이름 폴더로 이관 후, 일자별 파일을 통합본으로 단일화.
storage.migrate_legacy_dirs()
storage.migrate_to_single_file()

app = FastAPI(title="EX 데이터 수집기")

# 개발 시 Vite dev 서버(5173)에서의 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_html(request, call_next):
    """index.html 캐시로 구버전 JS가 남는 문제 방지."""
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache"
    return response

# 소스별 사용 가능 날짜 범위 캐시 (최초 1회 조회)
_date_range_cache = {}


def _date_range(source):
    num = source["num"]
    if num not in _date_range_cache:
        try:
            dates = ExClient().available_dates(source)
            if dates:
                _date_range_cache[num] = {
                    "minDate": _fmt(dates[0]),
                    "maxDate": _fmt(dates[-1]),
                    "availableCount": len(dates),
                }
            else:
                _date_range_cache[num] = {"minDate": None, "maxDate": None,
                                          "availableCount": 0}
        except Exception as e:
            logging.warning("날짜 범위 조회 실패 (%s): %s", num, e)
            return {"minDate": None, "maxDate": None, "availableCount": 0}
    return _date_range_cache[num]


def _fmt(d):
    return f"{d[0:4]}-{d[4:6]}-{d[6:8]}"


# ── API ───────────────────────────────────────────────────────
@app.get("/api/sources")
def get_sources():
    """소스 목록 + 사용 가능 날짜 범위 + 통합본에 담긴 일수."""
    result = []
    for s in config.SOURCES:
        rng = _date_range(s)
        result.append({
            "num": s["num"],
            "name": s["name"],
            "minDate": rng["minDate"],
            "maxDate": rng["maxDate"],
            "availableCount": rng["availableCount"],
            "dayCount": storage.day_count(s["num"]),
            "file": storage.consolidated_info(s["num"]),
        })
    return result


@app.get("/api/counts")
def get_counts():
    """소스별 담긴 일수(가벼운 새로고침용)."""
    return storage.all_counts()


@app.get("/api/survey-options")
def get_survey_options():
    """다운로드 신청자 설문 항목/선택지(사이트 원본 폼)."""
    return config.SURVEY_FIELDS


@app.get("/api/info")
def get_info():
    """저장 경로 등 서버 정보."""
    return {"dataDir": os.path.abspath(config.DATA_DIR)}


class Selection(BaseModel):
    num: str
    start: str   # 'YYYY-MM-DD'
    end: str     # 'YYYY-MM-DD'


class DownloadRequest(BaseModel):
    selections: list[Selection]
    survey: dict[str, str]   # {key: code} 신청자 정보(받는 주체)


@app.post("/api/download")
def start_download(req: DownloadRequest):
    """선택한 소스/기간에 대한 다운로드 작업을 시작하고 jobId 반환."""
    selections = [s.model_dump() for s in req.selections if s.start and s.end]
    if not selections:
        raise HTTPException(400, "선택된 소스가 없습니다.")
    # 신청자 설문 필수 검증(사이트가 요구) — 하나라도 비면 400
    try:
        config.build_survey_params(req.survey)
    except ValueError as e:
        raise HTTPException(400, str(e))
    job = manager.start(selections, req.survey)
    return {"jobId": job.id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(404, "작업을 찾을 수 없습니다.")
    return job.snapshot()


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(404, "작업을 찾을 수 없습니다.")
    job.cancel()
    return {"ok": True}


# ── 빌드된 프론트엔드 서빙 (있을 때만) ────────────────────────
_dist = os.path.abspath(config.FRONTEND_DIST)
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
