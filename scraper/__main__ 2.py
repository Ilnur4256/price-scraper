"""Запуск: python -m scraper --help"""

import argparse
import logging
import sys
from pathlib import Path

from scraper import exporters
from scraper.crawler import BASE_URL, crawl, list_categories
from scraper.diff import compare
from scraper.http import HttpClient


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scraper", description="Сбор цен с books.toscrape.com в CSV/JSON/Google Sheets"
    )
    p.add_argument("--category", help="Название категории, например Travel (по умолчанию — все)")
    p.add_argument("--list-categories", action="store_true", help="Показать категории и выйти")
    p.add_argument("--max-pages", type=int, help="Ограничить число страниц")
    p.add_argument("--min-rating", type=int, default=0, help="Минимальный рейтинг 1..5")
    p.add_argument("--max-price", type=float, help="Максимальная цена")
    p.add_argument("--in-stock", action="store_true", help="Только в наличии")
    p.add_argument("--csv", type=Path, help="Сохранить в CSV")
    p.add_argument("--json", type=Path, help="Сохранить в JSON (снимок для сравнения)")
    p.add_argument("--compare", type=Path, help="Сравнить с прошлым JSON-снимком")
    p.add_argument("--sheet-id", help="ID Google Таблицы")
    p.add_argument("--sheet-name", default="Books", help="Лист в таблице")
    p.add_argument(
        "--credentials",
        type=Path,
        default=Path("credentials.json"),
        help="JSON-ключ сервисного аккаунта Google",
    )
    p.add_argument("--delay", type=float, default=0.5, help="Пауза между запросами, с")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    client = HttpClient(delay=args.delay)

    if args.list_categories or args.category:
        categories = list_categories(client)
        if args.list_categories:
            print("\n".join(categories))
            return 0
        matches = {k: v for k, v in categories.items() if k.lower() == args.category.lower()}
        if not matches:
            print(f"Категория {args.category!r} не найдена. См. --list-categories", file=sys.stderr)
            return 2
        category, start_url = next(iter(matches.items()))
    else:
        category, start_url = "", BASE_URL + "catalogue/page-1.html"

    books = [
        b
        for b in crawl(client, start_url, category, args.max_pages)
        if b.rating >= args.min_rating
        and (args.max_price is None or b.price <= args.max_price)
        and (b.in_stock or not args.in_stock)
    ]
    logging.info("Собрано товаров: %s", len(books))

    if args.compare and args.compare.exists():
        print(compare(exporters.from_json(args.compare), books).summary())
    if args.csv:
        exporters.to_csv(books, args.csv)
        logging.info("CSV: %s", args.csv)
    if args.json:
        exporters.to_json(books, args.json)
        logging.info("JSON: %s", args.json)
    if args.sheet_id:
        url = exporters.to_google_sheet(books, args.sheet_id, args.credentials, args.sheet_name)
        logging.info("Google Sheets: %s", url)
    if not (args.csv or args.json or args.sheet_id):
        for b in books[:20]:
            print(f"{b.price:>8} {b.currency}  {'★' * b.rating:<5}  {b.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
