from __future__ import annotations

from pathlib import Path

from .extractor import extract_payroll_pdf
from .parser import PayrollParser
from .schemas import PayrollDocument


def parse_payroll_pdf(
    path: str | Path,
) -> PayrollDocument:
    """
    Executa o pipeline completo de processamento de um holerite.

    Fluxo:

        PDF
        ↓
        extração
        ↓
        normalização
        ↓
        PayrollExtractedPage
        ↓
        PayrollParser
        ↓
        PayrollDocument
    """

    extracted_pages = extract_payroll_pdf(path)

    parser = PayrollParser()

    return parser.parse(extracted_pages)