#!/bin/bash
# 初回だけダブルクリックしてください。このフォルダの中に専用の実行環境（.venv）を作ります。
cd "$(dirname "$0")" || exit 1

pause() { echo; read -r -p "Enterキーを押すと閉じます" _; }

echo "=== 納品明細 自動生成ツール：初回セットアップ ==="
if ! command -v python3 >/dev/null 2>&1; then
  echo "[エラー] Python 3 が見つかりません。README の「準備」を参照してください。"
  pause; exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "[エラー] Python 3.9 以上が必要です（現在: $(python3 --version)）。"
  pause; exit 1
fi

echo "Python: $(python3 --version)"
echo "実行環境を作成しています..."
python3 -m venv .venv || { echo "[エラー] 実行環境の作成に失敗しました。"; pause; exit 1; }
echo "必要なライブラリをインストールしています（1〜2分かかることがあります）..."
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt -e . \
  || { echo "[エラー] ライブラリのインストールに失敗しました。ネット接続を確認してください。"; pause; exit 1; }

echo
echo "セットアップが完了しました。次は「実行.command」をダブルクリックしてください。"
pause
