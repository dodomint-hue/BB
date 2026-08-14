/**
 * ============================================================================
 *  BBTECH T-PJT Dashboard — Google Sheets CSV 실시간 중계기
 *  Cloudflare Pages Functions
 * ----------------------------------------------------------------------------
 *  파일 위치 : functions/api/sheet.js
 *  접속 주소 : https://<사이트주소>/api/sheet
 *
 *  하는 일
 *   1. 브라우저 대신 Cloudflare 서버가 Google 게시 CSV를 직접 받아온다.
 *      (브라우저가 Google을 직접 부르면 CORS 차단 + 캐시 문제가 생김)
 *   2. 요청할 때마다 캐시 무효화 파라미터를 붙여 항상 최신본을 받는다.
 *   3. Google이 CSV 대신 HTML 오류 페이지를 주면 감지해서 에러로 처리한다.
 *   4. 응답에 진단용 헤더(수신 시각, 원본 행 수 등)를 붙여 돌려준다.
 *
 *  Build   : 2026-08-14
 *  Rev     : 1.0.0  (최초 작성 — Cloudflare Pages 배포 대응)
 * ============================================================================
 */

/** Google 스프레드시트 "웹에 게시" CSV 주소 */
const SHEET_CSV_URL =
  "https://docs.google.com/spreadsheets/d/e/2PACX-1vT36CbuNbqhSsvck-jwOeCDpP6wUjnjymBCx_4DNjmMfv7yFibZAgF4xxGsc6p-JroqNOg_yTPr-1Im/pub?output=csv";

/** Google 응답을 기다리는 최대 시간 (밀리초) */
const UPSTREAM_TIMEOUT_MS = 20000;

/** 브라우저·중간 서버 모두 캐시하지 못하게 하는 값 */
const NO_STORE = "no-store, no-cache, must-revalidate, max-age=0";

/** 대시보드가 읽을 수 있도록 노출할 커스텀 헤더 목록 */
const EXPOSED_HEADERS = [
  "X-BB-Source",
  "X-BB-Fetched-At",
  "X-BB-Raw-Rows",
  "X-BB-Upstream-Status",
  "X-BB-Upstream-Content-Type",
  "X-BB-Elapsed-Ms",
  "X-BB-Error",
  "X-BB-Error-Detail",
].join(", ");

/** 모든 응답에 공통으로 붙는 헤더 */
function baseHeaders(extra) {
  return Object.assign(
    {
      "Cache-Control": NO_STORE,
      Pragma: "no-cache",
      Expires: "0",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Expose-Headers": EXPOSED_HEADERS,
      "X-Content-Type-Options": "nosniff",
    },
    extra || {}
  );
}

/** 실패 응답을 JSON 형태로 만들어 준다 (대시보드는 이걸 보고 저장본으로 전환) */
function fail(code, detail, status, extra) {
  const at = new Date().toISOString();
  const body = JSON.stringify(
    { ok: false, source: "error", error: code, detail: String(detail), at: at },
    null,
    2
  );
  return new Response(body, {
    status: status || 502,
    headers: baseHeaders(
      Object.assign(
        {
          "Content-Type": "application/json; charset=utf-8",
          "X-BB-Source": "error",
          "X-BB-Fetched-At": at,
          "X-BB-Error": code,
          "X-BB-Error-Detail": encodeURIComponent(String(detail).slice(0, 300)),
        },
        extra || {}
      )
    ),
  });
}

/**
 * CSV 레코드(행) 개수를 센다.
 * 큰따옴표 안에 들어 있는 줄바꿈은 행 구분으로 세지 않는다.
 * 완전히 빈 줄은 세지 않는다.
 */
function countCsvRecords(text) {
  let rows = 0;
  let inQuotes = false;
  let hasContent = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];

    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') i++; // 이스케이프된 따옴표("")
        else inQuotes = false;
      }
      continue;
    }

    if (ch === '"') {
      inQuotes = true;
      hasContent = true;
      continue;
    }
    if (ch === "\r") {
      if (text[i + 1] === "\n") i++;
      if (hasContent) rows++;
      hasContent = false;
      continue;
    }
    if (ch === "\n") {
      if (hasContent) rows++;
      hasContent = false;
      continue;
    }
    hasContent = true;
  }
  if (hasContent) rows++;
  return rows;
}

/** 응답 본문이 CSV가 아니라 HTML 페이지인지 판별 */
function looksLikeHtml(text, contentType) {
  if (contentType && contentType.indexOf("text/html") !== -1) return true;
  return /^\s*(<!doctype|<html|<head\b|<meta\b|<body\b)/i.test(text.slice(0, 300));
}

