#!/bin/bash
# ダブルクリックで実行します。出荷CSVを選ぶと、納品明細のExcel/PDFと要確認一覧を作ります。
cd "$(dirname "$0")" || exit 1

pause() { echo; read -r -p "Enterキーを押すと閉じます" _; }

if [ ! -x .venv/bin/python ]; then
  echo "[エラー] 先に「セットアップ.command」をダブルクリックしてください。"
  pause; exit 1
fi

choice=$(osascript <<'APPLESCRIPT'
try
  set r to display dialog "出荷データ（CSV）から納品明細を作成します。" buttons {"キャンセル", "サンプルで試す", "CSVを選ぶ"} default button "CSVを選ぶ" cancel button "キャンセル" with title "納品明細 自動生成ツール"
  if button returned of r is "サンプルで試す" then return "SAMPLE"
  return POSIX path of (choose file with prompt "出荷データのCSVファイルを選んでください" of type {"public.comma-separated-values-text", "csv"})
on error
  return ""
end try
APPLESCRIPT
)

if [ -z "$choice" ]; then
  echo "キャンセルしました。"
  exit 0
elif [ "$choice" = "SAMPLE" ]; then
  echo "サンプルデータで実行します。"
  set --
else
  set -- "$choice"
fi

.venv/bin/python -m shipdoc "$@"
status=$?
if [ $status -eq 0 ]; then
  latest=$(ls -dt output/*/ 2>/dev/null | head -n 1)
  [ -n "$latest" ] && open "$latest"
fi
pause
exit $status
