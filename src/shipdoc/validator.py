"""行単位のチェック。問題を見つけても値は直さず、要確認として報告するだけ。"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

from .models import COLUMNS, REQUIRED_COLUMNS, Issue, ShipmentRow

# 半角数字のみ許可（全角数字は Python の int() では通ってしまうため正規表現で弾く）
_QUANTITY_RE = re.compile(r"[0-9]+")
_PRICE_RE = re.compile(r"[0-9]+(\.[0-9]+)?")
_DATE_RE = re.compile(r"([0-9]{4})([-/])([0-9]{1,2})\2([0-9]{1,2})")

CAT_MISSING = "必須項目欠損"
CAT_QUANTITY = "数量不正"
CAT_PRICE = "単価不正"
CAT_DATE = "日付不正"
CAT_DUPLICATE = "明細ID重複"
CAT_COLUMN_COUNT = "列数不一致"
CAT_CONTROL_CHAR = "使用できない文字"

# Excelに書き込めない制御文字（タブ・改行は除く）
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def parse_quantity(text: str) -> int | None:
    """1以上の整数なら int を返す。それ以外は None。"""
    text = text.strip()
    if not _QUANTITY_RE.fullmatch(text):
        return None
    value = int(text)
    return value if value >= 1 else None


def parse_price(text: str) -> Decimal | None:
    """0以上の数値なら Decimal を返す。それ以外は None。"""
    text = text.strip()
    if not _PRICE_RE.fullmatch(text):
        return None
    try:
        return Decimal(text)
    except InvalidOperation:  # 正規表現を通れば起きないが念のため
        return None


def parse_date(text: str) -> date | None:
    """YYYY-MM-DD / YYYY/MM/DD を日付にする。存在しない日付は None。"""
    match = _DATE_RE.fullmatch(text.strip())
    if not match:
        return None
    year, _, month, day = match.groups()
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def _is_blank(value: str) -> bool:
    return not value.strip()  # str.strip() は全角スペースも取り除く


def make_issue(row: ShipmentRow, category: str, message: str) -> Issue:
    return Issue(
        line_no=row.line_no,
        detail_id=row.data.get("明細ID", "").strip(),
        slip_no=row.data.get("伝票番号", "").strip(),
        category=category,
        message=message,
        raw=dict(row.data),
    )


def _check_row(row: ShipmentRow) -> list[Issue]:
    data = row.data
    issues: list[Issue] = []
    if row.field_count != len(COLUMNS):
        message = f"この行には値が{row.field_count}個あります（正しくは{len(COLUMNS)}個）。"
        if row.extra:
            message += f"余分な値: {' / '.join(row.extra)}。"
        message += "値の中のカンマ（例: 1,200）や区切りの抜けを確認してください"
        issues.append(make_issue(row, CAT_COLUMN_COUNT, message))
    bad_chars = [c for c in COLUMNS if CONTROL_CHARS_RE.search(data.get(c, ""))]
    if bad_chars:
        issues.append(make_issue(
            row, CAT_CONTROL_CHAR, f"制御文字が含まれています: {', '.join(bad_chars)}"))
    missing = [c for c in REQUIRED_COLUMNS if _is_blank(data.get(c, ""))]
    if missing:
        issues.append(make_issue(row, CAT_MISSING, f"未入力の必須項目: {', '.join(missing)}"))

    checks = (
        ("数量", parse_quantity, CAT_QUANTITY, "1以上の整数（半角）で入力してください"),
        ("単価", parse_price, CAT_PRICE, "0以上の数値（半角）で入力してください"),
        ("出荷日", parse_date, CAT_DATE, "YYYY-MM-DD 形式の実在する日付で入力してください"),
    )
    for column, parser, category, hint in checks:
        value = data.get(column, "")
        if column in missing:
            continue  # 欠損として報告済み
        if parser(value) is None:
            issues.append(make_issue(row, category, f"{column}「{value}」は不正です。{hint}"))
    return issues


def _check_duplicates(rows: list[ShipmentRow]) -> list[Issue]:
    lines_by_id: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        detail_id = row.data.get("明細ID", "").strip()
        if detail_id:
            lines_by_id[detail_id].append(row.line_no)

    issues: list[Issue] = []
    for row in rows:
        detail_id = row.data.get("明細ID", "").strip()
        lines = lines_by_id.get(detail_id, [])
        if len(lines) > 1:
            others = ", ".join(str(n) for n in lines if n != row.line_no)
            issues.append(make_issue(
                row, CAT_DUPLICATE,
                f"明細ID「{detail_id}」が他の行（{others}行目）と重複しています"))
    return issues


def find_row_issues(rows: list[ShipmentRow]) -> list[Issue]:
    """全行をチェックし、見つかった問題を行番号順で返す。"""
    issues = [issue for row in rows for issue in _check_row(row)]
    issues += _check_duplicates(rows)
    return sorted(issues, key=lambda i: i.line_no)
