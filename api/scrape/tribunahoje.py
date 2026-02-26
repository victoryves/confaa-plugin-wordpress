import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
import re
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup

from lib.scraper_base import BaseScraper, Article

BASE = "https://tribunahoje.com"


class TribunaHojeScraper(BaseScraper):
    site_name = "tribunahoje.com"
    listing_url = "https://tribunahoje.com/"

    def get_article_links(self, soup: BeautifulSoup) -> list[str]:
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if not isinstance(href, str):
                continue
            if href.startswith("/noticias/"):
                href = BASE + href
            # Article URLs: /noticias/category/YYYY/MM/DD/ID-slug
            if "/noticias/" in href and re.search(r"/20\d{2}/\d{2}/\d{2}/", href):
                if href not in links:
                    links.append(href)
        return links[:20]

    def parse_article(self, soup: BeautifulSoup, url: str) -> Article | None:
        # Real article title is in h1.news-header__title (h1 alone picks up category name)
        title_el = soup.select_one("h1.news-header__title")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        # Body: <p> tags inside section.news-content
        content_el = soup.select_one("section.news-content") or soup.select_one("article")
        if content_el:
            paragraphs = content_el.select("p")
            body = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            body = ""

        first_para = body.split("\n")[0] if body else ""

        # Image inside <figure> > <picture> > <img>
        img_el = (
            soup.select_one("header.news-header figure picture img")
            or soup.select_one("figure picture img")
            or soup.select_one("img[src*='s3.tribunahoje.com']")
        )
        image_url = img_el.get("src") if img_el else None

        return Article(url=url, title=title, body=body, image_url=image_url, first_paragraph=first_para)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "tribunahoje scraper ready"}).encode())
