"""テンプレートを読み込み、伝票1枚分の値を流し込んで別名で保存する。"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell

from . import template_layout as L
from .models import Slip

_UNSAFE_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def safe_filename(text: str) -> str:
    """ファイル名に使えない文字を「_」に置き換える。"""
    name = _UNSAFE_CHARS.sub("_", text).strip().strip(".")
    return name or "_"


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
        ws[f"{cols['unit_price']}{row}"] = item.unit_price
        ws[f"{cols['amount']}{row}"] = item.amount
        _set_text(ws[f"{cols['note']}{row}"], item.note)

    ws[L.TOTAL_QUANTITY_CELL] = slip.total_quantity
    ws[L.TOTAL_AMOUNT_CELL] = slip.total_amount

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path
