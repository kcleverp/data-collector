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
