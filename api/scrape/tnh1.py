import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup

from lib.scraper_base import BaseScraper, Article

BASE = "https://tnh1.com.br"


class TNH1Scraper(BaseScraper):
    site_name = "tnh1.com.br"
    listing_url = "https://tnh1.com.br/"

    def get_article_links(self, soup: BeautifulSoup) -> list[str]:
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if not isinstance(href, str):
                continue
            # Normalise relative URLs
            if href.startswith("/noticia/nid/"):
                href = BASE + href
            if "/noticia/nid/" in href:
                if href not in links:
                    links.append(href)
        return links[:20]

    def parse_article(self, soup: BeautifulSoup, url: str) -> Article | None:
        title_el = soup.select_one("h1")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        # Body: collect all <p> inside main content area
        content_el = (
            soup.select_one(".entry-content")
            or soup.select_one("article")
            or soup.select_one("main")
        )
        if content_el:
            paragraphs = content_el.select("p")
            body = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            body = ""

        first_para = body.split("\n")[0] if body else ""

        img_el = (
            soup.select_one("img[src*='media/_versions']")
            or soup.select_one(".entry-content img")
            or soup.select_one("article img")
        )
        image_url = img_el.get("src") if img_el else None
        if image_url and image_url.startswith("/"):
            image_url = BASE + image_url

        return Article(url=url, title=title, body=body, image_url=image_url, first_paragraph=first_para)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "tnh1 scraper ready"}).encode())
