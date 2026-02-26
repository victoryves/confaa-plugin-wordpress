import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup

from lib.scraper_base import BaseScraper, Article


class TNH1Scraper(BaseScraper):
    site_name = "tnh1.com.br"
    listing_url = "https://tnh1.com.br/"

    def get_article_links(self, soup: BeautifulSoup) -> list[str]:
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if isinstance(href, str) and href.startswith("https://tnh1.com.br/") and len(href) > 25:
                if href not in links:
                    links.append(href)
        return links[:20]

    def parse_article(self, soup: BeautifulSoup, url: str) -> Article | None:
        title_el = soup.select_one("h1.entry-title") or soup.select_one("h1") or soup.select_one(".titulo")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        body_el = soup.select_one(".entry-content") or soup.select_one(".texto-noticia") or soup.select_one("article")
        body = body_el.get_text(separator="\n", strip=True) if body_el else ""

        first_para = ""
        p = (body_el or soup).select_one("p")
        if p:
            first_para = p.get_text(strip=True)

        img_el = soup.select_one(".wp-post-image") or soup.select_one(".entry-content img") or soup.select_one("article img")
        image_url = img_el.get("src") if img_el else None

        return Article(url=url, title=title, body=body, image_url=image_url, first_paragraph=first_para)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "tnh1 scraper ready"}).encode())
