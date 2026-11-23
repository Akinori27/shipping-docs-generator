"""処理全体の流れ: 読込 → チェック → 伝票化 → 出力。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .excel_writer import safe_filename, write_slip_excel
from .grouper import group_slips
from .pdf_writer import write_slip_pdf
from .reader import read_shipments
from .review_writer import write_review_list
from .validator import find_row_issues

REVIEW_FILE = "要確認一覧.xlsx"
REPORT_FILE = "処理結果.txt"


@dataclass
class RunSummary:
    source: Path
    output_dir: Path
    total_rows: int
    slip_count: int
    issue_count: int
    held_slip_nos: list[str]
    excel_paths: list[Path] = field(default_factory=list)
    pdf_paths: list[Path] = field(default_factory=list)

    def report(self) -> str:
        held = "、".join(self.held_slip_nos) if self.held_slip_nos else "なし"
        lines = [
            "=== 納品明細 自動生成 処理結果 ===",
            f"入力ファイル: {self.source}",
            f"読み込んだ行: {self.total_rows}行",
            f"出力した伝票: {self.slip_count}件",
            f"保留した伝票: {held}",
            f"要確認の行  : {self.issue_count}行（{REVIEW_FILE} を確認してください）"
            if self.issue_count else "要確認の行  : 0行",
            f"出力先      : {self.output_dir}",
        ]
        return "\n".join(lines)


def _new_output_dir(output_root: Path, now: datetime) -> Path:
    """日時名のフォルダを新規作成する。同名があれば _2, _3 … を付ける（上書きしない）。"""
    base = now.strftime("%Y%m%d_%H%M%S")
    candidate, n = output_root / base, 1
    while True:
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        except FileExistsError:
            n += 1
            candidate = output_root / f"{base}_{n}"


def _unique_stem(slip_no: str, used: set[str]) -> str:
    stem = f"納品明細_{safe_filename(slip_no)}"
    candidate, n = stem, 1
    while candidate in used:
        n += 1
        candidate = f"{stem}_{n}"
    used.add(candidate)
    return candidate


def run(csv_path: Path, output_root: Path, template_path: Path,
        now: datetime | None = None) -> RunSummary:
    now = now or datetime.now()
    csv_path, output_root = Path(csv_path), Path(output_root)

    rows = read_shipments(csv_path)
    result = group_slips(rows, find_row_issues(rows))

    output_dir = _new_output_dir(output_root, now)
    excel_paths, pdf_paths, used = [], [], set()
    for slip in result.slips:
        stem = _unique_stem(slip.slip_no, used)
        excel_paths.append(write_slip_excel(
            slip, template_path, output_dir / "excel" / f"{stem}.xlsx", now.date()))
        pdf_paths.append(write_slip_pdf(slip, output_dir / "pdf" / f"{stem}.pdf", now.date()))

    write_review_list(result.issues, output_dir / REVIEW_FILE)

    output_slips = {s.slip_no for s in result.slips}
    held = list(dict.fromkeys(
        i.slip_no for i in result.issues if i.slip_no and i.slip_no not in output_slips))

    summary = RunSummary(
        source=csv_path,
        output_dir=output_dir,
        total_rows=len(rows),
        slip_count=len(result.slips),
        issue_count=len({i.line_no for i in result.issues}),
        held_slip_nos=held,
        excel_paths=excel_paths,
        pdf_paths=pdf_paths,
    )
    (output_dir / REPORT_FILE).write_text(summary.report() + "\n", encoding="utf-8")
    return summary
