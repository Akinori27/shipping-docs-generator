"""伝票1枚分の納品明細PDFを作る。

日本語フォントは reportlab に内蔵の HeiseiKakuGo-W5 を使うため、
フォントファイルの同梱や追加インストールは不要。
レイアウトは Excel テンプレートと同じ項目・並びにそろえている。
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Table, TableStyle

from . import template_layout as L
from .models import Slip

FONT = "HeiseiKakuGo-W5"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))

_HEADER_BG = colors.HexColor("#DCE6F1")
_LINE = colors.HexColor("#808080")
# 明細表の列幅（Excelテンプレートの列幅の比率に合わせる）
_COL_WIDTHS_MM = (10, 22, 56, 15, 11, 20, 24, 22)
_CELL_PADDING = 4  # セル左右の余白（pt）
_BASE_SIZE = 9
_MIN_TEXT_SIZE = 5  # 文字列はここまで縮める
_MIN_NUMBER_SIZE = 6  # 金額などの数字は読みやすさのため 6pt まで
_MIN_CUSTOMER_NAME_SIZE = 8  # 宛名は帳票の顔なので 8pt まで
_NUMBER_COLS = (3, 5, 6)  # 数量・単価・金額
# 見出し部の値の最大幅
_CUSTOMER_NAME_WIDTH = 110 * mm
_CUSTOMER_CODE_WIDTH = 100 * mm
_SLIP_NO_WIDTH = 42 * mm


def _num(value: int | Decimal) -> str:
    """3桁区切り。小数があるときだけ小数部を表示する。"""
    value = Decimal(value)
    if value == value.to_integral_value():
        return f"{int(value):,}"
    return f"{value.normalize():,f}"


def fit_font_size(text: str, width: float, base: float = 9, minimum: float = 5) -> float:
    """text が width（pt）に収まる最大の文字サイズを返す（base〜minimum の範囲）。"""
    size = base
    while size > minimum and pdfmetrics.stringWidth(text, FONT, size) > width:
        size -= 0.5
    return size


def _fits(text: str, width: float, base: float, minimum: float) -> tuple[float, bool]:
    """(使う文字サイズ, 最小サイズで収まるか) を返す。"""
    size = fit_font_size(text, width, base, minimum)
    return size, pdfmetrics.stringWidth(text, FONT, size) <= width


def _item_cells(slip: Slip) -> list[list[str]]:
    return [[str(n), item.product_code, item.product_name, _num(item.quantity), item.unit,
             _num(item.unit_price), _num(item.amount), item.note]
            for n, item in enumerate(slip.items, start=1)]


def _total_cells(slip: Slip) -> list[str]:
    return ["", "", L.TOTAL_LABEL, _num(slip.total_quantity), "", "",
            _num(slip.total_amount), ""]


def _customer_line(slip: Slip) -> str:
    return f"{slip.customer_name}  御中"


def _customer_code_line(slip: Slip) -> str:
    return f"得意先コード  {slip.customer_code}"


def _cell_width(col: int) -> float:
    return _COL_WIDTHS_MM[col] * mm - _CELL_PADDING


def layout_problems(slip: Slip) -> list[str]:
    """最小の文字サイズでも帳票の枠に収まらない項目を「項目名（明細ID）」の形で返す。"""
    problems: list[str] = []
    keys = list(L.ITEM_COLUMNS)
    for item, row in zip(slip.items, _item_cells(slip)):
        for col in range(1, len(keys)):
            minimum = _MIN_NUMBER_SIZE if col in _NUMBER_COLS else _MIN_TEXT_SIZE
            if not _fits(row[col], _cell_width(col), _BASE_SIZE, minimum)[1]:
                problems.append(f"{L.ITEM_HEADERS[keys[col]]}（{item.detail_id}）")
    totals = _total_cells(slip)
    for col, label in ((3, "合計数量"), (6, "合計金額")):
        if not _fits(totals[col], _cell_width(col), 10, _MIN_NUMBER_SIZE)[1]:
            problems.append(label)
    checks = (
        (_customer_line(slip), _CUSTOMER_NAME_WIDTH, 15, _MIN_CUSTOMER_NAME_SIZE, "得意先名"),
        (_customer_code_line(slip), _CUSTOMER_CODE_WIDTH, 10, _MIN_TEXT_SIZE, "得意先コード"),
        (slip.slip_no, _SLIP_NO_WIDTH, 10, _MIN_TEXT_SIZE, "伝票番号"),
    )
    for text, width, base, minimum, label in checks:
        if not _fits(text, width, base, minimum)[1]:
            problems.append(label)
    return problems


def _fmt_date(value: date) -> str:
    return value.strftime("%Y/%m/%d")


def write_slip_pdf(slip: Slip, out_path: Path, issue_date: date) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = A4
    left, right = 15 * mm, width - 15 * mm

    c = Canvas(str(out_path), pagesize=A4)
    c.setTitle(f"納品明細書 {slip.slip_no}")
    c.setAuthor(L.ISSUER_LINES[0])

    # タイトル
    c.setFont(FONT, 20)
    c.drawCentredString(width / 2, height - 25 * mm, L.TITLE)

    # 右上: 発行日・伝票番号
    c.setFont(FONT, 10)
    y = height - 38 * mm
    for label, value in (("発行日", _fmt_date(issue_date)), ("伝票番号", slip.slip_no)):
        c.setFont(FONT, 10)
        c.drawString(right - 60 * mm, y, label)
        c.setFont(FONT, _fits(value, _SLIP_NO_WIDTH, 10, _MIN_TEXT_SIZE)[0])
        c.drawRightString(right, y, value)
        y -= 6 * mm

    # 左: 得意先
    y = height - 44 * mm
    code_line = _customer_code_line(slip)
    c.setFont(FONT, _fits(code_line, _CUSTOMER_CODE_WIDTH, 10, _MIN_TEXT_SIZE)[0])
    c.drawString(left, y, code_line)
    y -= 10 * mm
    name_line = _customer_line(slip)
    c.setFont(FONT, _fits(name_line, _CUSTOMER_NAME_WIDTH, 15, _MIN_CUSTOMER_NAME_SIZE)[0])
    c.drawString(left, y, name_line)
    c.setLineWidth(0.8)
    c.line(left, y - 2 * mm, left + _CUSTOMER_NAME_WIDTH, y - 2 * mm)
    y -= 10 * mm
    c.setFont(FONT, 10)
    c.drawString(left, y, f"出荷日  {_fmt_date(slip.ship_date)}")
    y -= 7 * mm
    c.drawString(left, y, L.GREETING)

    # 右: 発行元（架空）
    c.setFont(FONT, 9)
    iy = height - 58 * mm
    for line in L.ISSUER_LINES:
        c.drawString(right - 60 * mm, iy, line)
        iy -= 5 * mm

    # 明細表（空行も含めて常に15行分の枠を描く）
    keys = list(L.ITEM_COLUMNS)
    data = [[L.ITEM_HEADERS[k] for k in keys]]
    data += _item_cells(slip)
    data += [[""] * len(keys) for _ in range(L.ITEM_ROWS - len(slip.items))]
    data.append(_total_cells(slip))

    col_widths = [w * mm for w in _COL_WIDTHS_MM]
    # 長い値は枠からはみ出さないよう、そのセルだけ文字を小さくする
    # （最小サイズでも収まらない伝票は layout_problems で事前に保留される）
    shrink = []
    rows_to_fit = [(r, _BASE_SIZE) for r in range(1, len(slip.items) + 1)] + [(len(data) - 1, 10)]
    for row_idx, base in rows_to_fit:
        for col_idx in range(1, len(keys)):
            minimum = _MIN_NUMBER_SIZE if col_idx in _NUMBER_COLS else _MIN_TEXT_SIZE
            size = _fits(data[row_idx][col_idx], _cell_width(col_idx), base, minimum)[0]
            if size < base:
                shrink.append(("FONTSIZE", (col_idx, row_idx), (col_idx, row_idx), size))

    table = Table(data, colWidths=col_widths, rowHeights=7.5 * mm)
    table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), FONT, 9),
        ("GRID", (0, 0), (-1, -1), 0.5, _LINE),
        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (3, 1), (3, -1), "RIGHT"),
        ("ALIGN", (5, 1), (6, -1), "RIGHT"),
        ("ALIGN", (2, -1), (2, -1), "RIGHT"),
        ("FONT", (0, -1), (-1, -1), FONT, 10),
        ("LINEABOVE", (0, -1), (-1, -1), 1.2, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ] + shrink))  # 後に書いた指定が優先されるため、縮小指定は最後に置く
    _, table_height = table.wrapOn(c, right - left, height)
    table.drawOn(c, left, y - 8 * mm - table_height)

    c.setFont(FONT, 8)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawString(left, 15 * mm, L.NOTE)

    c.showPage()
    c.save()
    return out_path
