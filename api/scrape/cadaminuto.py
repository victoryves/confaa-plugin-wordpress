import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup

from lib.scraper_base import BaseScraper, Article


class CadaMinutoScraper(BaseScraper):
    site_name = "cadaminuto.com.br"
    listing_url = "https://www.cadaminuto.com.br/"

    def get_article_links(self, soup: BeautifulSoup) -> list[str]:
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if isinstance(href, str) and "/noticia/" in href and "cadaminuto.com.br" in href:
                if href not in links:
                    links.append(href)
        return links[:20]

    def parse_article(self, soup: BeautifulSoup, url: str) -> Article | None:
        # cadaminuto uses h2 for article title, not h1
        title_el = (
            soup.select_one("h2.font-bold")
            or soup.select_one("h1")
            or soup.select_one("h2")
        )
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        # Body: div.post-content or fallback to article paragraphs
        body_el = soup.select_one("div.post-content") or soup.select_one("article")
        if body_el:
            paragraphs = body_el.select("p")
            body = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            body = ""

        first_para = body.split("\n")[0] if body else ""

        # Image: inside <picture> tag
        img_el = (
            soup.select_one("picture img")
            or soup.select_one("img[src*='cadaminuto']")
            or soup.select_one(".post-content img")
        )
        image_url = img_el.get("src") if img_el else None

        return Article(url=url, title=title, body=body, image_url=image_url, first_paragraph=first_para)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "cadaminuto scraper ready"}).encode())
