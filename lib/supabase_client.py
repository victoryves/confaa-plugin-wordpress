import os
from supabase import create_client, Client

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_KEY"]
        _client = create_client(url, key)
    return _client


def is_url_published(url: str) -> bool:
    client = get_client()
    result = client.table("published_urls").select("id").eq("url", url).limit(1).execute()
    return len(result.data) > 0


def log_published_url(
    url: str,
    title: str,
    source_site: str,
    category: str,
    wp_post_id: int,
) -> None:
    client = get_client()
    client.table("published_urls").insert({
        "url": url,
        "title": title,
        "source_site": source_site,
        "category": category,
        "wp_post_id": wp_post_id,
    }).execute()


def log_scrape_result(
    source_site: str,
    articles_found: int,
    articles_published: int,
    articles_filtered: int,
    error: str | None = None,
) -> None:
    client = get_client()
    client.table("scrape_logs").insert({
        "source_site": source_site,
        "articles_found": articles_found,
        "articles_published": articles_published,
        "articles_filtered": articles_filtered,
        "error": error,
    }).execute()


def get_sources() -> list[dict]:
    client = get_client()
    result = client.table("sources").select("*").eq("active", True).execute()
    return result.data


def get_filter_keywords() -> list[str]:
    """Fetch custom filter keywords from Supabase if stored, else return defaults."""
    from lib.filter import DEFAULT_BLACKLIST
    try:
        client = get_client()
        result = client.table("filter_keywords").select("keyword").execute()
        if result.data:
            return [row["keyword"] for row in result.data]
    except Exception:
        pass
    return DEFAULT_BLACKLIST
