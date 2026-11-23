"""テスト共通の補助関数。"""
import csv
from pathlib import Path

import pytest

from shipdoc.models import COLUMNS


def make_row(**overrides: str) -> dict[str, str]:
    """正常な1行分のデータを作る。引数で一部の値を上書きできる。"""
    row = {
        "伝票番号": "D0001",
        "明細ID": "L001",
        "出荷日": "2026-11-20",
        "得意先コード": "C001",
        "得意先名": "サンプル商事株式会社",
        "商品コード": "00123",
        "商品名": "A4コピー用紙",
        "数量": "10",
        "単位": "箱",
        "単価": "1200",
        "備考": "",
    }
    row.update(overrides)
    return row


def write_csv(path: Path, rows: list[dict[str, str]], encoding: str = "utf-8-sig",
              columns: tuple[str, ...] = COLUMNS) -> Path:
    with path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})
    return path


@pytest.fixture
def csv_factory(tmp_path):
    def _make(rows, name="input.csv", **kwargs):
        return write_csv(tmp_path / name, rows, **kwargs)
    return _make
