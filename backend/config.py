"""백엔드 설정 — 수집 대상 데이터 소스와 경로 정의."""

import os
import re

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

# ── 다운로드 신청자 설문(사이트가 요구하는 필수 항목) ─────────
# 사이트는 다운로드 전에 "누가 어떤 목적으로 받는지"를 반드시 입력받는다.
# 아래는 사이트 원본 <select> 의 값/표시텍스트를 그대로 옮긴 것.
# codeParam/nameParam 은 다운로드 요청에 실려 서버 로그에 '받는 주체'로 기록된다.
SURVEY_FIELDS = [
    {
        "key": "dept", "label": "소속",
        "codeParam": "deptCd", "nameParam": "deptName",
        "options": [
            {"code": "0", "name": "중앙행정기관·공공기관"},
            {"code": "1", "name": "지방자치단체"},
            {"code": "2", "name": "공기업·준정부기관"},
            {"code": "3", "name": "민간기업·스타트업"},
            {"code": "4", "name": "대학교·연구기관"},
            {"code": "5", "name": "일반개인·학생"},
        ],
    },
    {
        "key": "region", "label": "지역",
        "codeParam": "regionCd", "nameParam": "regionName",
        "options": [
            {"code": "KR-11", "name": "서울특별시"},
            {"code": "KR-26", "name": "부산광역시"},
            {"code": "KR-27", "name": "대구광역시"},
            {"code": "KR-28", "name": "인천광역시"},
            {"code": "KR-29", "name": "광주광역시"},
            {"code": "KR-30", "name": "대전광역시"},
            {"code": "KR-31", "name": "울산광역시"},
            {"code": "KR-41", "name": "경기도"},
            {"code": "KR-42", "name": "강원특별자치도"},
            {"code": "KR-43", "name": "충청북도"},
            {"code": "KR-44", "name": "충청남도"},
            {"code": "KR-45", "name": "전라북도"},
            {"code": "KR-46", "name": "전라남도"},
            {"code": "KR-47", "name": "경상북도"},
            {"code": "KR-48", "name": "경상남도"},
            {"code": "KR-49", "name": "제주특별자치도"},
            {"code": "KR-50", "name": "세종특별자치시"},
        ],
    },
    {
        "key": "gender", "label": "성별",
        "codeParam": "genderCd", "nameParam": "gender",
        "options": [
            {"code": "0", "name": "남성"},
            {"code": "1", "name": "여성"},
        ],
    },
    {
        "key": "age", "label": "나이",
        "codeParam": "userAgeCd", "nameParam": "userAgeName",
        "options": [
            {"code": "10", "name": "10대"},
            {"code": "20", "name": "20대"},
            {"code": "30", "name": "30대"},
            {"code": "40", "name": "40대"},
            {"code": "50", "name": "50대"},
            {"code": "60", "name": "60대 이상"},
        ],
    },
    {
        "key": "pou", "label": "활용목적",
        "codeParam": "pouCd", "nameParam": "pouName",
        "options": [
            {"code": "0", "name": "연구 및 학술분석"},
            {"code": "1", "name": "서비스 및 앱 개발"},
            {"code": "2", "name": "정책 및 행정 활용"},
            {"code": "3", "name": "기업 비즈니스 마케팅 분석"},
            {"code": "4", "name": "교육 및 학습 목적"},
            {"code": "5", "name": "언론보도 또는 콘텐츠 제작"},
        ],
    },
]


def build_survey_params(survey):
    """{key: code} → 다운로드 요청용 파라미터(코드+표시명) dict.

    누락/잘못된 값이 있으면 ValueError.
    """
    params = {}
    for f in SURVEY_FIELDS:
        code = (survey or {}).get(f["key"], "")
        match = next((o for o in f["options"] if o["code"] == code), None)
        if match is None:
            raise ValueError(f"'{f['label']}' 값이 필요합니다.")
        params[f["codeParam"]] = code
        params[f["nameParam"]] = match["name"]
    params["emailAddress"] = "-"
    return params


def survey_label(survey):
    """{key: code} → '민간기업·스타트업 / 서울특별시 / 남성 / 20대 / 연구 및 학술분석'."""
    parts = []
    for f in SURVEY_FIELDS:
        code = (survey or {}).get(f["key"], "")
        match = next((o for o in f["options"] if o["code"] == code), None)
        parts.append(match["name"] if match else "-")
    return " / ".join(parts)


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


def source_dir_name(num):
    """소스의 저장 폴더 이름 = 소스 이름(파일시스템 금지문자/공백만 정리).

    예) 84 → 'VDS_교통량·속도·지정체'
    """
    s = source_by_num(num)
    name = s["name"] if s else num
    safe = re.sub(r'[\\/:*?"<>|]+', "_", name)   # 윈도우 금지문자 제거
    return safe.replace(" ", "_").strip("_")
