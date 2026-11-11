from dataclasses import asdict, dataclass, fields


@dataclass(frozen=True)
class Book:
    title: str
    price: float
    currency: str
    rating: int  # 1..5
    in_stock: bool
    url: str
    category: str = ""

    @classmethod
    def columns(cls) -> list[str]:
        return [f.name for f in fields(cls)]

    def as_row(self) -> list:
        return [asdict(self)[c] for c in self.columns()]
