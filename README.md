# BBTECH T-PJT 공사관리 대시보드

Samsung Taylor(T-PJT) 현장 공사관리 대시보드입니다.
**GitHub**에 코드를 보관하고, **Cloudflare Pages**로 일반 웹사이트처럼 배포합니다.
Google 스프레드시트의 데이터를 **1분마다 자동으로** 가져옵니다.

- Build: **2026-08-14**
- Rev: **1.0.0** (Cloudflare Pages 배포 대응 — 신규 파일 3종 추가)

---

## 목차

1. [무엇이 어떻게 동작하나요](#1-무엇이-어떻게-동작하나요)
2. [폴더 구조](#2-폴더-구조)
3. [준비물](#3-준비물)
4. [1단계 · GitHub에 코드 올리기](#4-1단계--github에-코드-올리기)
5. [2단계 · Cloudflare Pages 연결하기](#5-2단계--cloudflare-pages-연결하기)
6. [3단계 · 배포 확인하기](#6-3단계--배포-확인하기)
7. [나중에 코드를 수정하고 싶을 때](#7-나중에-코드를-수정하고-싶을-때)
8. [문제 해결](#8-문제-해결)
9. [/api/sheet 응답 규격](#9-apisheet-응답-규격)
10. [공식 문서 링크](#10-공식-문서-링크)
11. [변경 이력](#11-변경-이력)

---

## 1. 무엇이 어떻게 동작하나요

### 데이터가 흐르는 길

```
Google 스프레드시트 (웹에 게시한 CSV)
          │
          │  ← Cloudflare 서버가 대신 받아옴 (캐시 사용 안 함)
          ▼
  /api/sheet   ← functions/api/sheet.js 가 처리
          │
          │  ← 브라우저가 요청 (cache: "no-store")
          ▼
     대시보드 화면
```

### 왜 중계기(`/api/sheet`)가 필요한가요?

브라우저가 Google 주소를 직접 부르면 두 가지 문제가 생깁니다.

1. **CORS 차단** — 다른 도메인이라 브라우저가 응답을 막습니다.
2. **캐시** — Google이 몇 분 전 사본을 돌려줘서 최신 데이터가 안 옵니다.

Cloudflare 서버가 **대신** 받아오면 두 문제가 모두 사라집니다.
브라우저 입장에서는 같은 사이트(`/api/sheet`)를 부르는 것이라 차단되지 않습니다.

### 언제 데이터를 가져오나요

| 시점 | 동작 |
|---|---|
| 사이트를 열 때 | `/api/sheet` 호출 |
| 새로고침할 때 | `/api/sheet` 호출 |
| 시트 동기화 버튼을 누를 때 | `/api/sheet` 즉시 호출 |
| 페이지를 켜 둔 동안 | **1분마다** 자동 호출 |

### 실시간 데이터 vs 저장본

- **정상** → Google 원본을 그대로 사용 (화면에 **실시간** 표시)
- **Google 연결 실패 시에만** → 저장본 `sheet-data.csv` 사용 (화면에 **저장본** 표시)

저장본은 오래된 데이터일 수 있으므로 화면에서 색과 문구로 뚜렷하게 구분됩니다.

---

## 2. 폴더 구조

GitHub 저장소 **최상위**가 아래처럼 되어야 합니다.

```
(저장소 최상위)
├── index.html          ← 대시보드 본체
├── _headers            ← 캐시 차단 설정 (확장자 없음!)
├── README.md           ← 이 문서
├── sheet-data.csv      ← 장애 시 사용하는 저장본
├── sheet-data.js       ← 2차 저장본
└── functions/
    └── api/
        └── sheet.js    ← Google CSV 중계기
```

> ⚠️ **가장 중요한 규칙**
> `functions` 폴더는 반드시 **저장소 최상위**에 있어야 합니다.
> 다른 폴더 안에 넣으면 `/api/sheet` 주소가 만들어지지 않습니다.

> ⚠️ `_headers` 파일은 **확장자가 없습니다.**
> Windows 메모장으로 저장하면 `_headers.txt`가 되어 동작하지 않으니,
> 이 저장소에 있는 파일을 **그대로 업로드**하세요.

---

## 3. 준비물

| 항목 | 설명 |
|---|---|
| GitHub 계정 | 무료. 코드 보관용 |
| Cloudflare 계정 | 무료. 웹사이트 배포용. **신용카드 불필요** |
| Google 시트 게시 | 이미 완료됨. 게시를 **중지하지만 않으면** 됩니다 |

설치할 프로그램은 없습니다. **웹 브라우저만** 있으면 됩니다.
Git 프로그램, Python, 명령 프롬프트(CMD), PowerShell 모두 필요 없습니다.

---

## 4. 1단계 · GitHub에 코드 올리기

### 4-1. 저장소(Repository) 만들기 — 이미 있으면 건너뛰세요

1. `github.com`에 로그인합니다.
2. 오른쪽 위 **`+`** 아이콘 → **`New repository`** 를 누릅니다.
3. 아래처럼 입력합니다.
   - **Repository name**: `bbtech-dashboard`
   - **Public** 또는 **Private** 중 선택 (둘 다 Cloudflare 연결 가능)
   - `Add a README file` 체크는 **해제**
4. 맨 아래 **`Create repository`** 버튼을 누릅니다.

### 4-2. 파일 업로드하기

1. 저장소 화면에서 **`Add file`** 버튼 → **`Upload files`** 를 누릅니다.
2. 파일들을 회색 점선 영역으로 **끌어다 놓습니다.**
   - `functions` 폴더는 **폴더째로** 끌어다 놓으세요. 그래야 안쪽 구조가 유지됩니다.
   - 폴더 드래그가 안 되면, 아래 4-3 방법을 쓰세요.
3. 아래 **`Commit changes`** 버튼을 누릅니다.

### 4-3. 폴더 드래그가 안 될 때 (모바일 등)

`functions/api/sheet.js`만 따로 만드는 방법입니다.

1. 저장소 화면에서 **`Add file`** → **`Create new file`** 을 누릅니다.
2. 파일 이름 칸에 정확히 다음을 입력합니다.
   ```
   functions/api/sheet.js
   ```
   `/`를 입력할 때마다 폴더가 자동으로 만들어집니다.
3. 아래 넓은 칸에 `sheet.js` 내용을 붙여넣습니다.
4. **`Commit changes`** 버튼을 누릅니다.

### 4-4. 확인

저장소 첫 화면에 `functions` 폴더가 보이고,
`functions` → `api` → `sheet.js` 순서로 들어가지면 성공입니다.

---

## 5. 2단계 · Cloudflare Pages 연결하기

> 아래 화면 구성은 Cloudflare가 수시로 바꿉니다.
> 버튼 이름이 조금 달라도 **뜻이 같은 버튼**을 누르면 됩니다.
> 정확한 최신 절차는 [10번 공식 문서](#10-공식-문서-링크)를 함께 참고하세요.

### 5-1. 프로젝트 만들기

1. `dash.cloudflare.com`에 로그인합니다.
2. 왼쪽 메뉴에서 **`Workers & Pages`** 를 누릅니다.
3. **`Create`** (또는 `Create application`) 버튼을 누릅니다.
4. **`Pages`** 탭을 선택합니다.
5. **`Connect to Git`** (또는 `Import an existing Git repository`)을 누릅니다.

### 5-2. GitHub 계정 연결

1. **`Connect GitHub`** 버튼을 누릅니다.
2. GitHub 로그인 화면이 뜨면 로그인합니다.
3. 권한 화면에서
   - `All repositories` 또는
   - `Only select repositories` → `bbtech-dashboard` 선택
4. **`Install & Authorize`** 버튼을 누릅니다.
5. Cloudflare 화면으로 돌아오면 저장소 목록에서 **`bbtech-dashboard`** 를 고르고
   **`Begin setup`** 을 누릅니다.

### 5-3. 빌드 설정 — ⭐ 가장 중요한 부분

아래 표대로 정확히 입력하세요.

| 항목 | 입력할 값 |
|---|---|
| Project name | `bbtech-dashboard` (사이트 주소가 됩니다) |
| Production branch | `main` |
| Framework preset | **`None`** |
| Build command | **비워 둡니다** (아무것도 입력하지 않음) |
| Build output directory | **`/`** 또는 비워 둡니다 |
| Root directory | 건드리지 않습니다 (기본값 유지) |

> 이 대시보드는 **빌드가 필요 없는 정적 사이트**입니다.
> Build command에 뭔가를 넣으면 배포가 실패합니다.

### 5-4. 배포 시작

1. **`Save and Deploy`** 버튼을 누릅니다.
2. 1~2분 기다립니다. 로그가 흐르다가 **`Success`** 가 뜨면 완료입니다.
3. 화면에 나오는 주소를 확인합니다.
   ```
   https://bbtech-dashboard.pages.dev
   ```

---

## 6. 3단계 · 배포 확인하기

### 6-1. 중계기부터 확인 (가장 중요)

브라우저 주소창에 다음을 입력합니다.

```
https://<본인주소>.pages.dev/api/sheet
```

| 화면에 보이는 것 | 의미 |
|---|---|
| 쉼표로 구분된 글자가 잔뜩 나옴 | ✅ **성공** — CSV가 정상 수신됨 |
| `{"ok":false,"error":"HTML_INSTEAD_OF_CSV"...}` | ❌ Google 게시 링크 문제 |
| `Nothing is here yet` / 404 | ❌ `functions` 폴더 위치가 잘못됨 |

### 6-2. 대시보드 확인

1. `https://<본인주소>.pages.dev` 로 접속합니다.
2. 화면에 **실시간** 표시가 뜨는지 봅니다.
3. 다음 숫자들이 표시되는지 확인합니다.
   - 성공 시각
   - 원본 CSV 행 수
   - 대시보드 반영 건수
   - 제외 건수 (및 사유별 내역)

### 6-3. 모바일 확인

휴대폰 브라우저에서 같은 주소로 접속해 화면이 깨지지 않는지 확인합니다.

---

## 7. 나중에 코드를 수정하고 싶을 때

**GitHub에 파일을 올리면 Cloudflare가 자동으로 다시 배포합니다.** 별도 작업이 없습니다.

1. GitHub 저장소에서 바꿀 파일을 클릭합니다.
2. 오른쪽 위 **연필(✏️) 아이콘**을 누릅니다.
3. 내용을 고칩니다.
4. **`Commit changes`** 를 누릅니다.
5. 1~2분 뒤 사이트에 자동 반영됩니다.

파일을 통째로 바꾸려면 **`Add file`** → **`Upload files`** 로 같은 이름의 파일을 올리면 덮어써집니다.

---

## 8. 문제 해결

### `/api/sheet` 관련 오류

| 에러 코드 | 원인 | 조치 |
|---|---|---|
| `HTML_INSTEAD_OF_CSV` | Google이 CSV 대신 오류 페이지를 반환 | 스프레드시트 → `파일` → `공유` → `웹에 게시` 가 켜져 있는지 확인 |
| `UPSTREAM_HTTP_404` | 게시 링크가 잘못되었거나 게시가 중지됨 | 게시 링크를 다시 복사해 `sheet.js`의 `SHEET_CSV_URL` 수정 |
| `UPSTREAM_TIMEOUT` | Google 응답 지연 | 잠시 후 재시도. 반복되면 시트 용량 확인 |
| `EMPTY_BODY` | 시트가 비어 있음 | 원본 시트 확인 |
| 404 페이지가 나옴 | `functions` 폴더 위치 오류 | `functions/api/sheet.js` 가 저장소 **최상위** 아래에 있는지 확인 |

### 배포 관련 오류

| 증상 | 원인 | 조치 |
|---|---|---|
| 배포가 `Failed` | Build command에 값이 들어 있음 | 설정에서 Build command를 **비움** |
| 사이트는 뜨는데 데이터가 저장본 | `/api/sheet` 실패 | 위 표대로 `/api/sheet` 를 직접 열어 원인 확인 |
| 옛날 화면이 계속 보임 | 브라우저 캐시 | 강력 새로고침 (`Ctrl`+`Shift`+`R`) |
| `_headers`가 안 먹힘 | 파일명이 `_headers.txt` | 확장자 없이 `_headers` 로 다시 업로드 |

---

## 9. `/api/sheet` 응답 규격

### 성공 시

- 상태 코드: `200`
- Content-Type: `text/csv; charset=utf-8`
- 본문: Google 원본 CSV 그대로

응답 헤더:

| 헤더 | 의미 |
|---|---|
| `X-BB-Source` | `live` (실시간 수신 성공) |
| `X-BB-Fetched-At` | 수신 시각 (ISO 형식) |
| `X-BB-Raw-Rows` | 원본 CSV 행 수 (따옴표 안 줄바꿈 제외) |
| `X-BB-Upstream-Status` | Google이 준 HTTP 상태 |
| `X-BB-Elapsed-Ms` | 수신에 걸린 시간(ms) |

### 실패 시

- 상태 코드: `502`
- Content-Type: `application/json; charset=utf-8`

```json
{
  "ok": false,
  "source": "error",
  "error": "HTML_INSTEAD_OF_CSV",
  "detail": "Google이 CSV 대신 HTML 페이지를 반환했습니다. ...",
  "at": "2026-08-14T09:00:00.000Z"
}
```

대시보드는 이 응답을 받으면 **저장본 모드로 전환**합니다.

### 참고 옵션

`/api/sheet?format=json` 으로 호출하면 CSV 본문과 메타데이터를 JSON으로 함께 받습니다.
(진단·디버깅용)

---

## 10. 공식 문서 링크

배포 화면이 이 문서와 다르면 아래 공식 문서를 기준으로 하세요.

- Pages Functions 시작하기 — https://developers.cloudflare.com/pages/functions/
- 파일 경로 → URL 규칙 (라우팅) — https://developers.cloudflare.com/pages/functions/routing/
- Git 연동 배포 — https://developers.cloudflare.com/pages/get-started/git-integration/
- `_headers` 파일 규격 — https://developers.cloudflare.com/pages/configuration/headers/
- 빌드 설정 — https://developers.cloudflare.com/pages/configuration/build-configuration/

---

## 11. 변경 이력

| Rev | 날짜 | 내용 |
|---|---|---|
| 1.0.0 | 2026-08-14 | Cloudflare Pages 배포 대응. `functions/api/sheet.js` 중계기 신규 작성, `_headers` 캐시 차단 설정 추가, README 작성 |

### 다음 예정 작업

`index.html` 수정은 아직 진행되지 않았습니다. 다음 항목이 남아 있습니다.

- [ ] GitHub Pages 전용 `sheet-data.csv` 강제 사용 코드 제거
- [ ] 데이터 로딩부를 `/api/sheet` 우선 방식으로 교체
- [ ] 1분 자동 동기화 타이머 추가
- [ ] 실시간 / 저장본 구분 배지 추가
- [ ] 진단 패널 추가 (성공 시각, 원본 행 수, 반영 건수, 제외 건수)
- [ ] 제외 사유 분류 표시 (날짜 누락 / 빈 행 / 헤더 불일치 / 파싱 실패)
- [ ] `index.html` 내 빌드 버전 및 Revision 갱신
