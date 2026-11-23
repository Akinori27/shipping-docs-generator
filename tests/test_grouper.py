from datetime import date
from decimal import Decimal

from conftest import make_row
from shipdoc.grouper import group_slips
from shipdoc.models import ShipmentRow
from shipdoc.validator import find_row_issues


def run(*dicts, max_items=15):
    rows = [ShipmentRow(line_no=i + 2, data=d) for i, d in enumerate(dicts)]
    return group_slips(rows, find_row_issues(rows), max_items=max_items)


def test_groups_rows_by_slip_in_order():
    result = run(
        make_row(伝票番号="D2", 明細ID="L1"),
        make_row(伝票番号="D1", 明細ID="L2"),
        make_row(伝票番号="D2", 明細ID="L3"),
    )
    assert [s.slip_no for s in result.slips] == ["D2", "D1"]
    assert [i.detail_id for i in result.slips[0].items] == ["L1", "L3"]
    assert result.issues == []


def test_slip_values_are_parsed():
    result = run(make_row(明細ID="L1", 数量="3", 単価="1200", 出荷日="2026/11/20"),
                 make_row(明細ID="L2", 数量="2", 単価="99.5"))
    slip = result.slips[0]
    assert slip.ship_date == date(2026, 11, 20)
    assert slip.total_quantity == 5
    assert slip.total_amount == Decimal("3799.0")


def test_one_bad_row_holds_whole_slip():
    result = run(
        make_row(伝票番号="D1", 明細ID="L1"),
        make_row(伝票番号="D1", 明細ID="L2", 数量="0"),
        make_row(伝票番号="D2", 明細ID="L3"),
    )
    assert [s.slip_no for s in result.slips] == ["D2"]
    assert [(i.line_no, i.category) for i in result.issues] == [
        (2, "同一伝票内に要確認行あり"), (3, "数量不正")]


def test_header_mismatch_holds_slip():
    result = run(
        make_row(伝票番号="D1", 明細ID="L1", 得意先名="サンプル商事株式会社"),
        make_row(伝票番号="D1", 明細ID="L2", 得意先名="テスト工業株式会社"),
    )
    assert result.slips == []
    assert [i.category for i in result.issues] == ["ヘッダ不一致", "ヘッダ不一致"]
    assert "得意先名" in result.issues[0].message


def test_too_many_items_holds_slip():
    rows = [make_row(明細ID=f"L{n}") for n in range(3)]
    result = run(*rows, max_items=2)
    assert result.slips == []
    assert {i.category for i in result.issues} == {"明細行数超過"}
    assert len(result.issues) == 3


def test_row_without_slip_no_is_reported_once():
    result = run(make_row(伝票番号="", 明細ID="L1"), make_row(伝票番号="D9", 明細ID="L2"))
    assert [s.slip_no for s in result.slips] == ["D9"]
    assert [i.category for i in result.issues] == ["必須項目欠損"]


def test_same_date_in_different_notation_is_not_mismatch():
    result = run(make_row(明細ID="L1", 出荷日="2026/11/20"),
                 make_row(明細ID="L2", 出荷日="2026-11-20"))
    assert result.issues == []
    assert len(result.slips) == 1
