"""Сравнение с прошлым запуском: что появилось, пропало и где изменилась цена."""

from dataclasses import dataclass, field

from scraper.models import Book


@dataclass
class PriceChange:
    book: Book
    old_price: float

    @property
    def delta_percent(self) -> float:
        return round((self.book.price - self.old_price) / self.old_price * 100, 1)


@dataclass
class Report:
    added: list[Book] = field(default_factory=list)
    removed: list[Book] = field(default_factory=list)
    price_changes: list[PriceChange] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.price_changes)

    def summary(self) -> str:
        lines = [
            f"Новых: {len(self.added)}, пропало: {len(self.removed)}, "
            f"изменилась цена: {len(self.price_changes)}"
        ]
        for ch in sorted(self.price_changes, key=lambda c: c.delta_percent):
            lines.append(
                f"  {ch.book.title}: {ch.old_price} → {ch.book.price} ({ch.delta_percent:+}%)"
            )
        return "\n".join(lines)


def compare(old: list[Book], new: list[Book]) -> Report:
    old_by_url = {b.url: b for b in old}
    new_by_url = {b.url: b for b in new}
    report = Report()
    for url, book in new_by_url.items():
        prev = old_by_url.get(url)
        if prev is None:
            report.added.append(book)
        elif prev.price != book.price:
            report.price_changes.append(PriceChange(book=book, old_price=prev.price))
    report.removed = [b for url, b in old_by_url.items() if url not in new_by_url]
    return report
