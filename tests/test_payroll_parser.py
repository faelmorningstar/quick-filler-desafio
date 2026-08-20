from backend.app.payroll.parser import PayrollParser
from backend.app.payroll.schemas import (
    PayrollExtractedLine,
    PayrollExtractedPage,
)


def make_page(
    page: int,
    lines: list[str],
) -> PayrollExtractedPage:
    """
    Cria uma página de entrada para os testes.

    Simula exatamente o formato que o parser receberá
    depois da etapa de extração de texto/OCR.
    """

    return PayrollExtractedPage(
        page=page,
        lines=[
            PayrollExtractedLine(
                text=text,
                order=index,
            )
            for index, text in enumerate(lines)
        ],
    )


def test_parse_competence():
    parser = PayrollParser()

    pages = [
        make_page(
            1,
            [
                "EMPRESA XYZ",
                "COMPETÊNCIA 01/2020",
            ],
        )
    ]

    result = parser.parse(pages)

    assert len(result.pages) == 1
    assert result.pages[0].year == "2020"
    assert result.pages[0].month == "01"


def test_parse_field_with_code_reference_and_value():
    parser = PayrollParser()

    pages = [
        make_page(
            1,
            [
                "CÓDIGO DESCRIÇÃO REFERÊNCIA VALOR",
                "0010 Salário Base 220,00 2.389,77",
            ],
        )
    ]

    result = parser.parse(pages)

    assert len(result.pages[0].fields) == 1

    field = result.pages[0].fields[0]

    assert field.code == "0010"
    assert field.label == "Salário Base"
    assert field.reference == "220,00"
    assert field.value == "2.389,77"


def test_parse_field_without_reference():
    parser = PayrollParser()

    pages = [
        make_page(
            1,
            [
                "0998 INSS 262,87",
            ],
        )
    ]

    result = parser.parse(pages)

    field = result.pages[0].fields[0]

    assert field.code == "0998"
    assert field.label == "INSS"
    assert field.reference == ""
    assert field.value == "262,87"


def test_base_does_not_enter_fields():
    parser = PayrollParser()

    pages = [
        make_page(
            1,
            [
                "0010 Salário Base 220,00 2.389,77",
                "0998 INSS 262,87",
                "Base INSS 2.389,77",
                "Total Vencimentos 2.389,77",
                "Valor Líquido 2.126,90",
            ],
        )
    ]

    result = parser.parse(pages)

    page = result.pages[0]

    assert len(page.fields) == 2
    assert len(page.bases) == 3

    assert page.fields[0].label == "Salário Base"
    assert page.fields[1].label == "INSS"

    assert page.bases[0].label == "Base INSS"
    assert page.bases[1].label == "Total Vencimentos"
    assert page.bases[2].label == "Valor Líquido"


def test_empty_page_is_preserved():
    parser = PayrollParser()

    pages = [
        make_page(1, []),
    ]

    result = parser.parse(pages)

    assert len(result.pages) == 1
    assert result.pages[0].page == 1
    assert result.pages[0].fields == []
    assert result.pages[0].bases == []


def test_page_order_is_preserved():
    parser = PayrollParser()

    pages = [
        make_page(1, ["COMPETÊNCIA 01/2020"]),
        make_page(2, ["COMPETÊNCIA 02/2020"]),
        make_page(3, ["COMPETÊNCIA 03/2020"]),
    ]

    result = parser.parse(pages)

    assert [page.page for page in result.pages] == [1, 2, 3]

    assert [page.month for page in result.pages] == [
        "01",
        "02",
        "03",
    ]


def test_invalid_month_is_not_accepted():
    parser = PayrollParser()

    pages = [
        make_page(
            1,
            [
                "COMPETÊNCIA 13/2020",
            ],
        )
    ]

    result = parser.parse(pages)

    assert result.pages[0].year == ""
    assert result.pages[0].month == ""


def test_money_format_is_preserved_as_string():
    parser = PayrollParser()

    pages = [
        make_page(
            1,
            [
                "0010 Salário Base 220,00 2.3?9,77",
            ],
        )
    ]

    result = parser.parse(pages)

    field = result.pages[0].fields[0]

    assert field.value == "2.3?9,77"
    assert isinstance(field.value, str)