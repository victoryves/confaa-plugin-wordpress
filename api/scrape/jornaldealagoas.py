import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
import re
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup

from lib.scraper_base import BaseScraper, Article

BASE = "https://www.jornaldealagoas.com.br"


class JornalDeAlagoasScraper(BaseScraper):
    site_name = "jornaldealagoas.com.br"
    listing_url = "https://jornaldealagoas.com.br/"

    def get_article_links(self, soup: BeautifulSoup) -> list[str]:
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if not isinstance(href, str):
                continue
            if href.startswith("/") and re.search(r"/20\d{2}/\d{2}/\d{2}/", href):
                href = BASE + href
            # Pattern: /category/YYYY/MM/DD/ID-slug
            if "jornaldealagoas.com.br" in href and re.search(r"/20\d{2}/\d{2}/\d{2}/", href):
                if href not in links:
                    links.append(href)
        return links[:20]

    def parse_article(self, soup: BeautifulSoup, url: str) -> Article | None:
        title_el = (
            soup.select_one("h1")
            or soup.select_one("h2.title")
            or soup.select_one("h2")
        )
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        content_el = soup.select_one("article") or soup.select_one(".news-body") or soup.select_one("main")
        if content_el:
            paragraphs = content_el.select("p")
            body = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            body = ""

        first_para = body.split("\n")[0] if body else ""

        img_el = (
            soup.select_one("img[src*='digitaloceanspaces.com']")
            or soup.select_one("article img")
            or soup.select_one(".news-img img")
        )
        image_url = img_el.get("src") if img_el else None

        return Article(url=url, title=title, body=body, image_url=image_url, first_paragraph=first_para)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "jornaldealagoas scraper ready"}).encode())
