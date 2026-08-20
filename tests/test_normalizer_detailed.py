from backend.app.payroll.normalizer import (
    TextSpan,
    normalize_spans_detailed,
)


def test_detailed_normalizer_preserves_spans():
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
    ]

    result = normalize_spans_detailed(spans)

    assert len(result) == 1

    line = result[0]

    assert line.text == "37 DSR Adicional 28,03"
    assert line.y == 224.4
    assert len(line.spans) == 3


def test_detailed_normalizer_preserves_horizontal_order():
    spans = [
        TextSpan("VALOR", 500.0, 100.0, 30.0),
        TextSpan("CÓDIGO", 30.0, 100.0, 30.0),
        TextSpan("DESCRIÇÃO", 100.0, 100.0, 50.0),
    ]

    result = normalize_spans_detailed(spans)

    assert result[0].text == (
        "CÓDIGO DESCRIÇÃO VALOR"
    )


def test_detailed_normalizer_separates_different_y_positions():
    spans = [
        TextSpan("LINHA 1", 30.0, 100.0, 40.0),
        TextSpan("LINHA 2", 30.0, 120.0, 40.0),
    ]

    result = normalize_spans_detailed(spans)

    assert len(result) == 2
    assert result[0].text == "LINHA 1"
    assert result[1].text == "LINHA 2"