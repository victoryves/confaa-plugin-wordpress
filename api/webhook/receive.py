"""
Webhook endpoint called by the WordPress plugin to trigger a scrape run.
Expects: POST with Authorization: Bearer <API_SECRET_KEY>
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
import os as _os
from http.server import BaseHTTPRequestHandler

from api.scrape.index import run_all


def _authenticate(headers: dict) -> bool:
    expected = _os.environ.get("API_SECRET_KEY", "")
    if not expected:
        return True
    auth = headers.get("authorization") or headers.get("Authorization", "")
    return auth == f"Bearer {expected}"


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not _authenticate(dict(self.headers)):
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized"}')
            return

        try:
            data = run_all()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as exc:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode())

    def do_GET(self):
        # Health check
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
