import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
import re
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup

from lib.scraper_base import BaseScraper, Article

BASE = "https://www.gazetaweb.com"


class GazetaWebScraper(BaseScraper):
    site_name = "gazetaweb.com"
    listing_url = "https://www.gazetaweb.com/"

    def get_article_links(self, soup: BeautifulSoup) -> list[str]:
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if not isinstance(href, str):
                continue
            if href.startswith("/noticias/"):
                href = BASE + href
            # Article URLs end with a 6-digit numeric ID
            if "/noticias/" in href and re.search(r"-\d{5,7}$", href):
                if href not in links:
                    links.append(href)
        return links[:20]

    def parse_article(self, soup: BeautifulSoup, url: str) -> Article | None:
        title_el = (
            soup.select_one(".gzw-article h1")
            or soup.select_one("header h1")
            or soup.select_one("h1")
        )
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        body_el = soup.select_one("#article") or soup.select_one("article")
        if body_el:
            paragraphs = body_el.select("p")
            body = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            body = ""

        first_para = body.split("\n")[0] if body else ""

        img_el = (
            soup.select_one(".article-destaque img")
            or soup.select_one(".article-destaque picture img")
            or soup.select_one("article img")
        )
        image_url = img_el.get("src") if img_el else None

        return Article(url=url, title=title, body=body, image_url=image_url, first_paragraph=first_para)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "gazetaweb scraper ready"}).encode())
