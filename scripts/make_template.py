"""デモ用テンプレート（templates/納品明細テンプレート.xlsx）を作り直す。

使い方: python scripts/make_template.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from shipdoc.template_builder import build_template  # noqa: E402

if __name__ == "__main__":
    path = build_template(ROOT / "templates" / "納品明細テンプレート.xlsx")
    print(f"作成しました: {path}")
