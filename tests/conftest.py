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


def make_slip(slip_no: str = "D0001", n_items: int = 2, **item_overrides):
    """出力テスト用の検証済み伝票を作る。"""
    from datetime import date
    from decimal import Decimal

    from shipdoc.models import LineItem, Slip

    items = []
    for n in range(1, n_items + 1):
        fields = dict(detail_id=f"L{n:03d}", product_code=f"0012{n}",
                      product_name=f"商品{n}", quantity=n * 2, unit="箱",
                      unit_price=Decimal("1200"), note="")
        fields.update(item_overrides)
        items.append(LineItem(**fields))
    return Slip(slip_no=slip_no, ship_date=date(2026, 11, 20), customer_code="C001",
                customer_name="サンプル商事株式会社", items=tuple(items))
