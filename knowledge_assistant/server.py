from __future__ import annotations

import json
import pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .assistant import ask
from .cli import AUDIT, load_index
from .llm import LLMError, get_llm
from .security import ROLES


class Handler(BaseHTTPRequestHandler):
    index = None

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            return self._send(200, (pathlib.Path(__file__).parent / "static/index.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/roles":
            return self._send(200, json.dumps(list(ROLES)).encode())
        self._send(404, b"{}")

    def do_POST(self):
        if self.path != "/api/ask":
            return self._send(404, b"{}")
        try:
            n = int(self.headers.get("content-length", 0))
            if n > 20000:
                return self._send(413, b'{"error":"too large"}')
            req = json.loads(self.rfile.read(n))
            r = ask(req["question"], req.get("role", "employee"), Handler.index, get_llm(req.get("provider") or "mock"), audit_path=AUDIT)
            self._send(200, json.dumps(r).encode())
        except (LLMError, ValueError, KeyError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode())

    def log_message(self, *a):
        pass


def serve(port=8081):
    Handler.index = load_index()
    print(f"http://localhost:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
