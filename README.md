# 고속도로 VDS 데이터 수집기

data.ex.co.kr 의 VDS 데이터를 **데이터 소스별·기간별로 선택해 CSV로 저장**하는 웹 앱입니다.
백엔드(FastAPI)가 순수 HTTP로 파일을 받아 gzip 해제 후 CSV로 저장하고,
React 프론트엔드에서 기간 선택·진행률·저장 현황을 확인합니다. (브라우저/Selenium 불필요)

## 주요 기능

- **데이터 소스별 기간 선택** — 소스(84/87/F5)마다 시작일·종료일을 따로 지정
- **실시간 진행률** — 전체/소스별 프로그래스 바와 현재 처리 날짜 표시
- **저장 현황** — 소스별로 저장된 CSV 파일 개수를 별도 영역에 표시
- **재개 지원** — 이미 받은 날짜·데이터 없는 날짜는 자동으로 건너뜀
- **취소** — 진행 중인 작업을 즉시 중단
- **순수 HTTP 다운로드** — 브라우저/드라이버 없이 서버가 직접 파일 수집

## 구조

```
ex_collector/
├─ backend/                FastAPI 서버 (순수 HTTP 다운로드)
│  ├─ config.py            소스 정의(84/87/F5)·경로·네트워크 설정
│  ├─ ex_client.py         data.ex.co.kr 클라이언트 (검색→다운로드→gzip해제)
│  ├─ storage.py           CSV 저장·개수 집계·재개(중복 건너뛰기)
│  ├─ jobs.py              백그라운드 다운로드 작업 + 진행률 추적
│  ├─ app.py               API 라우트 + 프론트엔드 서빙  ← 진입점
│  ├─ requirements.txt
│  └─ data/                소스별 CSV 저장 위치 (실행 시 생성)
└─ frontend/               React + Vite 대시보드
   ├─ src/                 App / api / components(SourceCard·StatusPanel·ProgressBar)
   └─ dist/                빌드 결과 (백엔드가 이 폴더를 서빙)
```

## 실행 방법 (가장 간단)

프론트엔드는 이미 빌드되어 있어 **백엔드만 켜면** 됩니다.

```bash
cd backend
.venv\Scripts\activate            # (PowerShell: .venv\Scripts\Activate.ps1)
python app.py
```

그 다음 브라우저에서 **http://127.0.0.1:8000** 접속.

> 가상환경을 처음부터 만들려면:
> ```bash
> cd backend
> python -m venv .venv
> .venv\Scripts\activate
> pip install -r requirements.txt
> ```

## 사용 흐름

1. **소스 선택** — 받을 데이터 소스(체크박스)를 켭니다.
2. **기간 지정** — 소스별 시작일·종료일을 고릅니다. (가능 기간이 안내됨)
3. **수집 시작** — 버튼을 누르면 진행률 바가 채워지고, 완료된 파일 수가 실시간 표시됩니다.

- 저장 위치: `backend/data/<소스번호>/<소스번호>_<YYYY-MM-DD>.csv`
- 이미 받은 날짜는 자동으로 **건너뜁니다**(재개 지원).
- 데이터가 없는 날짜도 자동으로 건너뜁니다.

## 프론트엔드 개발 모드 (선택)

UI를 수정하려면:

```bash
cd frontend
npm install          # 최초 1회
npm run dev          # http://localhost:5173 (/api 는 8000으로 프록시)
```

수정 후 반영: `npm run build` → `backend/app.py`가 새 `dist/`를 서빙.

## 참고

- 로그인 불필요. 다운로드 전 설문 5개는 서버가 요구하지만 데이터에는 영향이 없어 자동 처리됩니다.
- 소스 3종: `84`(교통량·속도·지정체), `87`(정체길이), `F5`(구간별 소통일관성지수 TCI).
- CSV 인코딩은 원본 그대로(cp949)입니다. Excel에서 바로 열립니다.
