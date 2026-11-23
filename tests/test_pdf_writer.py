from datetime import date

from pypdf import PdfReader

from conftest import make_slip
from shipdoc.pdf_writer import write_slip_pdf

ISSUE_DATE = date(2026, 11, 23)


def pdf_text(path):
    return "".join(page.extract_text() for page in PdfReader(path).pages)


def test_creates_one_page_pdf(tmp_path):
    out = write_slip_pdf(make_slip(), tmp_path / "out.pdf", ISSUE_DATE)
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(out).pages) == 1


def test_pdf_contains_slip_values(tmp_path):
    out = write_slip_pdf(make_slip(n_items=2), tmp_path / "out.pdf", ISSUE_DATE)
    text = pdf_text(out)
    for expected in ("D0001", "2026/11/20", "2026/11/23", "00121", "7,200"):
        assert expected in text


def test_pdf_contains_japanese_text(tmp_path):
    out = write_slip_pdf(make_slip(), tmp_path / "out.pdf", ISSUE_DATE)
    text = pdf_text(out)
    assert "サンプル商事株式会社" in text
    assert "商品1" in text


def test_fifteen_items_stay_on_one_page(tmp_path):
    out = write_slip_pdf(make_slip(n_items=15), tmp_path / "out.pdf", ISSUE_DATE)
    assert len(PdfReader(out).pages) == 1


def test_long_text_shrinks_to_fit_column():
    from reportlab.pdfbase.pdfmetrics import stringWidth

    from shipdoc.pdf_writer import FONT, fit_font_size

    long_name = "業務用高耐久ステンレス製多目的収納ラック（大型・キャスター付き）"
    size = fit_font_size(long_name, width=200, base=9, minimum=5)
    assert 5 <= size < 9
    assert stringWidth(long_name, FONT, size) <= 200
    assert fit_font_size("短い名前", width=150, base=9, minimum=5) == 9


def test_long_product_name_is_printed_in_full(tmp_path):
    name = "業務用高耐久ステンレス製多目的収納ラック（大型）"
    out = write_slip_pdf(make_slip(product_name=name), tmp_path / "out.pdf", ISSUE_DATE)
    assert name in pdf_text(out).replace("\n", "")


def test_layout_problems_none_for_normal_slip():
    from shipdoc.pdf_writer import layout_problems
    assert layout_problems(make_slip(n_items=3)) == []


def test_layout_problems_detects_too_long_name():
    from shipdoc.pdf_writer import layout_problems
    problems = layout_problems(make_slip(n_items=1, product_name="長" * 47))
    assert len(problems) == 1
    assert "商品名" in problems[0] and "L001" in problems[0]


def test_layout_problems_detects_huge_amount():
    from decimal import Decimal

    from shipdoc.pdf_writer import layout_problems
    slip = make_slip(n_items=1, quantity=999999, unit_price=Decimal("999999999"))
    assert any("金額" in p for p in layout_problems(slip))


def test_layout_problems_detects_long_customer_name():
    from dataclasses import replace

    from shipdoc.pdf_writer import layout_problems
    slip = replace(make_slip(), customer_name="株式会社" * 12)
    assert any("得意先名" in p for p in layout_problems(slip))


def test_moderately_long_values_fit():
    from dataclasses import replace
    from decimal import Decimal

    from shipdoc.pdf_writer import layout_problems
    slip = replace(make_slip(n_items=1, product_name="業務用高耐久ステンレス製収納ラック（大型）",
                             quantity=12345, unit_price=Decimal("98765123")),
                   customer_name="株式会社サンプルホールディングス東日本支社")
    assert layout_problems(slip) == []
