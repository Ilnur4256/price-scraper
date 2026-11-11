import csv
import json
from dataclasses import asdict
from pathlib import Path

from scraper.models import Book


def to_csv(books: list[Book], path: Path) -> None:
    # utf-8-sig — чтобы Excel сразу корректно открывал кириллицу
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(Book.columns())
        writer.writerows(b.as_row() for b in books)


def to_json(books: list[Book], path: Path) -> None:
    path.write_text(
        json.dumps([asdict(b) for b in books], ensure_ascii=False, indent=2), encoding="utf-8"
    )


def from_json(path: Path) -> list[Book]:
    return [Book(**item) for item in json.loads(path.read_text(encoding="utf-8"))]


def to_worksheet(books: list[Book], worksheet) -> None:
    """Перезаписывает лист Google Таблицы одним запросом (batch), а не построчно."""
    rows = [Book.columns()] + [b.as_row() for b in books]
    worksheet.clear()
    worksheet.update(rows, "A1")
    worksheet.freeze(rows=1)


def to_google_sheet(
    books: list[Book], spreadsheet_id: str, credentials_file: Path, sheet_name: str
) -> str:
    import gspread  # импорт здесь: для CSV/JSON библиотека не нужна

    client = gspread.service_account(filename=str(credentials_file))
    spreadsheet = client.open_by_key(spreadsheet_id)
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(sheet_name, rows=len(books) + 10, cols=10)
    to_worksheet(books, worksheet)
    return spreadsheet.url
