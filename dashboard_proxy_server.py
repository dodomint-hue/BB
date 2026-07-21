from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
import os
import sys


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vT36CbuNbqhSsvck-jwOeCDpP6wUjnjymBCx_4DNjmMfv7yFibZAgF4xxGsc6p-JroqNOg_yTPr-1Im"
    "/pub?output=csv"
)
HTML_FILE = "BBtech_Dashboard_Auto_google_sheet_sync_fixed.html"
URL_FILE = BASE_DIR / "dashboard_server_url.txt"


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


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/" + HTML_FILE)
            self.end_headers()
            return

        if parsed.path == "/gsheet-csv":
            qs = parse_qs(parsed.query)
            url = qs.get("url", [DEFAULT_CSV_URL])[0] or DEFAULT_CSV_URL
            if not allowed_google_csv(url):
                self.send_error(400, "Only published Google Sheets CSV URLs are allowed")
                return
            try:
                req = Request(url, headers={"User-Agent": "BBTECH-Dashboard/1.0"})
                with urlopen(req, timeout=30) as resp:
                    data = resp.read()
            except Exception as exc:
                self.send_error(502, "Google Sheets fetch failed: " + str(exc))
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        return super().do_GET()

    def log_message(self, fmt, *args):
        sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()


def main():
    os.chdir(BASE_DIR)
    host = "127.0.0.1"
    start_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    last_error = None
    for port in range(start_port, start_port + 30):
        try:
            httpd = ThreadingHTTPServer((host, port), Handler)
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
