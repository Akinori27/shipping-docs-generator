from datetime import date
from decimal import Decimal

import pytest

from conftest import make_row
from shipdoc.models import ShipmentRow
from shipdoc.validator import find_row_issues, parse_date, parse_price, parse_quantity


def rows_of(*dicts):
    return [ShipmentRow(line_no=i + 2, data=d) for i, d in enumerate(dicts)]


@pytest.mark.parametrize("text, expected", [
    ("10", 10), (" 3 ", 3), ("1", 1),
    ("0", None), ("-1", None), ("1.5", None), ("abc", None), ("", None), ("１０", None),
])
def test_parse_quantity(text, expected):
    assert parse_quantity(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("1200", Decimal("1200")), ("0", Decimal("0")), ("99.5", Decimal("99.5")),
    ("-1", None), ("abc", None), ("", None), ("NaN", None), ("Infinity", None),
])
def test_parse_price(text, expected):
    assert parse_price(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("2026-11-20", date(2026, 11, 20)), ("2026/11/20", date(2026, 11, 20)),
    ("2026-02-30", None), ("20261120", None), ("", None),
])
def test_parse_date(text, expected):
    assert parse_date(text) == expected


def test_valid_rows_have_no_issues():
    assert find_row_issues(rows_of(make_row(明細ID="L1"), make_row(明細ID="L2"))) == []


def test_missing_required_field():
    issues = find_row_issues(rows_of(make_row(商品名="")))
    assert [(i.line_no, i.category) for i in issues] == [(2, "必須項目欠損")]
    assert "商品名" in issues[0].message


def test_whitespace_only_is_missing():
    issues = find_row_issues(rows_of(make_row(得意先名="　 ")))
    assert [i.category for i in issues] == ["必須項目欠損"]


def test_optional_fields_may_be_empty():
    assert find_row_issues(rows_of(make_row(得意先コード="", 単位="", 備考=""))) == []


def test_invalid_quantity():
    issues = find_row_issues(rows_of(make_row(数量="-3")))
    assert [i.category for i in issues] == ["数量不正"]
    assert "-3" in issues[0].message


def test_empty_quantity_is_reported_once_as_missing():
    issues = find_row_issues(rows_of(make_row(数量="")))
    assert [i.category for i in issues] == ["必須項目欠損"]


def test_invalid_price_and_date():
    issues = find_row_issues(rows_of(make_row(単価="千円", 出荷日="2026/13/01")))
    assert sorted(i.category for i in issues) == ["単価不正", "日付不正"]


def test_duplicate_id_flags_every_occurrence():
    issues = find_row_issues(rows_of(
        make_row(明細ID="L1"), make_row(明細ID="L2"), make_row(明細ID="L1")))
    assert [(i.line_no, i.category) for i in issues] == [(2, "明細ID重複"), (4, "明細ID重複")]
    assert "4" in issues[0].message and "2" in issues[1].message


def test_issue_keeps_raw_row_unmodified():
    row = make_row(数量=" -3 ")
    issues = find_row_issues(rows_of(row))
    assert issues[0].raw == row
    assert issues[0].raw is not row


def test_extra_fields_is_column_count_issue():
    row = ShipmentRow(line_no=2, data=make_row(単価="1", 備考="200"), field_count=12, extra=("",))
    issues = find_row_issues([row])
    assert [i.category for i in issues] == ["列数不一致"]
    assert "12" in issues[0].message and "11" in issues[0].message


def test_missing_fields_is_column_count_issue():
    row = ShipmentRow(line_no=2, data=make_row(), field_count=3)
    assert "列数不一致" in [i.category for i in find_row_issues([row])]


def test_control_character_is_reported():
    issues = find_row_issues(rows_of(make_row(商品名="用紙\x1a")))
    assert [i.category for i in issues] == ["使用できない文字"]
    assert "商品名" in issues[0].message
