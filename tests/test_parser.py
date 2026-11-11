from pathlib import Path

import pytest

from scraper.crawler import crawl
from scraper.parser import ParseError, parse_categories, parse_list_page, parse_price

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://books.toscrape.com/catalogue/"


def read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "text, expected",
    [("£51.77", (51.77, "£")), ("Â£10.00", (10.0, "£")), ("$ 7,5", (7.5, "$"))],
)
def test_parse_price(text, expected):
    assert parse_price(text) == expected


def test_parse_price_error():
    with pytest.raises(ParseError):
        parse_price("бесплатно")


def test_parse_list_page():
    books, next_url = parse_list_page(read("page1.html"), BASE + "page-1.html", "Travel")
    assert next_url == BASE + "page-2.html"
    assert len(books) == 2  # битая карточка пропущена
    first, second = books
    assert first.title == "Book One"
    assert (first.price, first.currency, first.rating, first.in_stock) == (51.77, "£", 3, True)
    assert first.url == BASE + "book-one_1/index.html"
    assert first.category == "Travel"
    assert (second.rating, second.in_stock) == (5, False)


def test_last_page_has_no_next():
    _, next_url = parse_list_page(read("page2.html"), BASE + "page-2.html")
    assert next_url is None


def test_parse_categories():
    cats = parse_categories(read("page1.html"), "https://books.toscrape.com/")
    assert cats == {
        "Travel": "https://books.toscrape.com/catalogue/category/books/travel_2/index.html",
        "Poetry": "https://books.toscrape.com/catalogue/category/books/poetry_23/index.html",
    }


class FakeClient:
    def __init__(self, pages: dict[str, str]):
        self.pages = pages
        self.requested: list[str] = []

    def get(self, url: str) -> str:
        self.requested.append(url)
        return self.pages[url]


def test_crawl_follows_pages_and_dedupes():
    client = FakeClient(
        {BASE + "page-1.html": read("page1.html"), BASE + "page-2.html": read("page2.html")}
    )
    books = list(crawl(client, BASE + "page-1.html"))
    assert [b.title for b in books] == ["Book One", "Book Two", "Book Three"]
    assert client.requested == [BASE + "page-1.html", BASE + "page-2.html"]


def test_crawl_respects_max_pages():
    client = FakeClient({BASE + "page-1.html": read("page1.html")})
    assert len(list(crawl(client, BASE + "page-1.html", max_pages=1))) == 2
