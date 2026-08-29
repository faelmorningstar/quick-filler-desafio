from io import BytesIO

from openpyxl import load_workbook

from app.exporter import export_xlsx


def _sheet_for(value: dict):
    data = export_xlsx(value, "holerite")
    workbook = load_workbook(BytesIO(data))
    return workbook.active


def _page(
    page: int,
    month: str,
    fields: list[dict] | None = None,
) -> dict:
    return {
        "page": page,
        "year": "2020",
        "month": month,
        "fields": fields or [],
        "bases": [],
    }


def _salary(value: str = "2.389,77") -> dict:
    return {
        "code": "0010",
        "label": "Salário Base",
        "reference": "220,00",
        "value": value,
    }


def test_empty_payroll_page_is_yellow():
    value = {
        "pages": [
            _page(1, "01", [_salary()]),
            _page(2, "02"),
        ]
    }

    sheet = _sheet_for(value)

    assert sheet["A3"].fill.fgColor.rgb.endswith("FFF3CD")


def test_non_sequential_month_is_red_and_wins_over_uncertainty():
    value = {
        "pages": [
            _page(1, "01", [_salary()]),
            _page(2, "03", [_salary("2.3?9,77")]),
        ]
    }

    sheet = _sheet_for(value)

    assert sheet["A3"].fill.fgColor.rgb.endswith("F8D7DA")
    assert sheet["A3"].border.left.color.rgb.endswith("DC3545")