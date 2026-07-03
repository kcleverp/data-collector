"""다운로드 작업 관리 — 백그라운드 스레드로 실행하고 진행률을 추적한다."""

import time
import uuid
import logging
import threading

import config
import storage
from ex_client import ExClient

log = logging.getLogger(__name__)


def _to_yyyymmdd(s):
    """'2024-01-01' 또는 '20240101' → '20240101'."""
    return s.replace("-", "").strip()


class Job:
    def __init__(self, selections, survey):
        # selections: [{"num": "84", "start": "2024-01-01", "end": "2024-03-31"}, ...]
        # survey: {key: code} 신청자 정보(받는 주체) — 모든 소스에 공통 적용
        self.id = uuid.uuid4().hex[:12]
        self.selections = selections
        self.survey = survey
        self.status = "running"          # running | done | cancelled | error
        self.error = None
        self.lock = threading.Lock()
        self._cancel = threading.Event()
        self.started_at = time.time()
        self.finished_at = None
        # 소스별 진행 상태
        self.sources = {
            sel["num"]: {
                "num": sel["num"],
                "total": 0, "done": 0, "saved": 0,
                "skipped": 0, "failed": 0,
                "current": None, "error": None,
            }
            for sel in selections
        }

    # ── 스냅샷(진행률 조회용) ─────────────────────────────
    def snapshot(self):
        with self.lock:
            total = sum(s["total"] for s in self.sources.values())
            done = sum(s["done"] for s in self.sources.values())
            saved = sum(s["saved"] for s in self.sources.values())
            return {
                "id": self.id,
                "status": self.status,
                "error": self.error,
                "recipient": config.survey_label(self.survey),
                "overall": {
                    "total": total,
                    "done": done,
                    "saved": saved,
                    "percent": round(done / total * 100, 1) if total else 0.0,
                },
                "sources": {num: dict(s) for num, s in self.sources.items()},
            }

    def cancel(self):
        self._cancel.set()

    # ── 실제 수집 로직(워커 스레드) ──────────────────────
    def run(self):
        client = ExClient()
        try:
            for sel in self.selections:
                if self._cancel.is_set():
                    break
                self._run_source(client, sel)

            with self.lock:
                if self._cancel.is_set():
                    self.status = "cancelled"
                elif self.status == "running":
                    self.status = "done"
        except Exception as e:                       # 치명적(세션/네트워크 등)
            log.exception("작업 실패")
            with self.lock:
                self.status = "error"
                self.error = str(e)
        finally:
            self.finished_at = time.time()

    def _run_source(self, client, sel):
        num = sel["num"]
        source = config.source_by_num(num)
        st = self.sources[num]
        if source is None:
            with self.lock:
                st["error"] = "알 수 없는 소스"
            return

        # 요청 기간 내에서 실제 데이터가 있는 날짜만 대상으로
        start = _to_yyyymmdd(sel["start"])
        end = _to_yyyymmdd(sel["end"])
        try:
            available = client.available_dates(source)
        except Exception as e:
            with self.lock:
                st["error"] = f"날짜 목록 조회 실패: {e}"
            return
        targets = [d for d in available if start <= d <= end]

        with self.lock:
            st["total"] = len(targets)

        for d in targets:
            if self._cancel.is_set():
                break
            with self.lock:
                st["current"] = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"

            try:
                if storage.exists(num, d):           # 재개: 이미 있음
                    with self.lock:
                        st["skipped"] += 1
                else:
                    data = client.download_csv(source, d, self.survey)
                    if data is None:                 # 해당 날짜 파일 없음
                        with self.lock:
                            st["skipped"] += 1
                    else:
                        storage.save_csv(num, d, data)
                        with self.lock:
                            st["saved"] += 1
            except Exception as e:
                log.warning("[%s %s] 실패: %s", num, d, e)
                with self.lock:
                    st["failed"] += 1
            finally:
                with self.lock:
                    st["done"] += 1
                time.sleep(config.BETWEEN_FILES_DELAY)

        with self.lock:
            st["current"] = None


class JobManager:
    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()

    def start(self, selections, survey):
        job = Job(selections, survey)
        with self._lock:
            self._jobs[job.id] = job
        threading.Thread(target=job.run, daemon=True).start()
        return job

    def get(self, job_id):
        with self._lock:
            return self._jobs.get(job_id)


manager = JobManager()
