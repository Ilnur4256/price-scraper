"""Разбор HTML-страниц каталога books.toscrape.com (учебный сайт для парсинга)."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.models import Book

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
PRICE_RE = re.compile(r"(?P<cur>[^\d\s.,]+)\s*(?P<num>\d+(?:[.,]\d+)?)")


class ParseError(Exception):
    pass


def parse_price(text: str) -> tuple[float, str]:
    match = PRICE_RE.search(text.replace("Â", ""))  # сайт иногда отдаёт «Â£» из-за кодировки
    if not match:
        raise ParseError(f"Не удалось разобрать цену: {text!r}")
    return float(match["num"].replace(",", ".")), match["cur"]


def parse_rating(classes: list[str]) -> int:
    for cls in classes:
        if cls in RATINGS:
            return RATINGS[cls]
    return 0


def parse_list_page(html: str, page_url: str, category: str = "") -> tuple[list[Book], str | None]:
    """Возвращает книги со страницы и ссылку на следующую страницу (или None)."""
    soup = BeautifulSoup(html, "html.parser")
    books: list[Book] = []
    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        price_tag = card.select_one(".price_color")
        if link is None or price_tag is None:
            continue  # пропускаем «битую» карточку, а не падаем на всём каталоге
        price, currency = parse_price(price_tag.get_text())
        rating_tag = card.select_one("p.star-rating")
        stock_tag = card.select_one(".availability")
        books.append(
            Book(
                title=link.get("title") or link.get_text(strip=True),
                price=price,
                currency=currency,
                rating=parse_rating(rating_tag.get("class", []) if rating_tag else []),
                in_stock=bool(stock_tag and "in stock" in stock_tag.get_text().lower()),
                url=urljoin(page_url, link["href"]),
                category=category,
            )
        )
    next_link = soup.select_one("li.next a")
    next_url = urljoin(page_url, next_link["href"]) if next_link else None
    return books, next_url


def parse_categories(html: str, page_url: str) -> dict[str, str]:
    """Категории из бокового меню: {«Travel»: url}."""
    soup = BeautifulSoup(html, "html.parser")
    return {
        a.get_text(strip=True): urljoin(page_url, a["href"])
        for a in soup.select(".side_categories ul li ul li a")
    }
