"""CSV 저장 · 파일 개수 집계 · 재개(이미 받은 파일 건너뛰기).

저장 위치:  backend/data/{num}/{num}_{YYYY-MM-DD}.csv
"""

import os
import glob

import config


def source_dir(num):
    d = os.path.join(config.DATA_DIR, num)
    os.makedirs(d, exist_ok=True)
    return d


def _fmt_date(yyyymmdd):
    return f"{yyyymmdd[0:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def csv_path(num, yyyymmdd):
    return os.path.join(source_dir(num), f"{num}_{_fmt_date(yyyymmdd)}.csv")


def exists(num, yyyymmdd):
    """해당 날짜 CSV가 이미 저장돼 있으면 True (재개용)."""
    return os.path.exists(csv_path(num, yyyymmdd))


def save_csv(num, yyyymmdd, data_bytes):
    """CSV 바이트를 원본 인코딩(cp949) 그대로 저장. 저장 경로 반환."""
    path = csv_path(num, yyyymmdd)
    with open(path, "wb") as f:
        f.write(data_bytes)
    return path


def file_count(num):
    """해당 소스에 저장된 CSV 파일 개수."""
    return len(glob.glob(os.path.join(source_dir(num), "*.csv")))


def all_counts():
    """모든 소스의 저장 파일 개수 {num: count}."""
    return {s["num"]: file_count(s["num"]) for s in config.SOURCES}


# ── 통합(merge) ───────────────────────────────────────────────
def merged_dir():
    d = os.path.join(config.DATA_DIR, "_merged")
    os.makedirs(d, exist_ok=True)
    return d


def merged_path(num):
    """소스별 통합 파일 경로.  data/_merged/{num}_통합.csv"""
    return os.path.join(merged_dir(), f"{num}_통합.csv")


def _daily_files(num):
    """해당 소스의 일자별 CSV 파일 목록(날짜순)."""
    return sorted(glob.glob(os.path.join(source_dir(num), f"{num}_*.csv")))


def merged_info(num):
    """통합 파일 존재 여부/크기."""
    path = merged_path(num)
    if os.path.exists(path):
        return {"exists": True, "bytes": os.path.getsize(path), "path": path}
    return {"exists": False, "bytes": 0, "path": None}


def merge_source(num):
    """해당 소스의 일자별 CSV를 하나로 합친다(헤더 1회, cp949 원본 유지).

    반환: {num, files, rows, bytes, path}  — files=합친 파일 수, rows=데이터 행수.
    """
    files = _daily_files(num)
    if not files:
        return {"num": num, "files": 0, "rows": 0, "bytes": 0, "path": None}

    out = merged_path(num)
    total_rows = 0
    with open(out, "wb") as w:
        for i, fp in enumerate(files):
            with open(fp, "rb") as r:
                data = r.read()
            nl = data.find(b"\n")
            if nl == -1:                       # 헤더뿐이거나 개행 없음
                header, body = data, b""
            else:
                header, body = data[: nl + 1], data[nl + 1:]
            if i == 0:
                w.write(header)                # 헤더는 첫 파일 것만
            if body:
                if not body.endswith(b"\n"):   # 파일 경계에서 행이 붙지 않도록
                    body += b"\n"
                w.write(body)
                total_rows += body.count(b"\n")

    return {
        "num": num,
        "files": len(files),
        "rows": total_rows,
        "bytes": os.path.getsize(out),
        "path": out,
    }
