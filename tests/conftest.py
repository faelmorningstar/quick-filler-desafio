from pathlib import Path

import pymupdf
import pytest


@pytest.fixture
def pdf_with_text_layer(tmp_path: Path) -> Path:
    path = tmp_path / "with_text.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "09:00")
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def pdf_without_text_layer(tmp_path: Path) -> Path:
    path = tmp_path / "without_text.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def multi_page_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "multi_page.pdf"
    doc = pymupdf.open()

    first_page = doc.new_page()
    first_page.insert_text((72, 72), "pagina 1")

    doc.new_page()

    doc.save(path)
    doc.close()
    return path
