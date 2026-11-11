from pathlib import Path

import scraper.__main__ as cli
from scraper import exporters

FIXTURES = Path(__file__).parent / "fixtures"


class FakeHttp:
    def __init__(self, *args, **kwargs):
        pass

    def get(self, url: str) -> str:
        name = "page2.html" if url.endswith("page-2.html") else "page1.html"
        return (FIXTURES / name).read_text(encoding="utf-8")


def test_cli_filters_and_compare(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "HttpClient", FakeHttp)
    snapshot = tmp_path / "snap.json"
    assert cli.main(["--json", str(snapshot), "--delay", "0"]) == 0
    assert len(exporters.from_json(snapshot)) == 3

    out = tmp_path / "f.csv"
    assert (
        cli.main(["--min-rating", "4", "--in-stock", "--csv", str(out), "--compare", str(snapshot)])
        == 0
    )
    lines = out.read_text(encoding="utf-8-sig").splitlines()
    assert len(lines) == 2 and lines[1].startswith("Book Three")
    assert "Новых: 0, пропало: 2" in capsys.readouterr().out


def test_cli_unknown_category(monkeypatch):
    monkeypatch.setattr(cli, "HttpClient", FakeHttp)
    assert cli.main(["--category", "Nope"]) == 2
