from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook

from conftest import make_slip
from shipdoc import template_layout as L
from shipdoc.excel_writer import safe_filename, write_slip_excel
from shipdoc.template_builder import build_template

ISSUE_DATE = date(2026, 11, 23)
REPO_TEMPLATE = Path(__file__).parent.parent / "templates" / "納品明細テンプレート.xlsx"


@pytest.fixture
def template(tmp_path):
    return build_template(tmp_path / "template.xlsx")


def written_sheet(tmp_path, template, slip):
    out = write_slip_excel(slip, template, tmp_path / "out.xlsx", ISSUE_DATE)
    return load_workbook(out)[L.SHEET_NAME]


def as_date(value):
    return value.date() if isinstance(value, datetime) else value


def test_header_values(tmp_path, template):
    ws = written_sheet(tmp_path, template, make_slip())
    assert ws[L.SLIP_NO_CELL].value == "D0001"
    assert ws[L.CUSTOMER_NAME_CELL].value == "サンプル商事株式会社"
    assert ws[L.CUSTOMER_CODE_CELL].value == "C001"
    assert as_date(ws[L.SHIP_DATE_CELL].value) == date(2026, 11, 20)
    assert as_date(ws[L.ISSUE_DATE_CELL].value) == ISSUE_DATE


def test_item_rows_and_totals(tmp_path, template):
    ws = written_sheet(tmp_path, template, make_slip(n_items=2))
    row = L.ITEM_FIRST_ROW
    assert ws[f"{L.ITEM_COLUMNS['no']}{row}"].value == 1
    assert ws[f"{L.ITEM_COLUMNS['product_code']}{row}"].value == "00121"
    assert ws[f"{L.ITEM_COLUMNS['quantity']}{row + 1}"].value == 4
    assert ws[f"{L.ITEM_COLUMNS['amount']}{row + 1}"].value == 4800
    assert ws[f"{L.ITEM_COLUMNS['no']}{row + 2}"].value is None
    assert ws[L.TOTAL_QUANTITY_CELL].value == 6
    assert ws[L.TOTAL_AMOUNT_CELL].value == 7200


def test_template_formatting_is_kept(tmp_path, template):
    ws = written_sheet(tmp_path, template, make_slip())
    assert ws[L.TITLE_CELL].value == L.TITLE
    assert ws[L.TITLE_CELL].font.bold


def test_formula_like_text_is_not_formula(tmp_path, template):
    ws = written_sheet(tmp_path, template, make_slip(product_name="=HYPERLINK(\"http://x\")"))
    cell = ws[f"{L.ITEM_COLUMNS['product_name']}{L.ITEM_FIRST_ROW}"]
    assert cell.data_type == "s"
    assert cell.value == "=HYPERLINK(\"http://x\")"


def test_fifteen_items_fit(tmp_path, template):
    ws = written_sheet(tmp_path, template, make_slip(n_items=L.ITEM_ROWS))
    last = L.ITEM_FIRST_ROW + L.ITEM_ROWS - 1
    assert ws[f"{L.ITEM_COLUMNS['no']}{last}"].value == L.ITEM_ROWS


def test_template_file_is_not_modified(tmp_path, template):
    before = template.read_bytes()
    write_slip_excel(make_slip(), template, tmp_path / "out.xlsx", ISSUE_DATE)
    assert template.read_bytes() == before


def test_repo_template_matches_layout():
    ws = load_workbook(REPO_TEMPLATE)[L.SHEET_NAME]
    assert ws[L.TITLE_CELL].value == L.TITLE


@pytest.mark.parametrize("text, expected", [
    ("D0001", "D0001"), ("A/B", "A_B"), ('a:b*c?"<>|\\', "a_b_c______"),
    ("..", "_"), ("", "_"),
])
def test_safe_filename(text, expected):
    assert safe_filename(text) == expected
