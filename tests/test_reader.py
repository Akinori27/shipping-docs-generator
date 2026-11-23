import hashlib

import pytest

from conftest import make_row
from shipdoc.models import COLUMNS
from shipdoc.reader import CsvFormatError, read_shipments


def test_reads_rows_with_line_numbers(csv_factory):
    path = csv_factory([make_row(明細ID="L001"), make_row(明細ID="L002")])
    rows = read_shipments(path)
    assert [r.line_no for r in rows] == [2, 3]
    assert rows[1].data["明細ID"] == "L002"


def test_values_stay_as_text(csv_factory):
    rows = read_shipments(csv_factory([make_row(商品コード="00123")]))
    assert rows[0].data["商品コード"] == "00123"


def test_reads_cp932(csv_factory):
    path = csv_factory([make_row(得意先名="見本物流株式会社")], encoding="cp932")
    assert read_shipments(path)[0].data["得意先名"] == "見本物流株式会社"


def test_missing_column_raises(csv_factory):
    cols = tuple(c for c in COLUMNS if c != "数量")
    path = csv_factory([make_row()], columns=cols)
    with pytest.raises(CsvFormatError, match="数量"):
        read_shipments(path)


def test_empty_file_raises(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_bytes(b"")
    with pytest.raises(CsvFormatError):
        read_shipments(path)


def test_source_file_is_unchanged(csv_factory):
    path = csv_factory([make_row()])
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    read_shipments(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


HEADER = ",".join(COLUMNS)


def write_text(tmp_path, text, name="raw.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_row_with_extra_fields_is_marked(tmp_path):
    # 単価に「1,200」と打ち、引用符なしで保存された行（列が1つ増える）
    path = write_text(tmp_path, HEADER + "\nD1,L1,2026-11-20,C1,客,P1,商品,5,個,1,200,\n")
    row = read_shipments(path)[0]
    assert row.field_count == 12
    assert row.extra == ("",)
    assert row.data["単価"] == "1"


def test_row_with_missing_fields_is_marked(tmp_path):
    path = write_text(tmp_path, HEADER + "\nD1,L1,2026-11-20\n")
    row = read_shipments(path)[0]
    assert row.field_count == 3
    assert row.data["数量"] == ""


def test_duplicate_header_raises(tmp_path):
    path = write_text(tmp_path, HEADER + ",数量\nD1,L1,2026-11-20,C1,客,P1,商品,5,個,100,,7\n")
    with pytest.raises(CsvFormatError, match="重複"):
        read_shipments(path)
