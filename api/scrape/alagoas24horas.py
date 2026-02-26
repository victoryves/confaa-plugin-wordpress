import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from http.server import BaseHTTPRequestHandler
import json

from lib.scraper_base import BaseScraper, Article
from lib.supabase_client import get_filter_keywords


class Alagoas24HorasScraper(BaseScraper):
    site_name = "alagoas24horas.com.br"
    listing_url = "https://www.alagoas24horas.com.br/"

    def get_article_links(self, page) -> list[str]:
        links = []
        for a in page.css("a[href]"):
            href = a.attrib.get("href", "")
            if "alagoas24horas.com.br/" in href and len(href) > 35:
                if href not in links:
                    links.append(href)
        return links[:20]

    def parse_article(self, page, url: str) -> Article | None:
        title_el = page.css_first("h1") or page.css_first(".entry-title") or page.css_first(".news-title")
        if title_el is None:
            return None
        title = title_el.text.strip()

        body_el = page.css_first(".entry-content") or page.css_first(".news-body") or page.css_first("article")
        body = body_el.text.strip() if body_el else ""

        first_para = ""
        p = page.css_first(".entry-content p") or page.css_first("article p")
        if p:
            first_para = p.text.strip()

        img_el = page.css_first(".wp-post-image") or page.css_first(".entry-content img") or page.css_first("article img")
        image_url = img_el.attrib.get("src") if img_el else None

        return Article(url=url, title=title, body=body, image_url=image_url, first_paragraph=first_para)


def handler(request):
    scraper = Alagoas24HorasScraper()
    result = scraper.run(blacklist=get_filter_keywords())
    return {
        "statusCode": 200,
        "body": json.dumps({
            "site": result.source_site,
            "found": result.articles_found,
            "published": result.articles_published,
            "filtered": result.articles_filtered,
            "error": result.error,
        }),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = handler(None)
        self.send_response(result["statusCode"])
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(result["body"].encode())
