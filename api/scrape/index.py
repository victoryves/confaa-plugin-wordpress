"""
Orchestrator — chama cada scraper sequencialmente.
Recebe as credenciais do WordPress via payload (enviadas pelo plugin WP).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
from http.server import BaseHTTPRequestHandler

from api.scrape.cadaminuto import CadaMinutoScraper
from api.scrape.tnh1 import TNH1Scraper
from api.scrape.gazetaweb import GazetaWebScraper
from api.scrape.tribunahoje import TribunaHojeScraper
from api.scrape.jornaldealagoas import JornalDeAlagoasScraper
from api.scrape.alagoas24horas import Alagoas24HorasScraper
from api.scrape.agoraalagoas import AgoraAlagoasScraper
from lib.supabase_client import get_filter_keywords

SCRAPERS = [
    CadaMinutoScraper,
    TNH1Scraper,
    GazetaWebScraper,
    TribunaHojeScraper,
    JornalDeAlagoasScraper,
    Alagoas24HorasScraper,
    AgoraAlagoasScraper,
]

REQUIRED_CREDENTIALS = {"wp_url", "wp_username", "wp_app_password"}


def run_all(credentials: dict) -> dict:
    blacklist = get_filter_keywords()
    summary = []
    for scraper_cls in SCRAPERS:
        try:
            result = scraper_cls().run(credentials=credentials, blacklist=blacklist)
            summary.append({
                "site": result.source_site,
                "found": result.articles_found,
                "published": result.articles_published,
                "filtered": result.articles_filtered,
                "error": result.error,
            })
        except Exception as exc:
            summary.append({"site": scraper_cls.site_name, "error": str(exc)})
    return {"results": summary}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        missing = REQUIRED_CREDENTIALS - body.keys()
        if missing:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Missing fields: {missing}"}).encode())
            return

        data = run_all(credentials=body)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
