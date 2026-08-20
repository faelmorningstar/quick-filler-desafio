from __future__ import annotations

from pathlib import Path

import pymupdf

from .normalizer import normalize_pdf_page_detailed
from .schemas import PayrollExtractedLine, PayrollExtractedPage


def extract_payroll_pdf(
    path: str | Path,
    y_tolerance: float = 2.0,
) -> list[PayrollExtractedPage]:
    """
    Extrai e normaliza todas as páginas de um PDF de holerite.

    Fluxo:

        PDF
        -> PyMuPDF
        -> normalizer
        -> PayrollExtractedPage

    A ordem das páginas é preservada.
    Páginas sem texto continuam presentes no resultado.
    """

    pdf_path = Path(path)

    doc = pymupdf.open(pdf_path)

    try:
        pages: list[PayrollExtractedPage] = []

        for page_number, page in enumerate(doc, start=1):
            normalized_lines = normalize_pdf_page_detailed(
                page,
                y_tolerance=y_tolerance,
            )

            lines = [
                PayrollExtractedLine(
                    text=line.text,
                    order=order,
                )
                for order, line in enumerate(normalized_lines)
            ]

            pages.append(
                PayrollExtractedPage(
                    page=page_number,
                    lines=lines,
                )
            )

        return pages

    finally:
        doc.close()