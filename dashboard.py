"""Serve the local GDACS explorer using only Python's standard library."""
import argparse
import csv
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / '.venv/data/gdacs_global_events_2024-10-16_to_2026-10-16.csv'


def load_events(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        required = {'event_uid', 'event_type', 'start_date_utc', 'end_date_utc',
                    'latitude', 'longitude', 'alert_level', 'affected_country_iso3'}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing CSV columns: {", ".join(sorted(missing))}')
        return list(reader)


def make_handler(events):
    payload = json.dumps(events, ensure_ascii=False).encode('utf-8')

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/api/events':
                body, mime = payload, 'application/json; charset=utf-8'
            elif path in ('/', '/index.html'):
                body = (ROOT / 'dashboard.html').read_bytes()
                mime = 'text/html; charset=utf-8'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--port', type=int, default=8050)
    args = parser.parse_args()
    events = load_events(args.data)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(events))
    print(f'GDACS explorer: http://127.0.0.1:{args.port} ({len(events):,} events)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
