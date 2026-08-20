from app.payroll.schemas import PayrollBase, PayrollField, PayrollPage
from app.timecard.parser import DayRecord, Punch
from app.validation.payroll import validate_payroll_pages
from app.validation.timecard import validate_timecard_page


# ============================================================
# Helpers
# ============================================================


def make_punch(time: str, kind: str = "IN") -> Punch:
    return Punch(
        kind=kind,
        time_raw=time,
        time_hhmm=time,
    )


def make_day(
    date_raw: str,
    times: list[str],
) -> DayRecord:
    punches = tuple(
        make_punch(
            time=time,
            kind="IN" if index % 2 == 0 else "OUT",
        )
        for index, time in enumerate(times)
    )

    return DayRecord(
        date_raw=date_raw,
        punches=punches,
    )


def make_payroll_page(
    page: int,
    year: str,
    month: str,
    fields: list[PayrollField] | None = None,
    bases: list[PayrollBase] | None = None,
) -> PayrollPage:
    return PayrollPage(
        page=page,
        year=year,
        month=month,
        fields=fields or [],
        bases=bases or [],
    )


# ============================================================
# Cartão de ponto
# ============================================================


def test_timecard_valid_sequential_dates_produce_no_warnings():
    days = [
        make_day("21/05/2019", ["08:00", "12:00"]),
        make_day("22/05/2019", ["08:00", "12:00"]),
        make_day("23/05/2019", ["08:00", "12:00"]),
    ]

    warnings = validate_timecard_page(
        page_number=1,
        days=days,
    )

    assert warnings == []


def test_timecard_odd_number_of_punches_generates_warning():
    days = [
        make_day(
            "21/05/2019",
            ["08:00", "12:00", "13:00"],
        )
    ]

    warnings = validate_timecard_page(
        page_number=1,
        days=days,
    )

    assert len(warnings) == 1
    assert warnings[0].code == "ODD_PUNCHES"
    assert warnings[0].page == 1
    assert warnings[0].row == 0


def test_timecard_non_sequential_date_generates_warning():
    days = [
        make_day("21/05/2019", ["08:00", "12:00"]),
        make_day("23/05/2019", ["08:00", "12:00"]),
    ]

    warnings = validate_timecard_page(
        page_number=1,
        days=days,
    )

    assert len(warnings) == 1
    assert warnings[0].code == "NON_SEQUENTIAL_DATE"
    assert warnings[0].row == 1


def test_timecard_december_to_january_is_sequential():
    days = [
        make_day("31/12/2019", ["08:00", "12:00"]),
        make_day("01/01/2020", ["08:00", "12:00"]),
    ]

    warnings = validate_timecard_page(
        page_number=1,
        days=days,
    )

    assert warnings == []


def test_timecard_invalid_date_generates_warning():
    days = [
        make_day("38/05/2019", ["08:00", "12:00"]),
    ]

    warnings = validate_timecard_page(
        page_number=1,
        days=days,
    )

    assert len(warnings) == 1
    assert warnings[0].code == "INVALID_DATE"


def test_timecard_uncertain_date_is_not_treated_as_valid_date():
    days = [
        make_day("2?/05/2019", ["08:00", "12:00"]),
    ]

    warnings = validate_timecard_page(
        page_number=1,
        days=days,
    )

    assert len(warnings) == 1
    assert warnings[0].code == "INVALID_DATE"


# ============================================================
# Holerite
# ============================================================


def test_payroll_sequential_months_produce_no_warnings():
    pages = [
        make_payroll_page(1, "2020", "01"),
        make_payroll_page(
            2,
            "2020",
            "02",
            fields=[
                PayrollField(
                    code="0010",
                    label="Salário Base",
                    reference="220,00",
                    value="2.389,77",
                )
            ],
        ),
        make_payroll_page(
            3,
            "2020",
            "03",
            bases=[
                PayrollBase(
                    label="Base INSS",
                    value="2.389,77",
                )
            ],
        ),
    ]

    warnings = validate_payroll_pages(pages)

    # As páginas 1, 2 e 3 possuem competência válida.
    # A página 1 está vazia de dados, portanto gera EMPTY_PAGE.
    assert len(warnings) == 1
    assert warnings[0].code == "EMPTY_PAGE"


def test_payroll_non_sequential_month_generates_warning():
    pages = [
        make_payroll_page(
            1,
            "2020",
            "01",
            fields=[
                PayrollField(
                    code="0010",
                    label="Salário Base",
                    reference="220,00",
                    value="2.389,77",
                )
            ],
        ),
        make_payroll_page(
            2,
            "2020",
            "03",
            fields=[
                PayrollField(
                    code="0010",
                    label="Salário Base",
                    reference="220,00",
                    value="2.389,77",
                )
            ],
        ),
    ]

    warnings = validate_payroll_pages(pages)

    assert len(warnings) == 1
    assert warnings[0].code == "NON_SEQUENTIAL_MONTH"
    assert warnings[0].page == 2
    assert warnings[0].row == 1


def test_payroll_december_to_january_is_sequential():
    pages = [
        make_payroll_page(
            1,
            "2020",
            "12",
            fields=[
                PayrollField(
                    code="0010",
                    label="Salário Base",
                    reference="220,00",
                    value="2.389,77",
                )
            ],
        ),
        make_payroll_page(
            2,
            "2021",
            "01",
            fields=[
                PayrollField(
                    code="0010",
                    label="Salário Base",
                    reference="220,00",
                    value="2.389,77",
                )
            ],
        ),
    ]

    warnings = validate_payroll_pages(pages)

    assert warnings == []


def test_payroll_empty_page_generates_warning():
    pages = [
        make_payroll_page(
            1,
            "2020",
            "01",
        )
    ]

    warnings = validate_payroll_pages(pages)

    assert len(warnings) == 1
    assert warnings[0].code == "EMPTY_PAGE"
    assert warnings[0].page == 1
    assert warnings[0].row == 0


def test_payroll_unknown_competence_does_not_break_sequence():
    pages = [
        make_payroll_page(
            1,
            "2020",
            "01",
            fields=[
                PayrollField(
                    code="0010",
                    label="Salário Base",
                    reference="220,00",
                    value="2.389,77",
                )
            ],
        ),
        make_payroll_page(
            2,
            "",
            "",
            fields=[
                PayrollField(
                    code="0010",
                    label="Salário Base",
                    reference="220,00",
                    value="2.389,77",
                )
            ],
        ),
        make_payroll_page(
            3,
            "2020",
            "03",
            fields=[
                PayrollField(
                    code="0010",
                    label="Salário Base",
                    reference="220,00",
                    value="2.389,77",
                )
            ],
        ),
    ]

    warnings = validate_payroll_pages(pages)

    assert len(warnings) == 1
    assert warnings[0].code == "NON_SEQUENTIAL_MONTH"
    assert warnings[0].page == 3