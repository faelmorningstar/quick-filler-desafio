"""Análise estrutural de PDFs: detecção de camada textual por página."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(frozen=True)
class PageAnalysis:
    page_number: int
    width_pt: float
    height_pt: float
    orientation: str
    has_text_layer: bool


@dataclass(frozen=True)
class PdfAnalysis:
    path: Path
    page_count: int
    pages: tuple[PageAnalysis, ...]


def _orientation(width_pt: float, height_pt: float) -> str:
    return "retrato" if height_pt > width_pt else "paisagem"


def page_has_text_layer(page: pymupdf.Page) -> bool:
    return bool(page.get_text("text").strip())


def analyze_pdf(pdf_path: str | Path) -> PdfAnalysis:
    path = Path(pdf_path)
    doc = pymupdf.open(path)

    try:
        pages: list[PageAnalysis] = []

        for page_number, page in enumerate(doc, start=1):
            rect = page.rect
            pages.append(
                PageAnalysis(
                    page_number=page_number,
                    width_pt=rect.width,
                    height_pt=rect.height,
                    orientation=_orientation(rect.width, rect.height),
                    has_text_layer=page_has_text_layer(page),
                )
            )

        return PdfAnalysis(
            path=path,
            page_count=len(doc),
            pages=tuple(pages),
        )
    finally:
        doc.close()
