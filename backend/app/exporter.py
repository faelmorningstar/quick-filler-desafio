from __future__ import annotations

import csv
import io
import json
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


HEADER_FILL = PatternFill("solid", fgColor="173772")
WARNING_FILL = PatternFill("solid", fgColor="FFF3CD")


def _rows(value: dict[str, Any], document_type: str) -> tuple[list[str], list[list[str]]]:
    if document_type == "cartao-ponto":
        days = [day for page in value.get("pages", []) for day in page.get("days", [])]
        max_punches = max((len(day.get("punches", [])) for day in days), default=0)
        headers = ["Data"]
        for index in range(max_punches):
            headers.append(("Entrada " if index % 2 == 0 else "Saída ") + str(index // 2 + 1))
        rows = []
        for day in days:
            times = [punch.get("time_hhmm", "") for punch in day.get("punches", [])]
            rows.append([day.get("date_raw", ""), *times, *([""] * (max_punches - len(times)))])
        return headers, rows

    pages = value.get("pages", [])
    labels: list[str] = []
    for page in pages:
        for field in page.get("fields", []):
            label = field.get("label", "")
            if label and label not in labels:
                labels.append(label)
    headers = ["Pág.", "Mês", "Ano", *labels]
    rows = []
    for page in pages:
        by_label = {field.get("label", ""): field.get("value", "") for field in page.get("fields", [])}
        rows.append([str(page.get("page", "")), page.get("month", ""), page.get("year", ""),
                     *[by_label.get(label, "") for label in labels]])
    return headers, rows


def export_json(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


def export_csv(value: dict[str, Any], document_type: str) -> bytes:
    headers, rows = _rows(value, document_type)
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")


def export_xlsx(value: dict[str, Any], document_type: str) -> bytes:
    headers, rows = _rows(value, document_type)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Transcrição"
    sheet.append(headers)
    for cell in sheet[1]:
        cell.fill = HEADER_FILL
        cell.font = Font(color="FFFFFF", bold=True)
    for values in rows:
        sheet.append(values)
        row_number = sheet.max_row
        has_uncertainty = any("?" in str(value) for value in values)
        odd_punches = document_type == "cartao-ponto" and (len([v for v in values[1:] if v]) % 2 == 1)
        if has_uncertainty or odd_punches:
            for cell in sheet[row_number]:
                cell.fill = WARNING_FILL
    sheet.freeze_panes = "A2"
    for column in sheet.columns:
        width = min(max(len(str(cell.value or "")) for cell in column) + 2, 45)
        sheet.column_dimensions[column[0].column_letter].width = width
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()
