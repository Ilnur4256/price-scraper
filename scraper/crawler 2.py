import logging
from collections.abc import Iterator

from scraper.http import HttpClient
from scraper.models import Book
from scraper.parser import parse_categories, parse_list_page

log = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com/"


def list_categories(client: HttpClient, base_url: str = BASE_URL) -> dict[str, str]:
    return parse_categories(client.get(base_url), base_url)


def crawl(
    client: HttpClient,
    start_url: str,
    category: str = "",
    max_pages: int | None = None,
) -> Iterator[Book]:
    """Идёт по страницам каталога, пока есть «next» (или до max_pages)."""
    url: str | None = start_url
    page = 0
    seen: set[str] = set()
    while url and (max_pages is None or page < max_pages):
        page += 1
        books, url = parse_list_page(client.get(url), url, category)
        log.info("Страница %s: %s товаров", page, len(books))
        for book in books:
            if book.url not in seen:  # защита от дублей между страницами
                seen.add(book.url)
                yield book
