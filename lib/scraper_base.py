import time
from dataclasses import dataclass, field
from scrapling import Fetcher

from lib.classifier import classify_article
from lib.filter import is_violent_content
from lib.supabase_client import is_url_published, log_published_url, log_scrape_result
from lib.wordpress import upload_image, create_post


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

    def __init__(self):
        self.fetcher = Fetcher()

    def get_article_links(self, page) -> list[str]:
        raise NotImplementedError

    def parse_article(self, page, url: str) -> Article | None:
        raise NotImplementedError

    def run(self, credentials: dict, blacklist: list[str] | None = None) -> ScrapeResult:
        result = ScrapeResult(source_site=self.site_name)
        try:
            page = self.fetcher.get(self.listing_url)
            links = self.get_article_links(page)
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
        page = self.fetcher.get(url)
        article = self.parse_article(page, url)
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
