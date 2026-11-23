"""出荷CSVを読み込む。元ファイルは読み取り専用で開き、一切変更しない。"""
from __future__ import annotations

import csv
import io
from pathlib import Path

from .models import COLUMNS, ShipmentRow

# 試す順番: UTF-8（BOM付き・なし）→ Excelで保存したCSVに多い Shift_JIS
ENCODINGS: tuple[str, ...] = ("utf-8-sig", "cp932")


class CsvFormatError(Exception):
    """CSVの形式そのものが想定と違い、処理を続けられないときのエラー。"""


def _decode(raw: bytes) -> str:
    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise CsvFormatError("文字コードを判別できません（UTF-8 または Shift_JIS で保存してください）")


def read_shipments(path: Path) -> list[ShipmentRow]:
    """CSVを読み込み、行番号つきの行データを返す。値は文字列のまま。"""
    raw = Path(path).read_bytes()  # 読み取りのみ
    if not raw.strip():
        raise CsvFormatError("CSVが空です")

    reader = csv.DictReader(io.StringIO(_decode(raw), newline=""))
    header = [h.strip() for h in (reader.fieldnames or [])]
    missing = [c for c in COLUMNS if c not in header]
    unknown = [h for h in header if h not in COLUMNS]
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"不足している列: {', '.join(missing)}")
        if unknown:
            parts.append(f"想定外の列: {', '.join(unknown)}")
        raise CsvFormatError("CSVの列が想定と違います（" + " / ".join(parts) + "）")
    reader.fieldnames = header

    rows: list[ShipmentRow] = []
    for record in reader:
        if all(not (v or "").strip() for k, v in record.items() if k is not None):
            continue  # 完全な空行は読み飛ばす
        data = {c: (record.get(c) or "") for c in COLUMNS}
        # line_num は読み終えた行の物理行番号（ヘッダ=1）
        rows.append(ShipmentRow(line_no=reader.line_num, data=data))
    return rows
