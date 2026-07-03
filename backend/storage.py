"""CSV 저장(다운로드 즉시 단일화) · 진행 상태 · 재개.

이 버전은 **소스마다 하나의 통합 CSV**에 날짜별 데이터를 계속 이어붙인다.
일자별 파일을 따로 남기지 않는다.

저장 위치:
  통합본     backend/data/{소스이름}/{num}_통합.csv
  진행기록   backend/data/{소스이름}/.progress.json   (이미 담긴 날짜 목록 — 재개용)
"""

import os
import glob
import json
import shutil

import config

CONSOLIDATED_SUFFIX = "_통합.csv"


def source_dir(num):
    """소스 저장 폴더(= 소스 이름). 없으면 생성."""
    d = os.path.join(config.DATA_DIR, config.source_dir_name(num))
    os.makedirs(d, exist_ok=True)
    return d


def consolidated_path(num):
    """소스별 통합 CSV 경로."""
    return os.path.join(source_dir(num), f"{num}{CONSOLIDATED_SUFFIX}")


# ── 진행 기록(담긴 날짜) ──────────────────────────────────────
def _progress_path(num):
    return os.path.join(source_dir(num), ".progress.json")


def _load_dates(num):
    p = _progress_path(num)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def _add_date(num, yyyymmdd):
    dates = _load_dates(num)
    dates.add(yyyymmdd)
    with open(_progress_path(num), "w", encoding="utf-8") as f:
        json.dump(sorted(dates), f)


def exists(num, yyyymmdd):
    """해당 날짜가 이미 통합본에 담겨 있으면 True (재개용)."""
    return yyyymmdd in _load_dates(num)


def day_count(num):
    """통합본에 담긴 날짜(일) 수."""
    return len(_load_dates(num))


def all_counts():
    """모든 소스의 담긴 일수 {num: days}."""
    return {s["num"]: day_count(s["num"]) for s in config.SOURCES}


def consolidated_info(num):
    """통합본 존재 여부/크기/담긴 일수."""
    path = consolidated_path(num)
    return {
        "exists": os.path.exists(path),
        "bytes": os.path.getsize(path) if os.path.exists(path) else 0,
        "days": day_count(num),
        "path": path if os.path.exists(path) else None,
    }


# ── 저장(이어붙이기) ──────────────────────────────────────────
def _strip_header(data_bytes):
    nl = data_bytes.find(b"\n")
    return data_bytes[nl + 1:] if nl != -1 else b""


def append_csv(num, yyyymmdd, data_bytes):
    """받은 CSV 바이트를 소스 통합본에 이어붙인다(헤더는 최초 1회만).

    반환: 통합본 경로.
    """
    path = consolidated_path(num)
    first = not os.path.exists(path)
    out = data_bytes if first else _strip_header(data_bytes)
    if out and not out.endswith(b"\n"):
        out += b"\n"
    with open(path, "ab") as f:
        f.write(out)
    _add_date(num, yyyymmdd)
    return path


# ── 마이그레이션 ──────────────────────────────────────────────
def migrate_legacy_dirs():
    """예전 num 폴더(data/84 등)를 소스 이름 폴더로 이관."""
    for s in config.SOURCES:
        old = os.path.join(config.DATA_DIR, s["num"])
        new = os.path.join(config.DATA_DIR, config.source_dir_name(s["num"]))
        if not os.path.isdir(old) or os.path.abspath(old) == os.path.abspath(new):
            continue
        os.makedirs(new, exist_ok=True)
        for fn in os.listdir(old):
            dst = os.path.join(new, fn)
            if not os.path.exists(dst):
                shutil.move(os.path.join(old, fn), dst)
        try:
            if not os.listdir(old):
                os.rmdir(old)
        except OSError:
            pass


def migrate_to_single_file():
    """예전 일자별 CSV들을 소스별 통합본 1개로 합치고 일자별 파일을 제거한다.

    (예: {num}_2024-01-01.csv → {num}_통합.csv 에 편입 후 원본 삭제)
    옛 _merged 폴더도 이 모델에서는 불필요하므로 제거.
    """
    for s in config.SOURCES:
        num = s["num"]
        d = source_dir(num)
        daily = sorted(
            f for f in glob.glob(os.path.join(d, f"{num}_*.csv"))
            if os.path.basename(f) != f"{num}{CONSOLIDATED_SUFFIX}"
        )
        for fp in daily:
            base = os.path.basename(fp)               # {num}_YYYY-MM-DD.csv
            date = base[len(num) + 1:-4].replace("-", "")   # → YYYYMMDD
            if not exists(num, date):
                with open(fp, "rb") as r:
                    append_csv(num, date, r.read())
            os.remove(fp)

    old_merged = os.path.join(config.DATA_DIR, "_merged")
    if os.path.isdir(old_merged):
        shutil.rmtree(old_merged, ignore_errors=True)
