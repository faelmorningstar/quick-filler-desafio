import pymupdf

from app.pdf.analyzer import analyze_pdf, page_has_text_layer


def test_page_has_text_layer_when_text_exists(pdf_with_text_layer):
    doc = pymupdf.open(pdf_with_text_layer)
    try:
        assert page_has_text_layer(doc[0]) is True
    finally:
        doc.close()


def test_page_has_text_layer_when_text_is_empty(pdf_without_text_layer):
    doc = pymupdf.open(pdf_without_text_layer)
    try:
        assert page_has_text_layer(doc[0]) is False
    finally:
        doc.close()


def test_analyze_pdf_returns_one_entry_per_page(multi_page_pdf):
    report = analyze_pdf(multi_page_pdf)

    assert report.page_count == 2
    assert len(report.pages) == 2
    assert [page.page_number for page in report.pages] == [1, 2]


def test_analyze_pdf_detects_text_layer(pdf_with_text_layer):
    report = analyze_pdf(pdf_with_text_layer)

    assert report.page_count == 1
    assert report.pages[0].has_text_layer is True


def test_analyze_pdf_detects_missing_text_layer(pdf_without_text_layer):
    report = analyze_pdf(pdf_without_text_layer)

    assert report.page_count == 1
    assert report.pages[0].has_text_layer is False


def test_analyze_pdf_sets_orientation(multi_page_pdf):
    report = analyze_pdf(multi_page_pdf)

    assert report.pages[0].orientation == "retrato"
    assert report.pages[0].width_pt > 0
    assert report.pages[0].height_pt > 0
