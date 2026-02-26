"""
Dry-run endpoint — scrapa os sites mas NÃO publica no WordPress.
Retorna o que seria publicado: título, URL, categoria, status do filtro.

GET /api/preview           → testa todos os 7 sites
GET /api/preview?site=tnh1 → testa um site específico
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests as http_requests
from bs4 import BeautifulSoup

from lib.classifier import classify_article
from lib.filter import is_violent_content, DEFAULT_BLACKLIST
from lib.supabase_client import is_url_published
from lib.scraper_base import fetch_page

from api.scrape.cadaminuto    import CadaMinutoScraper
from api.scrape.tnh1          import TNH1Scraper
from api.scrape.gazetaweb     import GazetaWebScraper
from api.scrape.tribunahoje   import TribunaHojeScraper
from api.scrape.jornaldealagoas import JornalDeAlagoasScraper
from api.scrape.alagoas24horas  import Alagoas24HorasScraper
from api.scrape.agoraalagoas    import AgoraAlagoasScraper

SCRAPERS = {
    "cadaminuto":    CadaMinutoScraper,
    "tnh1":          TNH1Scraper,
    "gazetaweb":     GazetaWebScraper,
    "tribunahoje":   TribunaHojeScraper,
    "jornaldealagoas": JornalDeAlagoasScraper,
    "alagoas24horas":  Alagoas24HorasScraper,
    "agoraalagoas":    AgoraAlagoasScraper,
}


def preview_scraper(scraper_cls, max_articles: int = 5) -> dict:
    scraper = scraper_cls()
    result = {
        "site": scraper.site_name,
        "listing_url": scraper.listing_url,
        "links_found": 0,
        "articles": [],
        "error": None,
    }
    try:
        soup = fetch_page(scraper.listing_url)
        if soup is None:
            result["error"] = "Failed to fetch listing page"
            return result

        links = scraper.get_article_links(soup)
        result["links_found"] = len(links)

        for link in links[:max_articles]:
            entry = {"url": link, "status": None, "title": None, "category": None, "reason": None}
            try:
                if is_url_published(link):
                    entry["status"] = "skip"
                    entry["reason"] = "already published"
                    result["articles"].append(entry)
                    continue

                time.sleep(0.8)
                article_soup = fetch_page(link)
                if article_soup is None:
                    entry["status"] = "skip"
                    entry["reason"] = "fetch failed"
                    result["articles"].append(entry)
                    continue

                article = scraper.parse_article(article_soup, link)
                if article is None:
                    entry["status"] = "skip"
                    entry["reason"] = "parse failed"
                    result["articles"].append(entry)
                    continue

                entry["title"] = article.title

                if is_violent_content(article.title, article.body, DEFAULT_BLACKLIST):
                    entry["status"] = "filtered"
                    entry["reason"] = "violence/police content"
                else:
                    entry["status"] = "would_publish"
                    entry["category"] = classify_article(
                        article.title,
                        article.first_paragraph or article.body[:300]
                    )
                    entry["image_url"] = article.image_url
                    entry["body_preview"] = article.body[:200].replace("\n", " ")

            except Exception as exc:
                entry["status"] = "error"
                entry["reason"] = str(exc)

            result["articles"].append(entry)

    except Exception as exc:
        result["error"] = str(exc)

    return result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        site_filter = qs.get("site", [None])[0]

        if site_filter:
            if site_filter not in SCRAPERS:
                self._respond(400, {"error": f"Unknown site. Options: {list(SCRAPERS.keys())}"})
                return
            scrapers_to_run = {site_filter: SCRAPERS[site_filter]}
        else:
            scrapers_to_run = SCRAPERS

        results = []
        for key, cls in scrapers_to_run.items():
            results.append(preview_scraper(cls, max_articles=5))

        self._respond(200, {"preview": results, "total_sites": len(results)})

    def _respond(self, code: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
