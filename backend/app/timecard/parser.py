from __future__ import annotations

import re
from dataclasses import dataclass


TIME_PATTERN = re.compile(r"\b\d{1,2}[:\-]\d{2}\b")
DATE_PATTERN = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")


@dataclass(frozen=True)
class Punch:
    kind: str
    time_raw: str
    time_hhmm: str


@dataclass(frozen=True)
class DayRecord:
    date_raw: str
    punches: tuple[Punch, ...]


def normalize_time(value: str) -> str:
    return value.replace("-", ":")


def parse_page_text(text: str) -> list[DayRecord]:
    """
    Faz uma primeira interpretação de uma página de cartão de ponto.

    Esta versão assume que datas e horários aparecem em ordem
    no texto extraído. A lógica estrutural será refinada após
    validarmos os PDFs reais.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    records: list[DayRecord] = []
    current_date: str | None = None
    current_times: list[str] = []

    for line in lines:
        date_match = DATE_PATTERN.search(line)

        if date_match:
            if current_date is not None:
                records.append(
                    DayRecord(
                        date_raw=current_date,
                        punches=_build_punches(current_times),
                    )
                )

            current_date = date_match.group(0)
            current_times = []

        for match in TIME_PATTERN.finditer(line):
            current_times.append(match.group(0))

    if current_date is not None:
        records.append(
            DayRecord(
                date_raw=current_date,
                punches=_build_punches(current_times),
            )
        )

    return records


def _build_punches(times: list[str]) -> tuple[Punch, ...]:
    punches: list[Punch] = []

    for index, time_raw in enumerate(times):
        kind = "IN" if index % 2 == 0 else "OUT"

        punches.append(
            Punch(
                kind=kind,
                time_raw=time_raw,
                time_hhmm=normalize_time(time_raw),
            )
        )

    return tuple(punches)