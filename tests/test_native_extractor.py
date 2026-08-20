import glob

import pymupdf

from app.pdf.native_extractor import (
    extract_native_page,
    extract_native_text,
    native_text_length,
)


def test_extract_native_page_returns_dict(pdf_with_text_layer):
    doc = pymupdf.open(pdf_with_text_layer)

    try:
        data = extract_native_page(doc[0])

        assert isinstance(data, dict)
        assert "width" in data
        assert "height" in data
        assert "blocks" in data
        assert isinstance(data["blocks"], list)
    finally:
        doc.close()


def test_native_extraction_reports_text_by_page():
    pdf_paths = sorted(glob.glob("payroll-*.pdf"))

    assert len(pdf_paths) == 4

    for pdf_path in pdf_paths:
        doc = pymupdf.open(pdf_path)

        try:
            for page in doc:
                text = extract_native_text(page)

                assert isinstance(text, str)
                assert len(text) >= 0
        finally:
            doc.close()

def test_native_text_length_is_non_negative(pdf_with_text_layer):
    doc = pymupdf.open(pdf_with_text_layer)
    try:
        assert native_text_length(doc[0]) >= 0
    finally:
        doc.close()