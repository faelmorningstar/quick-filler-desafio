from __future__ import annotations

import pymupdf


def extract_native_page(page: pymupdf.Page) -> dict:
    """
    Extrai o conteúdo textual nativo de uma página
    preservando sua estrutura e coordenadas.
    """
    return page.get_text("dict")

def extract_native_text(page: pymupdf.Page) -> str:
    """
    Extrai todo o texto nativo de uma página, preservando
    a ordem fornecida pelo PyMuPDF.
    """
    data = extract_native_page(page)

    return "".join(
        span["text"]
        for block in data["blocks"]
        if block.get("type") == 0
        for line in block.get("lines", [])
        for span in line.get("spans", [])
    )

def native_text_length(page: pymupdf.Page) -> int:
    """Return the number of characters in the native text of a page."""
    return len(extract_native_text(page))