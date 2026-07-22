from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen
import hashlib
import json
import os
import re
import sys
import time
import traceback


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vT36CbuNbqhSsvck-jwOeCDpP6wUjnjymBCx_4DNjmMfv7yFibZAgF4xxGsc6p-JroqNOg_yTPr-1Im"
    "/pub?output=csv"
)
LOCAL_HTML_FILE = "BBtech_Dashboard_Auto_google_sheet_sync_fixed.html"
HTML_FILE = LOCAL_HTML_FILE if (BASE_DIR / LOCAL_HTML_FILE).is_file() else "index.html"
BUILD_ID = "2026-07-22.2"
URL_FILE = BASE_DIR / "dashboard_server_url.txt"
ERROR_LOG = BASE_DIR.parent / "work" / "dashboard_proxy_error.log"


def allowed_google_csv(url):
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme != "https" or parsed.netloc.lower() != "docs.google.com":
        return False
    if not parsed.path.startswith("/spreadsheets/d/e/"):
        return False
    qs = parse_qs(parsed.query)
    return qs.get("output", [""])[0].lower() == "csv"


def uncached_url(url):
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["bbtech_refresh"] = str(int(time.time() * 1000))
    return urlunparse(parsed._replace(query=urlencode(query)))


class Handler(SimpleHTTPRequestHandler):
    csv_cache = None
    csv_cache_time = None
    csv_cache_hash = None

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            data = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path == "/build":
            data = BUILD_ID.encode("ascii")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=ascii")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/%s?v=%s" % (HTML_FILE, BUILD_ID))
            self.end_headers()
            return

        if parsed.path == "/" + HTML_FILE:
            requested_build = parse_qs(parsed.query).get("v", [""])[0]
            if requested_build != BUILD_ID:
                self.send_response(302)
                self.send_header("Location", "/%s?v=%s" % (HTML_FILE, BUILD_ID))
                self.end_headers()
                return

        if parsed.path == "/download/github-package":
            zip_path = BASE_DIR / "bbtech-dashboard-github.zip"
            if not zip_path.is_file():
                self.send_error(404, "GitHub package not found")
                return
            data = zip_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header(
                "Content-Disposition",
                'attachment; filename="bbtech-dashboard-github.zip"',
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path in ("/gsheet-csv", "/gsheet-jsonp"):
            qs = parse_qs(parsed.query)
            url = qs.get("url", [DEFAULT_CSV_URL])[0] or DEFAULT_CSV_URL
            if not allowed_google_csv(url):
                self.send_error(400, "Only published Google Sheets CSV URLs are allowed")
                return
            data = None
            last_error = None
            for attempt in range(2):
                try:
                    req = Request(
                        uncached_url(url),
                        headers={
                            "User-Agent": "BBTECH-Dashboard/1.1",
                            "Accept": "text/csv,*/*;q=0.8",
                            "Cache-Control": "no-cache",
                            "Pragma": "no-cache",
                        },
                    )
                    with urlopen(req, timeout=45) as resp:
                        data = resp.read()
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt == 0:
                        time.sleep(0.8)
            stale = False
            if data is None:
                if Handler.csv_cache:
                    data = Handler.csv_cache
                    stale = True
                else:
                    try:
                        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
                        with ERROR_LOG.open("a", encoding="utf-8") as log:
                            log.write("\n%s upstream fetch failed: %r\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), last_error))
                    except Exception:
                        pass
                    self.send_error(502, "Google Sheets upstream fetch failed")
                    return
            else:
                Handler.csv_cache = data
                Handler.csv_cache_time = int(time.time())
                Handler.csv_cache_hash = hashlib.sha256(data).hexdigest()[:16]

            fetched_at = Handler.csv_cache_time or int(time.time())
            content_hash = Handler.csv_cache_hash or hashlib.sha256(data).hexdigest()[:16]

            if parsed.path == "/gsheet-jsonp":
                callback = qs.get("callback", [""])[0]
                if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]{0,127}", callback):
                    self.send_error(400, "Invalid JSONP callback")
                    return
                csv_text = data.decode("utf-8-sig", errors="replace")
                payload = (callback + "(" + json.dumps(csv_text, ensure_ascii=False) + ");").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("X-BBTECH-Fetched-At", str(fetched_at))
                self.send_header("X-BBTECH-Content-Hash", content_hash)
                if stale:
                    self.send_header("X-BBTECH-Cache", "stale")
                self.end_headers()
                self.wfile.write(payload)
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-BBTECH-Fetched-At", str(fetched_at))
            self.send_header("X-BBTECH-Content-Hash", content_hash)
            if stale:
                self.send_header("X-BBTECH-Cache", "stale")
            self.end_headers()
            self.wfile.write(data)
            return

        return super().do_GET()

    def log_message(self, fmt, *args):
        # 숨김 실행에서는 표준 출력 핸들이 닫힐 수 있으므로 요청 로그를 생략한다.
        return


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        try:
            ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
            with ERROR_LOG.open("a", encoding="utf-8") as log:
                log.write("\n%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), client_address))
                log.write(traceback.format_exc())
        except Exception:
            pass


def main():
    os.chdir(BASE_DIR)
    host = "127.0.0.1"
    start_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    last_error = None
    for port in range(start_port, start_port + 30):
        try:
            httpd = DashboardServer((host, port), Handler)
            break
        except OSError as exc:
            last_error = exc
    else:
        raise SystemExit("Could not bind local dashboard server: %s" % last_error)

    url = "http://%s:%s/%s" % (host, httpd.server_port, HTML_FILE)
    URL_FILE.write_text(url, encoding="utf-8")
    print("BBTECH dashboard server running:", url, flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
