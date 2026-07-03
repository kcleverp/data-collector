"""data.ex.co.kr 다운로드 클라이언트 — 순수 HTTP (브라우저 불필요).

역분석으로 확인한 흐름:
  1) 상세 페이지 GET       → 세션 쿠키 확보
  2) /portal/fdwn/collectDateList  → 데이터가 있는 날짜 목록
  3) /portal/fdwn/search           → 해당 날짜의 실제 파일명(outFileName)
  4) /portal/fdwn/log              → 파일 다운로드(내용은 .zip 이름이지만 실제로는 gzip)
  5) gzip 해제 → CSV(cp949) 바이트

설문 5개(소속/지역/성별/나이/활용목적)는 필수 항목이며, '이 데이터를 받는 주체'로
서버에 기록된다. 사용자가 프론트에서 입력한 값을 그대로 실어 보낸다.
"""

import gzip
import logging

import requests

import config

log = logging.getLogger(__name__)


class ExClient:
    """한 세션으로 여러 소스를 다룬다. (스레드 1개에서만 사용)"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"),
        })
        self._prepared = set()  # 세션 확보(페이지 방문)한 소스 num

    def _prepare(self, source):
        """소스 상세 페이지를 한 번 방문해 세션/Referer를 맞춘다."""
        if source["num"] in self._prepared:
            return
        self.session.headers["Referer"] = source["url"]
        self.session.get(source["url"], timeout=config.REQUEST_TIMEOUT)
        self._prepared.add(source["num"])

    def _base_params(self, source):
        return {
            "dataSupplyDate": "", "dataSupplyYear": "", "dataSupplyMonth": "",
            "dataSupplyYearQ": "", "dataSupplyQuater": "", "dataSupplyYearY": "",
            "collectType": config.COLLECT_TYPE,
            "dataType": source["dataType"],
            "collectCycle": config.COLLECT_CYCLE,
            "supplyCycle": config.SUPPLY_CYCLE,
        }

    def available_dates(self, source):
        """데이터가 존재하는 날짜 목록을 'YYYYMMDD' 문자열 리스트로 반환(오름차순)."""
        self._prepare(source)
        self.session.headers["Referer"] = source["url"]
        data = {
            "collectType": config.COLLECT_TYPE,
            "dataType": source["dataType"],
            "collectCycle": config.COLLECT_CYCLE,
            "supplyCycle": config.SUPPLY_CYCLE,
            "dayClsnYn": "N",
        }
        r = self.session.post(config.BASE_URL + "/portal/fdwn/collectDateList",
                              data=data, timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        dates = r.json().get("List", []) or []
        return sorted(dates)

    def search(self, source, yyyymmdd):
        """해당 날짜의 파일명(outFileName) 반환. 파일이 없으면 None."""
        self._prepare(source)
        self.session.headers["Referer"] = source["url"]
        params = self._base_params(source)
        params["dataSupplyDate"] = yyyymmdd
        r = self.session.post(config.BASE_URL + "/portal/fdwn/search",
                              data=params, timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return None
        return rows[0].get("outFileName")

    def download_csv(self, source, yyyymmdd, survey):
        """해당 날짜의 CSV 바이트(cp949)를 반환. 파일이 없으면 None.

        survey: {key: code} 형태의 신청자 정보(소속/지역/성별/나이/활용목적).
                서버에 '받는 주체'로 기록된다.
        """
        out_file_name = self.search(source, yyyymmdd)
        if not out_file_name:
            return None

        params = self._base_params(source)
        params["dataSupplyDate"] = yyyymmdd
        params["outFileName"] = out_file_name
        params["serviceId"] = source["serviceId"]
        params.update(config.build_survey_params(survey))

        self.session.headers["Referer"] = source["url"]
        r = self.session.post(config.BASE_URL + "/portal/fdwn/log",
                              data=params, timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        body = r.content

        if body[:2] != b"\x1f\x8b":  # gzip 매직이 아니면 실패(에러 페이지 등)
            raise RuntimeError(
                f"다운로드 응답이 gzip이 아님 (size={len(body)}, "
                f"content-type={r.headers.get('Content-Type')})"
            )
        return gzip.decompress(body)
