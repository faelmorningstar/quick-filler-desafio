from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence

from app.timecard.parser import DayRecord

from .models import ValidationWarning, WarningSeverity


def validate_timecard_page(
    page_number: int,
    days: Sequence[DayRecord],
) -> list[ValidationWarning]:
    """
    Valida uma página de cartão de ponto.

    Regras:
    - número ímpar de batidas;
    - datas não sequenciais;
    - datas impossíveis.

    A função não altera nenhum dado da transcrição.
    """

    warnings: list[ValidationWarning] = []

    for index, day in enumerate(days):
        row = index

        # -------------------------------------------------------------
        # Batidas ímpares
        # -------------------------------------------------------------

        if len(day.punches) % 2 != 0:
            warnings.append(
                ValidationWarning(
                    code="ODD_PUNCHES",
                    message="O dia possui número ímpar de batidas.",
                    page=page_number,
                    row=row,
                )
            )

        # -------------------------------------------------------------
        # Data
        # -------------------------------------------------------------

        current_date = _parse_date(day.date_raw)

        if current_date is None:
            warnings.append(
                ValidationWarning(
                    code="INVALID_DATE",
                    message=f"Data inválida ou ilegível: {day.date_raw}",
                    page=page_number,
                    row=row,
                )
            )

            # Sem uma data válida, não conseguimos comparar
            # sequencialidade com segurança.
            continue

        # -------------------------------------------------------------
        # Data sequencial
        # -------------------------------------------------------------

        if index == 0:
            continue

        previous_date = _parse_date(days[index - 1].date_raw)

        if previous_date is None:
            continue

        if current_date != previous_date + timedelta(days=1):

            warnings.append(
                ValidationWarning(
                    code="NON_SEQUENTIAL_DATE",
                    message="A data não é sequencial em relação à linha anterior.",
                    page=page_number,
                    row=row,
                    severity=WarningSeverity.WARNING,
                )
            )

    return warnings


def _parse_date(value: str) -> date | None:
    """
    Converte DD/MM/YYYY em date.

    Qualquer valor ilegível ou impossível retorna None.

    Exemplos:
        21/05/2019 -> date(...)
        38/07/2019 -> None
        21/13/2019 -> None
        2?/05/2019 -> None
    """

    parts = value.split("/")

    if len(parts) != 3:
        return None

    day, month, year = parts

    if not (
        day.isdigit()
        and month.isdigit()
        and year.isdigit()
    ):
        return None

    try:
        return date(
            int(year),
            int(month),
            int(day),
        )
    except ValueError:
        return None