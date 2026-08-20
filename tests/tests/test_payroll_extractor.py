from app.payroll.extractor import extract_payroll_pdf


def test_extract_payroll_pdf_preserves_page_order(multi_page_pdf):
    pages = extract_payroll_pdf(multi_page_pdf)

    assert [page.page for page in pages] == [1, 2]


def test_extract_payroll_pdf_preserves_empty_pages(pdf_without_text_layer):
    pages = extract_payroll_pdf(pdf_without_text_layer)

    assert len(pages) == 1
    assert pages[0].page == 1
    assert pages[0].lines == []


def test_extract_payroll_pdf_extracts_lines(pdf_with_text_layer):
    pages = extract_payroll_pdf(pdf_with_text_layer)

    assert len(pages) == 1
    assert len(pages[0].lines) > 0


def test_extract_payroll_pdf_assigns_line_order(pdf_with_text_layer):
    pages = extract_payroll_pdf(pdf_with_text_layer)

    orders = [line.order for line in pages[0].lines]

    assert orders == list(range(len(orders)))