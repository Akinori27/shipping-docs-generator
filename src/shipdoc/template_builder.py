"""デモ用の「既存テンプレート」を作る。

実案件では顧客が普段使っている Excel 書式をそのまま templates/ に置き、
template_layout のセル番地を合わせる。このモジュールはデモ用の書式を
再現可能な形で作るためだけにある（scripts/make_template.py から呼ぶ）。
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from . import template_layout as L

_THIN = Side(style="thin", color="808080")
_BOX = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_HEADER_FILL = PatternFill("solid", fgColor="DCE6F1")
_FONT = "游ゴシック"


def build_template(path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = L.SHEET_NAME

    for col, width in L.COLUMN_WIDTHS.items():
        ws.column_dimensions[col].width = width

    ws.merge_cells(f"{L.TITLE_CELL}:{L.LAST_COLUMN}1")
    ws[L.TITLE_CELL] = L.TITLE
    ws[L.TITLE_CELL].font = Font(name=_FONT, size=18, bold=True)
    ws[L.TITLE_CELL].alignment = Alignment(horizontal="center")
    ws.row_dimensions[1].height = 32

    labels = {
        L.ISSUE_DATE_LABEL_CELL: "発行日",
        L.SLIP_NO_LABEL_CELL: "伝票番号",
        L.CUSTOMER_CODE_LABEL_CELL: "得意先コード",
        L.SHIP_DATE_LABEL_CELL: "出荷日",
        L.HONORIFIC_CELL: "御中",
    }
    ws.merge_cells(f"{L.CUSTOMER_CODE_LABEL_CELL}:B3")
    ws.merge_cells(f"{L.SHIP_DATE_LABEL_CELL}:B6")
    for cell, text in labels.items():
        ws[cell] = text
        ws[cell].font = Font(name=_FONT, size=10)
    ws[L.ISSUE_DATE_CELL].number_format = "yyyy/mm/dd"
    ws[L.SHIP_DATE_CELL].number_format = "yyyy/mm/dd"
    ws[L.SHIP_DATE_CELL].alignment = Alignment(horizontal="left")
    ws[L.ISSUE_DATE_CELL].alignment = Alignment(horizontal="left")
    ws[L.SLIP_NO_CELL].alignment = Alignment(horizontal="left")

    ws.merge_cells(L.CUSTOMER_NAME_RANGE)
    ws[L.CUSTOMER_NAME_CELL].alignment = Alignment(shrink_to_fit=True, vertical="center")
    ws[L.CUSTOMER_NAME_CELL].font = Font(name=_FONT, size=14, bold=True, underline="single")
    ws[L.HONORIFIC_CELL].font = Font(name=_FONT, size=12)
    ws.row_dimensions[4].height = 24

    for cell, text in zip(L.ISSUER_CELLS, L.ISSUER_LINES):
        ws[cell] = text
        ws[cell].font = Font(name=_FONT, size=9)
    ws[L.GREETING_CELL] = L.GREETING

    for key, col in L.ITEM_COLUMNS.items():
        cell = ws[f"{col}{L.HEADER_ROW}"]
        cell.value = L.ITEM_HEADERS[key]
        cell.font = Font(name=_FONT, size=10, bold=True)
        cell.fill = _HEADER_FILL
        cell.border = _BOX
        cell.alignment = Alignment(horizontal="center")

    formats = {"quantity": "#,##0", "unit_price": "#,##0", "amount": "#,##0"}
    for row in range(L.ITEM_FIRST_ROW, L.TOTAL_ROW + 1):
        for key, col in L.ITEM_COLUMNS.items():
            cell = ws[f"{col}{row}"]
            cell.border = _BOX
            cell.font = Font(name=_FONT, size=10)
            if key in formats:
                cell.number_format = formats[key]
            if key == "no":
                cell.alignment = Alignment(horizontal="center")
            else:
                # 長い値は枠からはみ出さず、文字を縮めて表示する
                cell.alignment = Alignment(shrink_to_fit=True, vertical="center")

    ws[L.TOTAL_LABEL_CELL] = L.TOTAL_LABEL
    for cell in (L.TOTAL_LABEL_CELL, L.TOTAL_QUANTITY_CELL, L.TOTAL_AMOUNT_CELL):
        ws[cell].font = Font(name=_FONT, size=10, bold=True)
    ws[L.TOTAL_LABEL_CELL].alignment = Alignment(horizontal="right")
    ws[L.NOTE_CELL] = L.NOTE
    ws[L.NOTE_CELL].font = Font(name=_FONT, size=8, color="666666")

    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:{L.LAST_COLUMN}{L.TOTAL_ROW + 2}"

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
