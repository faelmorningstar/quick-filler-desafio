from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence


@dataclass(frozen=True)
class TextSpan:
    """
    Fragmento de texto extraído de uma página PDF.
    """

    text: str
    x: float
    y: float
    width: float


@dataclass(frozen=True)
class NormalizedLine:
    """
    Linha reconstruída a partir dos spans do PDF.

    Os spans permanecem disponíveis para que etapas posteriores
    possam utilizar a geometria original.
    """

    text: str
    spans: tuple[TextSpan, ...]
    y: float


def normalize_spans(
    spans: Sequence[TextSpan],
    y_tolerance: float = 2.0,
) -> list[str]:
    """
    Compatibilidade com a primeira versão do normalizador.

    Retorna apenas as linhas de texto.
    """

    lines = normalize_spans_detailed(
        spans,
        y_tolerance=y_tolerance,
    )

    return [line.text for line in lines]


def normalize_spans_detailed(
    spans: Sequence[TextSpan],
    y_tolerance: float = 2.0,
) -> list[NormalizedLine]:
    """
    Agrupa spans pela posição vertical e ordena pela posição horizontal.

    Diferentemente da versão simples, preserva os spans originais.
    """

    valid_spans = [
        span
        for span in spans
        if span.text.strip()
    ]

    if not valid_spans:
        return []

    ordered = sorted(
        valid_spans,
        key=lambda span: (span.y, span.x),
    )

    lines: list[list[TextSpan]] = []

    for span in ordered:
        placed = False

        for line in lines:
            reference_y = line[0].y

            if abs(span.y - reference_y) <= y_tolerance:
                line.append(span)
                placed = True
                break

        if not placed:
            lines.append([span])

    result: list[NormalizedLine] = []

    for line in lines:
        ordered_line = sorted(
            line,
            key=lambda span: span.x,
        )

        text = " ".join(
            span.text.strip()
            for span in ordered_line
            if span.text.strip()
        )

        if text:
            result.append(
                NormalizedLine(
                    text=text,
                    spans=tuple(ordered_line),
                    y=ordered_line[0].y,
                )
            )

    return result


def normalize_pdf_page(
    page,
    y_tolerance: float = 2.0,
) -> list[str]:
    """
    Extrai spans de uma página PyMuPDF
    e retorna linhas normalizadas.
    """

    spans: list[TextSpan] = []

    page_dict = page.get_text("dict")

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()

                if not text:
                    continue

                x0, _, x1, y0 = span["bbox"]

                spans.append(
                    TextSpan(
                        text=text,
                        x=x0,
                        y=y0,
                        width=x1 - x0,
                    )
                )

    return normalize_spans(
        spans,
        y_tolerance=y_tolerance,
    )


def normalize_pdf_page_detailed(
    page,
    y_tolerance: float = 2.0,
) -> list[NormalizedLine]:
    """
    Versão detalhada da normalização de uma página PDF.

    Preserva a geometria dos spans para as próximas etapas.
    """

    spans: list[TextSpan] = []

    page_dict = page.get_text("dict")

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()

                if not text:
                    continue

                x0, _, x1, y0 = span["bbox"]

                spans.append(
                    TextSpan(
                        text=text,
                        x=x0,
                        y=y0,
                        width=x1 - x0,
                    )
                )

    return normalize_spans_detailed(
        spans,
        y_tolerance=y_tolerance,
    )