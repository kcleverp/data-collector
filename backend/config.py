"""백엔드 설정 — 수집 대상 데이터 소스와 경로 정의."""

import os

# ── 수집 대상 데이터 소스 ─────────────────────────────────────
# 세 소스는 페이지 구조가 동일하고 아래 값만 다르다(역분석으로 확인).
#   num       : 데이터셋 식별자 (URL num 파라미터)
#   name      : 화면 표시용 이름
#   dataType  : 다운로드 API 파라미터 (num과 동일)
#   serviceId : 다운로드 API 파라미터 (소스마다 다름)
#   url       : 세션 확보용 상세 페이지
SOURCES = [
    {
        "num": "84",
        "name": "VDS 교통량·속도·지정체",
        "dataType": "84",
        "serviceId": "518",
        "url": "https://data.ex.co.kr/portal/fdwn/view?type=VDS&num=84&requestfrom=dataset",
    },
    {
        "num": "87",
        "name": "VDS 정체길이",
        "dataType": "87",
        "serviceId": "521",
        "url": "https://data.ex.co.kr/portal/fdwn/view?type=VDS&num=87&requestfrom=dataset",
    },
    {
        "num": "F5",
        "name": "구간별 소통일관성지수(TCI)",
        "dataType": "F5",
        "serviceId": "530",
        "url": "https://data.ex.co.kr/portal/fdwn/view?type=VDS&num=F5&nia_yn=y",
    },
]

# 소스는 모두 '1일' 집계다.
COLLECT_TYPE = "VDS"
COLLECT_CYCLE = "04"   # 집계주기: 1일
SUPPLY_CYCLE = "01"    # 제공주기: 1일

BASE_URL = "https://data.ex.co.kr"

# ── 경로 ──────────────────────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BACKEND_DIR, "data")          # 소스별 CSV 저장 루트
FRONTEND_DIST = os.path.join(BACKEND_DIR, "..", "frontend", "dist")

# ── 네트워크 ──────────────────────────────────────────────────
REQUEST_TIMEOUT = 120      # 개별 요청 타임아웃(초)
BETWEEN_FILES_DELAY = 0.3  # 파일 사이 간격(초) — 서버 부담 완화


def source_by_num(num):
    for s in SOURCES:
        if s["num"] == num:
            return s
    return None
