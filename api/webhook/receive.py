"""
Endpoint chamado pelo plugin WordPress para disparar o scraping.

POST /api/webhook/receive
Headers: Authorization: Bearer <api_secret_key>
Body JSON: {
    "wp_url": "https://meusite.com",
    "wp_username": "admin",
    "wp_app_password": "xxxx xxxx xxxx xxxx",
    "post_status": "publish"   (opcional, default: publish)
}
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
import os as _os
from http.server import BaseHTTPRequestHandler

from api.scrape.index import run_all

REQUIRED_FIELDS = {"wp_url", "wp_username", "wp_app_password"}


def _authenticate(headers: dict, api_secret: str | None) -> bool:
    """
    Valida o Bearer token enviado pelo plugin WP.
    Se o plugin não configurou api_secret, aceita qualquer requisição.
    """
    if not api_secret:
        return True
    auth = headers.get("authorization") or headers.get("Authorization", "")
    return auth == f"Bearer {api_secret}"


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length)) if length else {}
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON body"})
            return

        # Valida o secret key enviado no header com o que veio no body
        api_secret = body.get("api_secret_key") or _os.environ.get("API_SECRET_KEY", "")
        if not _authenticate(dict(self.headers), api_secret):
            self._respond(401, {"error": "Unauthorized"})
            return

        missing = REQUIRED_FIELDS - body.keys()
        if missing:
            self._respond(400, {"error": f"Missing fields: {list(missing)}"})
            return

        credentials = {
            "wp_url": body["wp_url"],
            "wp_username": body["wp_username"],
            "wp_app_password": body["wp_app_password"],
            "post_status": body.get("post_status", "publish"),
        }

        try:
            data = run_all(credentials=credentials)
            self._respond(200, data)
        except Exception as exc:
            self._respond(500, {"error": str(exc)})

    def do_GET(self):
        self._respond(200, {"status": "ok"})

    def _respond(self, code: int, data: dict) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
