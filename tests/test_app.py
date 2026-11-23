import hashlib
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from conftest import make_row
from shipdoc import cli
from shipdoc.app import run

ROOT = Path(__file__).parent.parent
SAMPLE = ROOT / "sample_data" / "shipments_sample.csv"
TEMPLATE = ROOT / "templates" / "納品明細テンプレート.xlsx"
NOW = datetime(2026, 11, 23, 15, 30, 0)


def test_sample_data_end_to_end(tmp_path):
    summary = run(SAMPLE, tmp_path, TEMPLATE, NOW)
    out = summary.output_dir
    assert out == tmp_path / "20261123_153000"
    assert summary.total_rows == 10
    assert summary.slip_count == 3
    assert summary.held_slip_nos == ["D0004", "D0005"]
    for slip_no in ("D0001", "D0002", "D0003"):
        assert (out / "excel" / f"納品明細_{slip_no}.xlsx").exists()
        assert (out / "pdf" / f"納品明細_{slip_no}.pdf").exists()
    assert not (out / "excel" / "納品明細_D0004.xlsx").exists()

    ws = load_workbook(out / "要確認一覧.xlsx").active
    rows = [(r[0], r[1], r[3]) for r in ws.iter_rows(min_row=2, max_col=4, values_only=True)]
    assert rows == [
        (9, "L0008", "同一伝票内に要確認行あり"),
        (10, "L0009", "数量不正"),
        (11, "L0010", "必須項目欠損"),
    ]
    assert summary.issue_count == 3
    report = (out / "処理結果.txt").read_text(encoding="utf-8")
    assert "出力した伝票: 3件" in report and "D0004" in report


def test_source_csv_is_not_modified(tmp_path):
    before = hashlib.sha256(SAMPLE.read_bytes()).hexdigest()
    run(SAMPLE, tmp_path, TEMPLATE, NOW)
    assert hashlib.sha256(SAMPLE.read_bytes()).hexdigest() == before


def test_run_all_rows_invalid(tmp_path, csv_factory):
    path = csv_factory([make_row(明細ID="L1", 数量="0"), make_row(明細ID="L2", 単価="")])
    summary = run(path, tmp_path / "out", TEMPLATE, NOW)
    assert summary.slip_count == 0
    assert summary.issue_count == 2
    assert (summary.output_dir / "要確認一覧.xlsx").exists()


def test_each_run_gets_new_folder(tmp_path):
    first = run(SAMPLE, tmp_path, TEMPLATE, NOW).output_dir
    second = run(SAMPLE, tmp_path, TEMPLATE, NOW).output_dir
    assert first != second
    assert (first / "要確認一覧.xlsx").exists() and (second / "要確認一覧.xlsx").exists()


def test_slip_numbers_that_collide_after_sanitizing(tmp_path, csv_factory):
    path = csv_factory([make_row(伝票番号="A/B", 明細ID="L1"),
                        make_row(伝票番号="A_B", 明細ID="L2")])
    summary = run(path, tmp_path, TEMPLATE, NOW)
    assert len({p.name for p in summary.excel_paths}) == 2
    assert len({p.name for p in summary.pdf_paths}) == 2


def test_cli_success(tmp_path, capsys):
    code = cli.main([str(SAMPLE), "--output", str(tmp_path)])
    assert code == 0
    printed = capsys.readouterr().out
    assert "出力した伝票: 3件" in printed


def test_cli_missing_file(tmp_path, capsys):
    code = cli.main([str(tmp_path / "nothing.csv"), "--output", str(tmp_path)])
    assert code == 1
    assert "見つかりません" in capsys.readouterr().out


def test_cli_bad_columns(tmp_path, capsys):
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n", encoding="utf-8")
    code = cli.main([str(bad), "--output", str(tmp_path)])
    assert code == 1
    assert "列が想定と違います" in capsys.readouterr().out


def test_case_only_different_slip_numbers_get_separate_files(tmp_path, csv_factory):
    path = csv_factory([make_row(伝票番号="a1", 明細ID="L1", 得意先名="客A"),
                        make_row(伝票番号="A1", 明細ID="L2", 得意先名="客B")])
    summary = run(path, tmp_path / "out", TEMPLATE, NOW)
    assert summary.slip_count == 2
    assert len(list((summary.output_dir / "excel").glob("*.xlsx"))) == 2
    assert len(list((summary.output_dir / "pdf").glob("*.pdf"))) == 2


def test_unquoted_comma_in_price_holds_slip(tmp_path):
    from shipdoc.models import COLUMNS
    path = tmp_path / "raw.csv"
    path.write_text(",".join(COLUMNS) + "\n"
                    "D1,L1,2026-11-20,C1,客,P1,商品,5,個,1,200,\n"
                    "D2,L2,2026-11-20,C1,客,P1,商品,5,個,1200,\n", encoding="utf-8")
    summary = run(path, tmp_path / "out", TEMPLATE, NOW)
    assert summary.slip_count == 1
    assert summary.held_slip_nos == ["D1"]


def test_too_long_product_name_holds_slip(tmp_path, csv_factory):
    path = csv_factory([make_row(明細ID="L1", 商品名="長" * 47)])
    summary = run(path, tmp_path / "out", TEMPLATE, NOW)
    assert summary.slip_count == 0
    ws = load_workbook(summary.output_dir / "要確認一覧.xlsx").active
    assert ws["D2"].value == "帳票に収まらない"


def test_control_character_does_not_crash(tmp_path, csv_factory):
    path = csv_factory([make_row(明細ID="L1", 備考="\x1a"), make_row(伝票番号="D2", 明細ID="L2")])
    summary = run(path, tmp_path / "out", TEMPLATE, NOW)
    assert summary.slip_count == 1
    assert summary.held_slip_nos == ["D0001"]


def test_cli_unexpected_error(tmp_path, capsys, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("disk full")
    monkeypatch.setattr(cli, "run", boom)
    code = cli.main([str(SAMPLE), "--output", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "予期しないエラー" in out and "disk full" in out
