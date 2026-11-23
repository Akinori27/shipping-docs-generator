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
