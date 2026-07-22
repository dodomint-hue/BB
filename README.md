# BBTECH T-PJT Dashboard

Google Sheets 공개 CSV와 연동되는 BBTECH T-PJT 공사관리 대시보드입니다.

## 인력 투입·성과 집계

- 출근공수를 설치, 용접, 사외제작, 지원 업무로 나눠 같은 기술인 행에 표시합니다.
- 설비 진척은 설비·공종·PRE/FINAL별로 한 번만 계산하고, 갱신 구간의 설치공수 비율로 기술인에게 배분합니다.
- 설치공수 2.0 M/D 또는 측정 2일 미만은 순위에서 제외하지 않고 `표본부족`으로 표시합니다.
- 용접 인력은 M/D와 함께 `Size - Welding Point` 합계를 확인할 수 있습니다.
- `인력 성과 다운로드`는 SheetJS를 불러올 수 있으면 XLSX로, CDN이 차단되면 한글 호환 CSV로 자동 저장합니다.

## 문제 진단

- 정체 기술인은 과거 최장 구간이 아닌 최신 진척률의 현재 연속 정체만 집계하며 이메일을 우선 식별자로 사용합니다.
- 정체와 저효율 설비는 중복 집계하지 않고, 미보고는 `3~13일` 최근 미보고와 `14일+` 장기 미갱신으로 분리합니다.
- 일반 작업내용과 단순 지원은 지연원인에서 제외하고, 선택기간에 근거가 없으면 직전 14일 특이사항을 사용합니다.
- 시트의 `턴온완료` 기록은 문제 설비에서 자동 제외합니다.

## GitHub Pages로 사용

1. 이 폴더의 파일을 GitHub 저장소에 업로드합니다.
2. GitHub 저장소에서 `Settings` → `Pages`로 이동합니다.
3. `Deploy from a branch`를 선택합니다.
4. Branch는 `main`, 폴더는 `/root`를 선택하고 저장합니다.
5. 저장소의 `Actions` 탭에서 `Sync Google Sheet`를 한 번 직접 실행합니다.
6. 배포된 Pages 주소에서 `시트 동기화`를 누릅니다.

GitHub Pages에서는 브라우저가 Google CSV를 직접 요청하지 않습니다. `Sync Google Sheet` 작업이 5분마다 `sheet-data.csv`를 갱신하고, 대시보드는 같은 사이트의 CSV를 읽습니다. GitHub의 예약 작업은 혼잡도에 따라 몇 분 늦어질 수 있으며 `Run workflow`로 즉시 실행할 수 있습니다.

`index.html`을 폴더에서 직접 열어도 `sheet-data.js`에 포함된 최근 동기화 데이터를 자동으로 표시합니다. 파일 직접 실행은 패키지 생성 시점의 데이터이며, Google 시트의 현재 값을 받으려면 `start_dashboard_server.cmd`를 실행합니다.

## 로컬에서 CORS가 날 때

`file://`로 HTML을 직접 열면 브라우저가 Google CSV 접근을 막을 수 있습니다.
그때는 `start_dashboard_server.cmd`를 실행하면 서버 버전과 실제 포트를 확인한 뒤 Chrome에서 최신 대시보드를 엽니다.
로컬 프록시는 Google 원본 캐시를 무효화해 다시 요청하고, 일반 요청이 막히면 JSONP 보조 연결로 전환합니다. 일시적인 upstream 오류에는 마지막 정상 CSV를 사용합니다.
로컬 ZIP은 `/download/github-package` 주소에서 첨부파일로 직접 내려받을 수 있습니다.
열린 탭이 이전 빌드이면 대시보드가 최신 HTML 버전을 감지해 자동으로 새로 엽니다.

기본 로컬 주소:

```text
http://127.0.0.1:8765/
```

## 포함 파일

- `index.html`: GitHub Pages용 대시보드 메인 파일
- `sheet-data.js`: `index.html` 직접 실행용 데이터
- `dashboard_proxy_server.py`: 로컬 CORS 회피용 작은 프록시 서버
- `start_dashboard_server.cmd`: Windows에서 로컬 서버를 실행하는 파일
