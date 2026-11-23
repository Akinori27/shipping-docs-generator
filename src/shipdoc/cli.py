"""コマンドラインから実行する入口。

使い方:
    python -m shipdoc                      # サンプルデータで実行
    python -m shipdoc 出荷データ.csv
    python -m shipdoc 出荷データ.csv --output 出力先フォルダ
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .app import run
from .reader import CsvFormatError

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "sample_data" / "shipments_sample.csv"
DEFAULT_OUTPUT = ROOT / "output"
DEFAULT_TEMPLATE = ROOT / "templates" / "納品明細テンプレート.xlsx"


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="shipdoc",
        description="出荷CSVから納品明細Excel/PDFを作成し、問題のある行を要確認一覧に出力します。",
    )
    p.add_argument("csv", nargs="?", type=Path, default=DEFAULT_CSV,
                   help="出荷データCSV（省略時はサンプルデータ）")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="出力先フォルダ")
    p.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="納品明細テンプレート")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    for path, label in ((args.csv, "CSVファイル"), (args.template, "テンプレート")):
        if not path.is_file():
            print(f"[エラー] {label}が見つかりません: {path}")
            return 1
    try:
        summary = run(args.csv, args.output, args.template)
    except CsvFormatError as e:
        print(f"[エラー] {e}")
        return 1
    except Exception as e:  # 想定外のエラーでも、画面に分かる言葉で伝える
        print(f"[エラー] 予期しないエラーが発生したため処理を中止しました: {type(e).__name__}: {e}")
        print(f"途中まで作成されたファイルがある場合は {args.output} 内の最新フォルダにあります。")
        print("このメッセージを添えて開発者へご連絡ください。")
        return 1
    print(summary.report())
    return 0
