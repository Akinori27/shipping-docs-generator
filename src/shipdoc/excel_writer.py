"""テンプレートを読み込み、伝票1枚分の値を流し込んで別名で保存する。"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell

from . import template_layout as L
from .models import Slip

_UNSAFE_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
MAX_FILENAME_CHARS = 80  # Macのファイル名上限（255バイト）に余裕を持たせる


def safe_filename(text: str) -> str:
    """ファイル名に使えない文字を「_」に置き換え、長すぎる場合は切り詰める。"""
    name = _UNSAFE_CHARS.sub("_", text).strip().strip(".")[:MAX_FILENAME_CHARS]
    return name or "_"


def number_format_for(value: int | Decimal) -> str:
    """値の小数桁数に合わせた表示形式。PDFと同じ桁数で表示し、丸めない。"""
    places = max(0, -Decimal(value).normalize().as_tuple().exponent)
    return "#,##0" if places == 0 else "#,##0." + "0" * places


def _set_number(cell: Cell, value: int | Decimal) -> None:
    cell.value = value
    cell.number_format = number_format_for(value)


def _set_text(cell: Cell, value: str) -> None:
    """文字列として書き込む。「=」で始まっても数式として扱わせない。"""
    cell.value = value
    cell.data_type = "s"


def write_slip_excel(slip: Slip, template_path: Path, out_path: Path, issue_date: date) -> Path:
    wb = load_workbook(template_path)  # テンプレートは読むだけ。保存は別名
    ws = wb[L.SHEET_NAME]

    ws[L.ISSUE_DATE_CELL] = issue_date
    ws[L.SHIP_DATE_CELL] = slip.ship_date
    _set_text(ws[L.SLIP_NO_CELL], slip.slip_no)
    _set_text(ws[L.CUSTOMER_CODE_CELL], slip.customer_code)
    _set_text(ws[L.CUSTOMER_NAME_CELL], slip.customer_name)

    cols = L.ITEM_COLUMNS
    for offset, item in enumerate(slip.items):
        row = L.ITEM_FIRST_ROW + offset
        ws[f"{cols['no']}{row}"] = offset + 1
        _set_text(ws[f"{cols['product_code']}{row}"], item.product_code)
        _set_text(ws[f"{cols['product_name']}{row}"], item.product_name)
        ws[f"{cols['quantity']}{row}"] = item.quantity
        _set_text(ws[f"{cols['unit']}{row}"], item.unit)
        _set_number(ws[f"{cols['unit_price']}{row}"], item.unit_price)
        _set_number(ws[f"{cols['amount']}{row}"], item.amount)
        _set_text(ws[f"{cols['note']}{row}"], item.note)

    ws[L.TOTAL_QUANTITY_CELL] = slip.total_quantity
    _set_number(ws[L.TOTAL_AMOUNT_CELL], slip.total_amount)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path
