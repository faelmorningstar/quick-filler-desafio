from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(frozen=True)
class ExtractedLine:
    """
    Representa uma linha extraída de uma página PDF.

    O texto é preservado junto com sua posição aproximada no documento.
    """

    text: str
    x: float
    y: float
    width: float


@dataclass(frozen=True)
class ExtractedPage:
    """
    Representa o conteúdo extraído de uma página.
    """

    page_number: int
    width: float
    height: float
    lines: tuple[ExtractedLine, ...]


def extract_pdf(path: str | Path) -> tuple[ExtractedPage, ...]:
    """
    Extrai linhas de texto de todas as páginas do PDF.

    A ordem das páginas é preservada.
    A posição espacial de cada linha também é preservada.
    """

    pdf_path = Path(path)

    doc = pymupdf.open(pdf_path)

    try:
        pages: list[ExtractedPage] = []

        for page_number, page in enumerate(doc, start=1):
            lines = _extract_page_lines(page)

            pages.append(
                ExtractedPage(
                    page_number=page_number,
                    width=page.rect.width,
                    height=page.rect.height,
                    lines=tuple(lines),
                )
            )

        return tuple(pages)

    finally:
        doc.close()


def _extract_page_lines(
    page: pymupdf.Page,
) -> list[ExtractedLine]:
    """
    Extrai linhas visuais da página.

    O PyMuPDF fornece os dados organizados em blocos,
    linhas e spans. Aqui transformamos essa estrutura
    em uma representação simples para o restante do pipeline.
    """

    raw = page.get_text("dict")

    extracted: list[ExtractedLine] = []

    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            spans = line.get("spans", [])

            if not spans:
                continue

            text_parts: list[str] = []

            x0 = None
            x1 = None
            y0 = None

            for span in spans:
                text = span.get("text", "")

                if not text:
                    continue

                text_parts.append(text)

                span_x0 = float(span["bbox"][0])
                span_y0 = float(span["bbox"][1])
                span_x1 = float(span["bbox"][2])

                if x0 is None:
                    x0 = span_x0
                    y0 = span_y0

                x0 = min(x0, span_x0)
                x1 = span_x1

            text = " ".join("".join(text_parts).split())

            if not text:
                continue

            if x0 is None or x1 is None or y0 is None:
                continue

            extracted.append(
                ExtractedLine(
                    text=text,
                    x=x0,
                    y=y0,
                    width=x1 - x0,
                )
            )

    extracted.sort(key=lambda item: (item.y, item.x))

    return extracted