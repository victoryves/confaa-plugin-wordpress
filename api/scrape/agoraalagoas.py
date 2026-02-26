import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
import re
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup

from lib.scraper_base import BaseScraper, Article

BASE = "https://agoraalagoas.com"


class AgoraAlagoasScraper(BaseScraper):
    """
    Agora Alagoas usa Elementor (renderização JS).
    O HTML estático retorna metadados schema.org com as URLs dos artigos — usamos isso.
    """
    site_name = "agoraalagoas.com"
    listing_url = "https://agoraalagoas.com/"

    def get_article_links(self, soup: BeautifulSoup) -> list[str]:
        links = []

        # Estratégia 1: schema.org JSON-LD com lista de artigos
        import json as _json
        for script in soup.select("script[type='application/ld+json']"):
            try:
                data = _json.loads(script.string or "")
                # Pode ser lista ou objeto único
                items = data if isinstance(data, list) else [data]
                for item in items:
                    url = item.get("url") or item.get("@id") or ""
                    if "agoraalagoas.com" in str(url) and len(str(url)) > 30:
                        if url not in links:
                            links.append(url)
                    # ItemList entries
                    for entry in item.get("itemListElement", []):
                        u = entry.get("url") or entry.get("item", {}).get("url") or ""
                        if "agoraalagoas.com" in str(u) and len(str(u)) > 30:
                            if u not in links:
                                links.append(u)
            except Exception:
                pass

        # Estratégia 2: links com padrão de post WordPress (?p=ID ou /slug/)
        if not links:
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                if not isinstance(href, str):
                    continue
                if href.startswith("/"):
                    href = BASE + href
                if (
                    "agoraalagoas.com" in href
                    and not any(x in href for x in ["#", "sobre", "contato", "anuncie", "whatsapp"])
                    and len(href) > 30
                ):
                    if href not in links:
                        links.append(href)

        # Remove páginas de navegação e âncoras
        links = [l for l in links if "#" not in l and not l.rstrip("/") == BASE]
        return links[:20]

    def parse_article(self, soup: BeautifulSoup, url: str) -> Article | None:
        title_el = soup.select_one("h1") or soup.select_one("h2.entry-title") or soup.select_one("h2")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        body_el = soup.select_one(".entry-content") or soup.select_one("article") or soup.select_one(".elementor-widget-text-editor")
        if body_el:
            paragraphs = body_el.select("p")
            body = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            body = ""

        first_para = body.split("\n")[0] if body else ""

        img_el = (
            soup.select_one(".wp-post-image")
            or soup.select_one(".entry-content img")
            or soup.select_one("article img")
            or soup.select_one("img[src*='agoraalagoas']")
        )
        image_url = img_el.get("src") if img_el else None

        return Article(url=url, title=title, body=body, image_url=image_url, first_paragraph=first_para)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "agoraalagoas scraper ready"}).encode())
