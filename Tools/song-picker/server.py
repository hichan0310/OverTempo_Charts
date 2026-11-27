"""OverTempo 수록 후보 곡 고르기 — 로컬 서버.

실행: python3 server.py [포트]   (기본 5310, 이 컴퓨터에서만 접속: http://127.0.0.1:5310/)
체크 결과는 같은 폴더의 picks.json에 저장된다.
"""
import json, os, sys, tempfile, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

HERE = Path(__file__).resolve().parent
PICKS = HERE / 'picks.json'
LOCK = threading.Lock()
VALID = {'like', 'maybe', 'no'}


def page() -> bytes:
    data = json.loads((HERE / 'songs.json').read_text(encoding='utf-8'))
    songs = json.dumps(data['songs'], ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = (HERE / 'template.html').read_text(encoding='utf-8')
    return html.replace('__SONGS__', songs).replace('__CUT__', str(data['cut'])).replace('__TOTAL__', str(data['total'])).encode()


def read_picks() -> dict:
    try:
        return json.loads(PICKS.read_text(encoding='utf-8')).get('picks', {})
    except FileNotFoundError:
        return {}


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body: bytes, ctype='application/json; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path in ('/', '/index.html'):
            self.send(200, page(), 'text/html; charset=utf-8')
        elif path == '/api/picks':
            with LOCK:
                self.send(200, json.dumps({'picks': read_picks()}, ensure_ascii=False).encode())
        else:
            self.send(404, b'{"error":"not found"}')

    def do_PUT(self):
        if self.path.split('?')[0] != '/api/picks':
            return self.send(404, b'{"error":"not found"}')
        try:
            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
            picks = {str(k): v for k, v in body.get('picks', {}).items() if v in VALID}
        except Exception:
            return self.send(400, b'{"error":"bad json"}')
        with LOCK:
            fd, tmp = tempfile.mkstemp(dir=HERE, prefix='.picks-', suffix='.json')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump({'picks': picks}, f, ensure_ascii=False, indent=1)
            os.replace(tmp, PICKS)
        self.send(200, json.dumps({'ok': True, 'count': len(picks)}).encode())

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5310
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'곡 고르기: http://127.0.0.1:{port}/', flush=True)
    server.serve_forever()
