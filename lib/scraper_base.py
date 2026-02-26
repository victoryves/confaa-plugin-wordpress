import time
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

from lib.classifier import classify_article
from lib.filter import is_violent_content
from lib.supabase_client import is_url_published, log_published_url, log_scrape_result
from lib.wordpress import upload_image, create_post

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_page(url: str, timeout: int = 15) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return BeautifulSoup(resp.text, "lxml")
    except Exception as exc:
        print(f"[fetch] Error fetching {url}: {exc}")
        return None


@dataclass
class Article:
    url: str
    title: str
    body: str
    image_url: str | None
    first_paragraph: str = ""


@dataclass
class ScrapeResult:
    source_site: str
    articles_found: int = 0
    articles_published: int = 0
    articles_filtered: int = 0
    error: str | None = None
    published: list[dict] = field(default_factory=list)


class BaseScraper:
    site_name: str = ""
    listing_url: str = ""
    request_delay: float = 1.5

    def get_article_links(self, soup: BeautifulSoup) -> list[str]:
        raise NotImplementedError

    def parse_article(self, soup: BeautifulSoup, url: str) -> Article | None:
        raise NotImplementedError

    def run(self, credentials: dict, blacklist: list[str] | None = None) -> ScrapeResult:
        result = ScrapeResult(source_site=self.site_name)
        try:
            soup = fetch_page(self.listing_url)
            if soup is None:
                result.error = "Failed to fetch listing page"
                log_scrape_result(self.site_name, 0, 0, 0, result.error)
                return result

            links = self.get_article_links(soup)
            result.articles_found = len(links)

            for link in links:
                try:
                    self._process_article(link, result, credentials, blacklist)
                except Exception as exc:
                    result.articles_filtered += 1
                    print(f"[{self.site_name}] Error processing {link}: {exc}")
                time.sleep(self.request_delay)

        except Exception as exc:
            result.error = str(exc)
            print(f"[{self.site_name}] Fatal error: {exc}")

        log_scrape_result(
            source_site=self.site_name,
            articles_found=result.articles_found,
            articles_published=result.articles_published,
            articles_filtered=result.articles_filtered,
            error=result.error,
        )
        return result

    def _process_article(self, url: str, result: ScrapeResult, credentials: dict, blacklist: list[str] | None) -> None:
        if is_url_published(url):
            result.articles_filtered += 1
            return

        time.sleep(self.request_delay)
        soup = fetch_page(url)
        if soup is None:
            result.articles_filtered += 1
            return

        article = self.parse_article(soup, url)
        if article is None:
            result.articles_filtered += 1
            return

        if is_violent_content(article.title, article.body, blacklist):
            result.articles_filtered += 1
            return

        category = classify_article(article.title, article.first_paragraph or article.body[:300])

        media_id = None
        if article.image_url:
            filename = article.image_url.split("/")[-1].split("?")[0] or "image.jpg"
            media_id = upload_image(article.image_url, filename, credentials)

        wp_id = create_post(
            title=article.title,
            content=article.body,
            category_name=category,
            featured_media_id=media_id,
            credentials=credentials,
            source_url=url,
        )

        log_published_url(
            url=url,
            title=article.title,
            source_site=self.site_name,
            category=category,
            wp_post_id=wp_id,
        )

        result.articles_published += 1
        result.published.append({"url": url, "title": article.title, "category": category})
