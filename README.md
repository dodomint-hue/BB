# BBTECH T-PJT Dashboard

Google Sheets 공개 CSV와 연동되는 BBTECH T-PJT 공사관리 대시보드입니다.

## GitHub Pages로 사용

1. 이 폴더의 파일을 GitHub 저장소에 업로드합니다.
2. GitHub 저장소에서 `Settings` → `Pages`로 이동합니다.
3. `Deploy from a branch`를 선택합니다.
4. Branch는 `main`, 폴더는 `/root`를 선택하고 저장합니다.
5. 배포된 Pages 주소에서 `시트 동기화`를 누릅니다.

## 로컬에서 CORS가 날 때

`file://`로 HTML을 직접 열면 브라우저가 Google CSV 접근을 막을 수 있습니다.
그때는 `start_dashboard_server.cmd`를 실행해서 로컬 서버 주소로 열면 됩니다.

기본 로컬 주소:

```text
http://127.0.0.1:8765/
```

## 포함 파일

- `index.html`: GitHub Pages용 대시보드 메인 파일
- `dashboard_proxy_server.py`: 로컬 CORS 회피용 작은 프록시 서버
- `start_dashboard_server.cmd`: Windows에서 로컬 서버를 실행하는 파일
