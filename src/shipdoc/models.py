"""ツール全体で使うデータの形を定義する。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

# 入力CSVの列（この1形式のみ受け付ける）
COLUMNS: tuple[str, ...] = (
    "伝票番号",
    "明細ID",
    "出荷日",
    "得意先コード",
    "得意先名",
    "商品コード",
    "商品名",
    "数量",
    "単位",
    "単価",
    "備考",
)

# 空欄を許さない列
REQUIRED_COLUMNS: tuple[str, ...] = (
    "伝票番号",
    "明細ID",
    "出荷日",
    "得意先名",
    "商品コード",
    "商品名",
    "数量",
    "単価",
)

# 同じ伝票の中で値がそろっていなければならない列
HEADER_COLUMNS: tuple[str, ...] = ("出荷日", "得意先コード", "得意先名")


@dataclass(frozen=True)
class ShipmentRow:
    """CSVの1行。値はすべて読み込んだままの文字列で持つ。"""

    line_no: int  # CSV上の物理行番号（ヘッダ=1）
    data: dict[str, str]
    field_count: int = len(COLUMNS)  # この行に実際にあった値の数
    extra: tuple[str, ...] = ()  # 列数より多かった分の値（そのまま保持）


@dataclass(frozen=True)
class Issue:
    """要確認一覧の1行。"""

    line_no: int
    detail_id: str
    slip_no: str
    category: str
    message: str
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LineItem:
    """納品明細の明細1行（検証済み）。"""

    detail_id: str
    product_code: str
    product_name: str
    quantity: int
    unit: str
    unit_price: Decimal
    note: str

    @property
    def amount(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Slip:
    """伝票1枚分（検証済み）。"""

    slip_no: str
    ship_date: date
    customer_code: str
    customer_name: str
    items: tuple[LineItem, ...]

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def total_amount(self) -> Decimal:
        return sum((item.amount for item in self.items), Decimal("0"))
