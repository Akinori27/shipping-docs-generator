"""要確認一覧（Excel）を書き出す。元の行データは加工せずそのまま載せる。"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .models import COLUMNS, Issue

REVIEW_HEADERS: tuple[str, ...] = ("CSV行番号", "明細ID", "伝票番号", "区分", "内容")
_WIDTHS = (10, 10, 10, 22, 60)
_HEADER_FILL = PatternFill("solid", fgColor="FCE4D6")
_RAW_FILL = PatternFill("solid", fgColor="F2F2F2")


def write_review_list(issues: list[Issue], out_path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "要確認一覧"

    headers = list(REVIEW_HEADERS) + list(COLUMNS)
    ws.append(headers)
    for idx, _ in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=idx)
        cell.font = Font(bold=True)
        cell.fill = _HEADER_FILL if idx <= len(REVIEW_HEADERS) else _RAW_FILL
        cell.alignment = Alignment(horizontal="center")
    for idx, width in enumerate(_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    for idx in range(len(REVIEW_HEADERS) + 1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(idx)].width = 14

    if not issues:
        ws["A2"] = "要確認の行はありません"
    for row_idx, issue in enumerate(issues, start=2):
        ws.cell(row=row_idx, column=1, value=issue.line_no)
        texts = [issue.detail_id, issue.slip_no, issue.category, issue.message]
        texts += [issue.raw.get(c, "") for c in COLUMNS]
        for col_idx, text in enumerate(texts, start=2):
            if text == "":
                continue
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = text
            cell.data_type = "s"  # 「=」で始まる値も数式にしない

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{max(ws.max_row, 2)}"

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path
