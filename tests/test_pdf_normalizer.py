import pymupdf

from backend.app.payroll.normalizer import normalize_pdf_page


def test_normalize_real_pdf_page():
    doc = pymupdf.open("payroll-01.pdf")

    try:
        lines = normalize_pdf_page(doc[0])

        assert lines
        assert any(
            "REMUNERAÇÃOMES" in line
            for line in lines
        )

    finally:
        doc.close()