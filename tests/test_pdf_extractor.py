from app.pdf.extractor import extract_pdf


def test_extract_pdf_preserves_page_order(multi_page_pdf):
    pages = extract_pdf(multi_page_pdf)

    assert len(pages) == 2
    assert [page.page_number for page in pages] == [1, 2]


def test_extract_pdf_returns_page_dimensions(multi_page_pdf):
    pages = extract_pdf(multi_page_pdf)

    assert pages[0].width > 0
    assert pages[0].height > 0


def test_extract_pdf_extracts_text(pdf_with_text_layer):
    pages = extract_pdf(pdf_with_text_layer)

    assert len(pages) == 1
    assert len(pages[0].lines) > 0


def test_extract_pdf_preserves_line_position(pdf_with_text_layer):
    pages = extract_pdf(pdf_with_text_layer)

    line = pages[0].lines[0]

    assert line.text
    assert line.x >= 0
    assert line.y >= 0
    assert line.width > 0