import csv

from scraper import exporters
from scraper.diff import compare
from scraper.models import Book


def book(n: int, price: float) -> Book:
    return Book(f"Book {n}", price, "£", 3, True, f"https://x/{n}")


def test_compare():
    old = [book(1, 10), book(2, 20), book(3, 30)]
    new = [book(1, 10), book(2, 15), book(4, 40)]
    report = compare(old, new)
    assert [b.title for b in report.added] == ["Book 4"]
    assert [b.title for b in report.removed] == ["Book 3"]
    assert len(report.price_changes) == 1
    assert report.price_changes[0].delta_percent == -25.0
    assert "Book 2: 20 → 15 (-25.0%)" in report.summary()


def test_compare_no_changes():
    assert compare([book(1, 10)], [book(1, 10)]).is_empty


def test_csv_and_json_roundtrip(tmp_path):
    books = [book(1, 10.5), Book("Кириллица", 1.0, "£", 5, False, "https://x/ru", "Poetry")]
    exporters.to_csv(books, tmp_path / "b.csv")
    with (tmp_path / "b.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    assert rows[0] == Book.columns()
    assert rows[2][0] == "Кириллица"

    exporters.to_json(books, tmp_path / "b.json")
    assert exporters.from_json(tmp_path / "b.json") == books


class FakeWorksheet:
    def __init__(self):
        self.calls = []

    def clear(self):
        self.calls.append(("clear",))

    def update(self, rows, start):
        self.calls.append(("update", rows, start))

    def freeze(self, rows):
        self.calls.append(("freeze", rows))


def test_to_worksheet_writes_one_batch():
    ws = FakeWorksheet()
    exporters.to_worksheet([book(1, 10)], ws)
    assert ws.calls[0] == ("clear",)
    _, rows, start = ws.calls[1]
    assert start == "A1"
    assert rows == [Book.columns(), ["Book 1", 10, "£", 3, True, "https://x/1", ""]]
    assert ws.calls[2] == ("freeze", 1)
    assert len(ws.calls) == 3
