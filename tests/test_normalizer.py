from backend.app.payroll.normalizer import (
    TextSpan,
    normalize_spans,
)


def test_normalize_spans_orders_text_from_left_to_right():
    spans = [
        TextSpan(
            text="28,03",
            x=193.1,
            y=224.4,
            width=18.0,
        ),
        TextSpan(
            text="37",
            x=34.1,
            y=224.4,
            width=8.1,
        ),
        TextSpan(
            text="DSR Adicional",
            x=45.1,
            y=224.4,
            width=44.9,
        ),
        TextSpan(
            text="19,23",
            x=145.0,
            y=224.4,
            width=18.0,
        ),
    ]

    result = normalize_spans(spans)

    assert result == [
        "37 DSR Adicional 19,23 28,03"
    ]


def test_normalize_spans_creates_separate_lines():
    spans = [
        TextSpan(
            text="37",
            x=34.1,
            y=224.4,
            width=8.1,
        ),
        TextSpan(
            text="DSR Adicional",
            x=45.1,
            y=224.4,
            width=44.9,
        ),
        TextSpan(
            text="491",
            x=228.0,
            y=233.8,
            width=12.1,
        ),
        TextSpan(
            text="Seguro Vida Fun",
            x=243.1,
            y=233.8,
            width=53.1,
        ),
    ]

    result = normalize_spans(spans)

    assert result == [
        "37 DSR Adicional",
        "491 Seguro Vida Fun",
    ]


def test_normalize_spans_ignores_empty_text():
    spans = [
        TextSpan(
            text="",
            x=10.0,
            y=100.0,
            width=10.0,
        ),
        TextSpan(
            text="Salário",
            x=20.0,
            y=100.0,
            width=30.0,
        ),
        TextSpan(
            text="   ",
            x=60.0,
            y=100.0,
            width=10.0,
        ),
    ]

    result = normalize_spans(spans)

    assert result == [
        "Salário"
    ]

def normalize_pdf_page(
    page,
    y_tolerance: float = 2.0,
) -> list[str]:
    """
    Extrai spans diretamente de uma página PyMuPDF
    e os normaliza em linhas de texto.

    A função não interpreta o conteúdo.
    Ela apenas reconstrói a ordem espacial do texto.
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