from openpyxl import load_workbook

from conftest import make_row
from shipdoc.models import COLUMNS, Issue
from shipdoc.review_writer import REVIEW_HEADERS, write_review_list


def test_writes_issue_rows_with_raw_data(tmp_path):
    raw = make_row(明細ID="L9", 数量="-2", 商品名="=1+1")
    issue = Issue(line_no=10, detail_id="L9", slip_no="D0004", category="数量不正",
                  message="数量「-2」は不正です", raw=raw)
    ws = load_workbook(write_review_list([issue], tmp_path / "r.xlsx")).active
    assert [c.value for c in ws[1]] == list(REVIEW_HEADERS) + list(COLUMNS)
    values = [c.value for c in ws[2]]
    assert values[:5] == [10, "L9", "D0004", "数量不正", "数量「-2」は不正です"]
    assert values[5:] == [raw[c] or None for c in COLUMNS]
    name_cell = ws.cell(row=2, column=len(REVIEW_HEADERS) + COLUMNS.index("商品名") + 1)
    assert name_cell.data_type == "s"


def test_empty_list_says_no_issues(tmp_path):
    ws = load_workbook(write_review_list([], tmp_path / "r.xlsx")).active
    assert ws["A2"].value == "要確認の行はありません"
