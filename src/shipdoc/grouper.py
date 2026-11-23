"""行を伝票番号ごとにまとめ、伝票単位で「出力する／保留する」を決める。

1行でも問題がある伝票は伝票ごと保留する。明細が欠けた納品明細が
顧客に届く事故を防ぐため。
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import HEADER_COLUMNS, Issue, LineItem, ShipmentRow, Slip
from .validator import make_issue, parse_date, parse_price, parse_quantity

MAX_ITEMS_PER_SLIP = 15  # テンプレートの明細欄の行数

CAT_HEADER_MISMATCH = "ヘッダ不一致"
CAT_TOO_MANY_ITEMS = "明細行数超過"
CAT_HELD = "同一伝票内に要確認行あり"


@dataclass(frozen=True)
class GroupResult:
    slips: list[Slip]  # 出力してよい伝票（CSVでの出現順）
    issues: list[Issue]  # 要確認一覧に載せる行（行番号順）


def _header_value(row: ShipmentRow, column: str) -> object:
    value = row.data.get(column, "").strip()
    if column == "出荷日":
        # 2026/11/20 と 2026-11-20 は同じ日付として扱う
        return parse_date(value) or value
    return value


def _slip_level_issues(rows: list[ShipmentRow], max_items: int) -> list[Issue]:
    issues: list[Issue] = []
    mismatched = [
        c for c in HEADER_COLUMNS
        if len({_header_value(r, c) for r in rows}) > 1
    ]
    if mismatched:
        message = f"同じ伝票内で {', '.join(mismatched)} が一致していません"
        issues += [make_issue(r, CAT_HEADER_MISMATCH, message) for r in rows]
    if len(rows) > max_items:
        message = f"明細が{len(rows)}行あり、帳票の上限（{max_items}行）を超えています"
        issues += [make_issue(r, CAT_TOO_MANY_ITEMS, message) for r in rows]
    return issues


def _build_slip(slip_no: str, rows: list[ShipmentRow]) -> Slip:
    first = rows[0].data
    items = tuple(
        LineItem(
            detail_id=r.data["明細ID"].strip(),
            product_code=r.data["商品コード"].strip(),
            product_name=r.data["商品名"].strip(),
            quantity=parse_quantity(r.data["数量"]),
            unit=r.data["単位"].strip(),
            unit_price=parse_price(r.data["単価"]),
            note=r.data["備考"].strip(),
        )
        for r in rows
    )
    return Slip(
        slip_no=slip_no,
        ship_date=parse_date(first["出荷日"]),
        customer_code=first["得意先コード"].strip(),
        customer_name=first["得意先名"].strip(),
        items=items,
    )


def group_slips(rows: list[ShipmentRow], row_issues: list[Issue],
                max_items: int = MAX_ITEMS_PER_SLIP) -> GroupResult:
    """行を伝票にまとめる。row_issues は validator.find_row_issues の結果。"""
    issues = list(row_issues)
    lines_with_issue = {i.line_no for i in row_issues}

    groups: dict[str, list[ShipmentRow]] = {}
    for row in rows:
        slip_no = row.data.get("伝票番号", "").strip()
        if slip_no:  # 伝票番号が空の行は欠損として報告済み
            groups.setdefault(slip_no, []).append(row)

    slips: list[Slip] = []
    for slip_no, slip_rows in groups.items():
        slip_issues = _slip_level_issues(slip_rows, max_items)
        issues += slip_issues
        flagged = lines_with_issue | {i.line_no for i in slip_issues}
        if any(r.line_no in flagged for r in slip_rows):
            issues += [
                make_issue(r, CAT_HELD, "同じ伝票に要確認の行があるため、伝票ごと出力を保留しました")
                for r in slip_rows if r.line_no not in flagged
            ]
        else:
            slips.append(_build_slip(slip_no, slip_rows))

    return GroupResult(slips=slips, issues=sorted(issues, key=lambda i: i.line_no))
