from __future__ import annotations

from typing import Sequence

from app.payroll.schemas import PayrollPage

from .models import ValidationWarning


def validate_payroll_pages(
    pages: Sequence[PayrollPage],
) -> list[ValidationWarning]:
    """
    Valida uma sequência de páginas de holerite.

    Regras:
    - página vazia;
    - mês não sequencial.

    A competência desconhecida não quebra a cadeia:
    comparamos a próxima competência legível com a última
    competência legível encontrada.
    """

    warnings: list[ValidationWarning] = []

    previous_competence: tuple[int, int] | None = None

    for row, page in enumerate(pages):

        # -------------------------------------------------------------
        # Página vazia
        # -------------------------------------------------------------

        if not page.fields and not page.bases:
            warnings.append(
                ValidationWarning(
                    code="EMPTY_PAGE",
                    message="Nenhum dado foi extraído desta página.",
                    page=page.page,
                    row=row,
                )
            )

        # -------------------------------------------------------------
        # Competência
        # -------------------------------------------------------------

        competence = _parse_competence(
            page.year,
            page.month,
        )

        if competence is None:
            # Competência ilegível não quebra a cadeia.
            continue

        # -------------------------------------------------------------
        # Mês sequencial
        # -------------------------------------------------------------

        if previous_competence is not None:
            expected = _next_month(previous_competence)

            if competence != expected:
                warnings.append(
                    ValidationWarning(
                        code="NON_SEQUENTIAL_MONTH",
                        message=(
                            "A competência não é sequencial em relação "
                            "à última competência legível."
                        ),
                        page=page.page,
                        row=row,
                    )
                )

        previous_competence = competence

    return warnings


def _parse_competence(
    year: str,
    month: str,
) -> tuple[int, int] | None:
    """
    Valida ano/mês.

    Retorna:
        (ano, mês)

    ou None quando a competência não pode ser interpretada.
    """

    if not year.isdigit() or not month.isdigit():
        return None

    year_number = int(year)
    month_number = int(month)

    if not 1 <= month_number <= 12:
        return None

    if not 1900 <= year_number <= 2100:
        return None

    return year_number, month_number


def _next_month(
    competence: tuple[int, int],
) -> tuple[int, int]:
    """
    Retorna a competência imediatamente seguinte.

    Dezembro -> janeiro do ano seguinte.
    """

    year, month = competence

    if month == 12:
        return year + 1, 1

    return year, month + 1