/** CORS 사전 요청 대응 */
export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: baseHeaders({
      "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
      "Access-Control-Allow-Headers": "*",
      "Access-Control-Max-Age": "86400",
    }),
  });
}

/** 실제 처리: GET /api/sheet */
export async function onRequestGet(context) {
  const startedAt = Date.now();
  const reqUrl = new URL(context.request.url);
  const wantJson = reqUrl.searchParams.get("format") === "json";

  // 1) 캐시 무효화용 파라미터를 붙인 Google 주소 만들기
  const sep = SHEET_CSV_URL.indexOf("?") !== -1 ? "&" : "?";
  const upstreamUrl = SHEET_CSV_URL + sep + "_cb=" + Date.now().toString(36);

  // 2) 타임아웃 준비
  const controller = new AbortController();
  const timer = setTimeout(function () {
    controller.abort();
  }, UPSTREAM_TIMEOUT_MS);

  // 3) Google 호출
  let res;
  try {
    res = await fetch(upstreamUrl, {
      method: "GET",
      redirect: "follow",
      signal: controller.signal,
      cf: { cacheTtl: 0, cacheEverything: false }, // Cloudflare 엣지 캐시도 사용 안 함
      headers: {
        Accept: "text/csv, text/plain, */*",
        "Cache-Control": "no-cache",
        Pragma: "no-cache",
        "User-Agent": "BBTECH-Dashboard (Cloudflare Pages Function)",
      },
    });
  } catch (err) {
    clearTimeout(timer);
    const aborted = err && err.name === "AbortError";
    return fail(
      aborted ? "UPSTREAM_TIMEOUT" : "UPSTREAM_UNREACHABLE",
      aborted
        ? "Google 응답이 " + UPSTREAM_TIMEOUT_MS + "ms 안에 오지 않았습니다."
        : (err && err.message) || err
    );
  }
  clearTimeout(timer);

  const upstreamStatus = String(res.status);
  const contentType = (res.headers.get("content-type") || "").toLowerCase();

  // 4) HTTP 상태 확인
  if (!res.ok) {
    return fail(
      "UPSTREAM_HTTP_" + res.status,
      "Google 응답 상태: " + res.status + " " + res.statusText,
      502,
      {
        "X-BB-Upstream-Status": upstreamStatus,
        "X-BB-Upstream-Content-Type": contentType,
      }
    );
  }

  // 5) 본문 읽기
  let text;
  try {
    text = await res.text();
  } catch (err) {
    return fail("UPSTREAM_BODY_READ_FAILED", (err && err.message) || err, 502, {
      "X-BB-Upstream-Status": upstreamStatus,
    });
  }

  // BOM 제거
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);

  // 6) HTML 오류 페이지 감지 (요구사항 12)
  if (looksLikeHtml(text, contentType)) {
    return fail(
      "HTML_INSTEAD_OF_CSV",
      "Google이 CSV 대신 HTML 페이지를 반환했습니다. 스프레드시트의 '웹에 게시' 상태와 게시 링크를 확인하세요.",
      502,
      {
        "X-BB-Upstream-Status": upstreamStatus,
        "X-BB-Upstream-Content-Type": contentType,
      }
    );
  }

  // 7) 빈 응답 감지
  if (!text.trim()) {
    return fail("EMPTY_BODY", "Google이 빈 본문을 반환했습니다.", 502, {
      "X-BB-Upstream-Status": upstreamStatus,
      "X-BB-Upstream-Content-Type": contentType,
    });
  }

  // 8) 정상 — 진단 정보와 함께 CSV 그대로 전달
  const fetchedAt = new Date().toISOString();
  const rawRows = countCsvRecords(text);
  const elapsedMs = Date.now() - startedAt;

  const meta = {
    "X-BB-Source": "live",
    "X-BB-Fetched-At": fetchedAt,
    "X-BB-Raw-Rows": String(rawRows),
    "X-BB-Upstream-Status": upstreamStatus,
    "X-BB-Upstream-Content-Type": contentType,
    "X-BB-Elapsed-Ms": String(elapsedMs),
  };

  if (wantJson) {
    return new Response(
      JSON.stringify({
        ok: true,
        source: "live",
        fetchedAt: fetchedAt,
        rawRows: rawRows,
        elapsedMs: elapsedMs,
        upstreamStatus: res.status,
        contentType: contentType,
        csv: text,
      }),
      {
        status: 200,
        headers: baseHeaders(
          Object.assign({ "Content-Type": "application/json; charset=utf-8" }, meta)
        ),
      }
    );
  }

  return new Response(text, {
    status: 200,
    headers: baseHeaders(
      Object.assign({ "Content-Type": "text/csv; charset=utf-8" }, meta)
    ),
  });
}
