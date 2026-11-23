"""納品明細テンプレートのセル配置。

テンプレート作成（template_builder）と書き込み（excel_writer）は、
必ずこの対応表だけを参照する。顧客の既存書式に合わせるときは、
ここのセル番地を書き換えれば流し込み先が変わる。
"""

SHEET_NAME = "納品明細"
TITLE = "納 品 明 細 書"
LAST_COLUMN = "H"

TITLE_CELL = "A1"
ISSUE_DATE_LABEL_CELL, ISSUE_DATE_CELL = "G2", "H2"
SLIP_NO_LABEL_CELL, SLIP_NO_CELL = "G3", "H3"
CUSTOMER_CODE_LABEL_CELL, CUSTOMER_CODE_CELL = "A3", "C3"  # 見出しは A3:B3 を結合
CUSTOMER_NAME_CELL = "A4"  # A4:D4 を結合
CUSTOMER_NAME_RANGE = "A4:D4"
HONORIFIC_CELL = "E4"  # 「御中」
SHIP_DATE_LABEL_CELL, SHIP_DATE_CELL = "A6", "C6"  # 見出しは A6:B6 を結合
GREETING_CELL = "A7"

ISSUER_CELLS = ("F5", "F6", "F7")  # 発行元（架空）

HEADER_ROW = 9
ITEM_FIRST_ROW = 10
ITEM_ROWS = 15  # 明細欄の行数（これを超える伝票は要確認に回す）
TOTAL_ROW = ITEM_FIRST_ROW + ITEM_ROWS  # 25
TOTAL_LABEL_CELL = f"C{TOTAL_ROW}"
TOTAL_QUANTITY_CELL = f"D{TOTAL_ROW}"
TOTAL_AMOUNT_CELL = f"G{TOTAL_ROW}"
NOTE_CELL = f"A{TOTAL_ROW + 2}"

# 明細欄の列（キー → 列）と見出し
ITEM_COLUMNS = {
    "no": "A",
    "product_code": "B",
    "product_name": "C",
    "quantity": "D",
    "unit": "E",
    "unit_price": "F",
    "amount": "G",
    "note": "H",
}
ITEM_HEADERS = {
    "no": "No",
    "product_code": "商品コード",
    "product_name": "商品名",
    "quantity": "数量",
    "unit": "単位",
    "unit_price": "単価",
    "amount": "金額",
    "note": "備考",
}
COLUMN_WIDTHS = {"A": 6, "B": 12, "C": 30, "D": 8, "E": 6, "F": 11, "G": 13, "H": 18}

ISSUER_LINES = ("デモ物流株式会社（架空）", "東京都架空区サンプル1-2-3", "TEL 00-0000-0000")
TOTAL_LABEL = "合計（税抜）"
GREETING = "下記のとおり納品いたしました。"
NOTE = "※ 本帳票はデモ用の架空データから自動生成したものです。"
