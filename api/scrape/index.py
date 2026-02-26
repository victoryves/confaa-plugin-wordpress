"""
Orchestrator — calls each site-specific scraper sequentially.
Triggered by WP Cron via the /api/webhook/receive endpoint or directly.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
import os as _os
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


def _authenticate(request_headers: dict) -> bool:
    expected = _os.environ.get("API_SECRET_KEY", "")
    if not expected:
        return True  # No key configured — allow (should be set in production)
    auth = request_headers.get("authorization") or request_headers.get("Authorization", "")
    return auth == f"Bearer {expected}"


def run_all() -> dict:
    blacklist = get_filter_keywords()
    summary = []
    for scraper_cls in SCRAPERS:
        try:
            result = scraper_cls().run(blacklist=blacklist)
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
    def do_GET(self):
        if not _authenticate(dict(self.headers)):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized"}')
            return

        data = run_all()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        self.do_GET()
