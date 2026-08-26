from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pymupdf


MONEY_RE = re.compile(r"^-?[\d?.]+,[\d?]{2}$")
MONEY_TEXT_RE = r"-?[\d?.]+,[\d?]{2}"
TIME_RE = re.compile(r"(?<!\d)([0-2?]?\d[:\-][0-5?]\d)(?!\d)")
FULL_DATE_RE = re.compile(r"\b([0-3?]\d/[01?]\d/(?:19|20|\?\?)\d{2})\b")
CODE_RE = re.compile(r"^(?:[A-Za-z]?/)?[A-Za-z]?\d{2,6}$")


@dataclass(frozen=True)
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float = 100.0


def _uncertain(text: str, confidence: float) -> str:
    if confidence >= 55:
        return text
    return "".join("?" if char.isalnum() else char for char in text)


def _native_words(page: pymupdf.Page) -> list[Word]:
    return [
        Word(str(text), float(x0), float(y0), float(x1), float(y1))
        for x0, y0, x1, y1, text, *_ in page.get_text("words", sort=True)
        if str(text).strip()
    ]


def _ocr_words(page: pymupdf.Page) -> list[Word]:
    """Executa Tesseract e devolve palavras nas coordenadas do PDF."""
    scale = 250 / 72
    pix = page.get_pixmap(dpi=250, colorspace=pymupdf.csRGB, alpha=False)
    with tempfile.TemporaryDirectory(prefix="quick-filler-ocr-") as directory:
        image_path = Path(directory) / "page.png"
        pix.save(image_path)
        result = None
        for languages in ("por+eng", "eng"):
            command = ["tesseract", str(image_path), "stdout", "-l", languages,
                       "--psm", "6", "tsv"]
            try:
                result = subprocess.run(
                    command, capture_output=True, text=True, timeout=90, check=True
                )
                break
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
        if result is None:
            return []

    words: list[Word] = []
    for line in result.stdout.splitlines()[1:]:
        columns = line.split("\t", 11)
        if len(columns) != 12 or not columns[11].strip():
            continue
        try:
            left, top, width, height = map(float, columns[6:10])
            confidence = float(columns[10])
        except ValueError:
            continue
        if confidence < 0:
            continue
        text = _uncertain(columns[11].strip(), confidence)
        words.append(
            Word(text, left / scale, top / scale,
                 (left + width) / scale, (top + height) / scale, confidence)
        )
    return words


def extract_page(page: pymupdf.Page) -> tuple[list[Word], str]:
    """Usa texto nativo quando há cobertura útil; caso contrário usa OCR."""
    native_text = page.get_text("text").strip()
    native = _native_words(page)
    # payroll-04 tem apenas o carimbo judicial: presença não significa cobertura.
    useful_native = len(native_text) >= 150 and len(native) >= 20
    if useful_native:
        return native, "native"
    ocr = _ocr_words(page)
    return (ocr, "ocr") if ocr else (native, "native-insufficient")


def group_rows(words: list[Word], tolerance: float = 3.2) -> list[list[Word]]:
    rows: list[list[Word]] = []
    for word in sorted(words, key=lambda item: (item.y0, item.x0)):
        center = (word.y0 + word.y1) / 2
        target = None
        for row in reversed(rows[-5:]):
            row_center = sum((w.y0 + w.y1) / 2 for w in row) / len(row)
            if abs(center - row_center) <= tolerance:
                target = row
                break
        if target is None:
            rows.append([word])
        else:
            target.append(word)
    for row in rows:
        row.sort(key=lambda item: item.x0)
    return rows


def row_text(row: list[Word]) -> str:
    return " ".join(word.text for word in row).strip()


def _competence(rows: list[list[Word]]) -> tuple[str, str]:
    labelled = re.compile(
        r"(?:per[ií]odo|m[eê]s/ano|refer[eê]ncia|compet[eê]ncia).{0,25}?"
        r"(0?[1-9]|1[0-2])\s*[/.-]\s*((?:19|20)\d{2})",
        re.IGNORECASE,
    )

    named_month = re.compile(
        r"\b("
        r"janeiro|fevereiro|mar[cç]o|abril|maio|junho|"
        r"julho|agosto|setembro|outubro|novembro|dezembro"
        r")\s*/\s*((?:19|20)\d{2})",
        re.IGNORECASE,
    )

    months = {
        "janeiro": "01",
        "fevereiro": "02",
        "março": "03",
        "marco": "03",
        "abril": "04",
        "maio": "05",
        "junho": "06",
        "julho": "07",
        "agosto": "08",
        "setembro": "09",
        "outubro": "10",
        "novembro": "11",
        "dezembro": "12",
    }

    for row in rows:
        text = row_text(row)

        match = labelled.search(text)
        if match:
            return match.group(2), f"{int(match.group(1)):02d}"

        match = named_month.search(text)
        if match:
            month_name = match.group(1).lower().replace("ç", "c")
            return match.group(2), months[month_name]

    return "", ""


def _money_words(row: list[Word]) -> list[Word]:
    return [word for word in row if MONEY_RE.match(word.text)]


def _parse_code_table(rows: list[list[Word]], width: float) -> tuple[list[dict], list[dict]]:
    fields: list[dict] = []
    bases: list[dict] = []
    header_y = None
    total_y = None
    for row in rows:
        normalized = row_text(row).lower()
        if "descri" in normalized and ("provento" in normalized or "valor" in normalized):
            header_y = min(word.y0 for word in row)
            break
    for row in rows:
        text = row_text(row)
        normalized = text.lower()
        if normalized.startswith("total") and _money_words(row):
            total_y = min(word.y0 for word in row)
            monies = _money_words(row)
            if monies:
                bases.append({"label": "Total Proventos", "value": monies[0].text})
            if len(monies) > 1:
                bases.append({"label": "Total Descontos", "value": monies[-1].text})
        if normalized.startswith(("líquido", "líqüido", "liquido")) and _money_words(row):
            bases.append({"label": "Valor Líquido", "value": _money_words(row)[-1].text})
        base_labels = (
            ("base i.n.s.s", "Base INSS"), ("base inss", "Base INSS"),
            ("base i.r.r.f", "Base IRRF"), ("base irrf", "Base IRRF"),
            ("base fgts", "Base FGTS"), ("f.g.t.s. do mês", "FGTS"),
        )
        for marker, label in base_labels:
            if marker in normalized and _money_words(row):
                # Uma linha pode trazer bases à esquerda e à direita.
                if marker.startswith("base i"):
                    candidates = [w for w in _money_words(row) if width * 0.18 < w.x0 < width * 0.45]
                else:
                    candidates = [w for w in _money_words(row) if w.x0 > width * 0.45]
                if candidates:
                    bases.append({"label": label, "value": candidates[-1].text})

    if header_y is None:
        return fields, _dedupe_bases(bases)
    end_y = total_y if total_y is not None else 650
    for row in rows:
        y = min(word.y0 for word in row)
        if y <= header_y + 4 or y >= end_y:
            continue
        code_word = next((word for word in row if CODE_RE.match(word.text)), None)
        monies = _money_words(row)
        if code_word is None or not monies:
            continue
        label_words = [
            word for word in row
            if word.x0 > code_word.x1 and word.x0 < width * 0.45
            and not MONEY_RE.match(word.text)
        ]
        label = " ".join(word.text for word in label_words).strip(" :-")
        if not label:
            continue
        reference_candidates = [w for w in monies if width * 0.43 <= w.x0 < width * 0.60]
        value_candidates = [w for w in monies if w.x0 >= width * 0.60]
        fields.append({
            "code": code_word.text,
            "label": label,
            "reference": reference_candidates[-1].text if reference_candidates else "",
            "value": value_candidates[-1].text if value_candidates else monies[-1].text,
        })
    return fields, _dedupe_bases(bases)


SUMMARY_LABELS = (
    "Remuneração Função Vl. Ref.",
    "Proventos Retidos",
    "Proventos Bruto",
    "Adiantamento 13o.",
    "Provisão FGTS",
    "Margem (30%)",
    "Margem (70%)",
    "Consignação",
    "Proventos Líquidos",
)


def _summary_items(row: list[Word]) -> list[dict]:
    """Extrai cada par rótulo/valor sem juntar colunas vizinhas."""
    text = row_text(row)
    items: list[dict] = []
    for label in SUMMARY_LABELS:
        pattern = re.escape(label)
        match = re.search(
            rf"{pattern}\s*:\s*({MONEY_TEXT_RE})",
            text,
            re.IGNORECASE,
        )
        if match:
            items.append({"label": label, "value": match.group(1)})
    return items

def _parse_receipt_payroll(
    rows: list[list[Word]],
    width: float,
) -> tuple[list[dict], list[dict]]:
    """Extrai campos e totais do layout Recibo de Pagamento via OCR."""

    fields: list[dict] = []
    bases: list[dict] = []
    seen_fields: set[tuple[str, str]] = set()

    for row in rows:
        text = row_text(row).lower()
        values = _money_words(row)

        if "otal de proventos" in text and values:
            bases.append(
                {
                    "label": "Total Proventos",
                    "value": values[0].text,
                }
            )

        if "otal de descontos" in text and values:
            bases.append(
                {
                    "label": "Total Descontos",
                    "value": values[-1].text,
                }
            )

        if "liquido a receber" in text and values:
            bases.append(
                {
                    "label": "Valor Líquido",
                    "value": values[0].text,
                }
            )

        left_words = [
            word for word in row
            if word.x0 < width * 0.45
        ]
        right_words = [
            word for word in row
            if word.x0 >= width * 0.45
        ]

        for column_words in (left_words, right_words):
            column_values = _money_words(column_words)

            if len(column_values) != 1:
                continue

            value = column_values[0].text
            label_words = [
                word.text for word in column_words
                if not MONEY_RE.match(word.text)
            ]
            label = " ".join(label_words).strip(" :-|")

            blocked_labels = (
                "descrição",
                "qtde",
                "valor",
                "otal de",
                "liquido",
            )

            if not label or any(
                blocked in label.lower()
                for blocked in blocked_labels
            ):
                continue

            related_index = next(
                (
                    index
                    for index, existing in enumerate(fields)
                    if existing["value"] == value
                    and (
                        label == existing["label"][1:]
                        or existing["label"] == label[1:]
                    )
                ),
                None,
            )

            if related_index is not None:
                existing = fields[related_index]

                if len(label) < len(existing["label"]):
                    old_key = (
                        existing["label"],
                        existing["value"],
                    )
                    seen_fields.discard(old_key)

                    fields[related_index] = {
                        "code": "",
                        "label": label,
                        "reference": "",
                        "value": value,
                    }
                    seen_fields.add((label, value))

                continue

            key = (label, value)

            if key in seen_fields:
                continue

            fields.append(
                {
                    "code": "",
                    "label": label,
                    "reference": "",
                    "value": value,
                }
            )
            seen_fields.add(key)

    return fields, _dedupe_bases(bases)

def _parse_generic_section(rows: list[list[Word]], width: float) -> tuple[list[dict], list[dict]]:
    """Lê uma tabela simples preservando inclusive referências textuais."""
    fields: list[dict] = []
    bases: list[dict] = []
    header_y: float | None = None
    for row in rows:
        normalized = row_text(row).lower()
        if "verba" in normalized and "nome" in normalized and "valor" in normalized:
            header_y = min(word.y0 for word in row)
            break

    for row in rows:
        bases.extend(_summary_items(row))
        if header_y is None or min(word.y0 for word in row) <= header_y + 3:
            continue
        code_word = next(
            (word for word in row if CODE_RE.match(word.text) and word.x0 < width * .2),
            None,
        )
        if code_word:
            label_words = [
                word for word in row
                if code_word.x1 < word.x0 < width * .44
                and not MONEY_RE.match(word.text)
            ]
            label = " ".join(w.text for w in label_words).strip(" :-")
            reference_words = [
                word for word in row if width * .44 <= word.x0 < width * .70
            ]
            value_candidates = [
                word for word in row
                if word.x0 >= width * .68 and MONEY_RE.match(word.text)
            ]
            if label and value_candidates:
                fields.append({
                    "code": code_word.text,
                    "label": label,
                    "reference": " ".join(w.text for w in reference_words).strip(),
                    "value": value_candidates[-1].text,
                })
    return fields, _dedupe_bases(bases)


def _parse_generic_payroll(
    rows: list[list[Word]], width: float
) -> tuple[list[dict], list[dict], list[dict]]:
    """Separa demonstrativos MÊS/ACERTO e mantém uma visão agregada compatível."""
    starts: list[tuple[int, str]] = []
    marker = re.compile(r"folha de pagamento\s*:\s*(m[eê]s|acerto)", re.IGNORECASE)
    for index, row in enumerate(rows):
        match = marker.search(row_text(row))
        if match:
            kind = "MÊS" if match.group(1).lower() != "acerto" else "ACERTO"
            starts.append((index, kind))

    sections: list[dict] = []
    if starts:
        for position, (start, kind) in enumerate(starts):
            end = starts[position + 1][0] if position + 1 < len(starts) else len(rows)
            fields, bases = _parse_generic_section(rows[start:end], width)
            sections.append({"payroll_type": kind, "fields": fields, "bases": bases})
    else:
        fields, bases = _parse_generic_section(rows, width)
        sections.append({"payroll_type": "MENSAL", "fields": fields, "bases": bases})

    all_fields = [field for section in sections for field in section["fields"]]
    all_bases = [base for section in sections for base in section["bases"]]
    return all_fields, all_bases, sections


def _dedupe_bases(items: list[dict]) -> list[dict]:
    result: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item["label"], item["value"])
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result


def parse_payroll(path: str | Path) -> dict:
    pages: list[dict] = []
    doc = pymupdf.open(path)

    try:
        is_financial_statement = bool(doc) and "fichafinanceira" in re.sub(
            r"\s+", "", doc[0].get_text("text").lower()
        )

        for number, page in enumerate(doc, 1):
            words, _source = extract_page(page)
            rows = group_rows(words)
            year, month = _competence(rows)
            text = " ".join(row_text(row).lower() for row in rows[:30])

            if (
                is_financial_statement
                or "fichafinanceira" in text
                or "ficha financeira" in text
            ):
                fields, bases, sections = [], [], []
                year, month = "", ""

            elif (
                "demonstrativo" in text
                or any("cod." in row_text(row).lower() for row in rows)
            ):
                fields, bases = _parse_code_table(rows, page.rect.width)
                sections = [
                    {
                        "payroll_type": "MENSAL",
                        "fields": fields,
                        "bases": bases,
                    }
                ]

            elif "recibo de pagamento" in text:
                fields, bases = _parse_receipt_payroll(rows, page.rect.width)
                sections = [
                    {
                        "payroll_type": "MENSAL",
                        "fields": fields,
                        "bases": bases,
                    }
                ]

            else:
                fields, bases, sections = _parse_generic_payroll(
                    rows,
                    page.rect.width,
                )

                if not year and not month and len(fields) < 3:
                    fields, bases, sections = [], [], []

            pages.append(
                {
                    "page": number,
                    "year": year,
                    "month": month,
                    "fields": fields,
                    "bases": bases,
                    "sections": sections,
                }
            )

    finally:
        doc.close()

    return {"pages": pages}


def _valid_time(value: str) -> bool:
    if "?" in value:
        return True
    try:
        hour, minute = map(int, value.replace("-", ":").split(":"))
    except ValueError:
        return False
    return 0 <= hour <= 23 and 0 <= minute <= 59


def _punches(times: list[str]) -> list[dict]:
    result = []
    for index, raw in enumerate(times):
        normalized = raw.replace("-", ":")
        if not _valid_time(normalized):
            normalized = "??:??"
        result.append({"kind": "IN" if index % 2 == 0 else "OUT",
                       "time_raw": raw, "time_hhmm": normalized})
    return result

def _order_time_words(
    time_words: list[tuple[float, str]],
    first_interval_x: float | None,
) -> list[str]:
    """Ordena horários conforme o layout identificado no cabeçalho."""

    ordered = sorted(time_words, key=lambda item: item[0])

    if first_interval_x is None:
        return [value for _, value in ordered]

    main_column_times = [
        value for x0, value in ordered
        if x0 < first_interval_x
    ]
    interval_times = [
        value for x0, value in ordered
        if x0 >= first_interval_x
    ]

    if len(main_column_times) >= 2:
        return [
            main_column_times[0],
            *interval_times,
            *main_column_times[1:],
        ]

    return [value for _, value in ordered]

def parse_timecard(path: str | Path) -> dict:
    pages: list[dict] = []
    doc = pymupdf.open(path)
    try:
        for number, page in enumerate(doc, 1):
            words, _source = extract_page(page)
            rows = group_rows(words, tolerance=4.0)
            header_words = [w for row in rows for w in row if w.y0 < page.rect.height * 0.32]
            starts = [w.x0 for w in header_words if w.text.lower().strip(".:/") in {"entrada", "ent1", "manhã", "manha"}]
            data_left = min(starts) - 20 if starts else page.rect.width * 0.12
            stops = [
                w.x0 for w in header_words
                if w.x0 > data_left and any(marker in w.text.lower() for marker in ("ocorr", "qtde", "h.ext", "atraso"))
            ]
            data_right = min(stops) if stops else page.rect.width * 0.82
            interval_starts = [
                word.x0
                for word in header_words
                if "intervalo" in word.text.lower()
            ]
            first_interval_x = (
                (min(starts) + min(interval_starts)) / 2
                if starts and interval_starts
                else None
)
            days: list[dict] = []
            current: dict | None = None
            current_y: float | None = None
            for row in rows:
                text = row_text(row)
                full = FULL_DATE_RE.search(text)
                day_week = re.match(r"^\s*(\d{1,2})\s*(?:-|\s)\s*(?:DOM|SEG|TER|QUA|QUI|SEX|SAB)\b", text, re.I)
                has_weekday = bool(re.search(r"\b(?:DOM|SEG|TER|QUA|QUI|SEX|SAB)\b", text, re.I))
                date_raw = full.group(1) if full and has_weekday else (day_week.group(1) if day_week else None)
                row_y = min(word.y0 for word in row)

                time_words: list[tuple[float, str]] = []
                for word in row:
                    if not (data_left <= word.x0 <= data_right):
                        continue
                    for match in TIME_RE.finditer(word.text):
                        time_words.append((word.x0, match.group(1)))

                times = _order_time_words(time_words, first_interval_x)
                if date_raw is not None:
                    current = {"date_raw": date_raw, "punches": _punches(times)}
                    days.append(current)
                    current_y = row_y
                elif current is not None and current_y is not None and times and row_y - current_y <= 16:
                    start = len(current["punches"])
                    for offset, punch in enumerate(_punches(times)):
                        punch["kind"] = "IN" if (start + offset) % 2 == 0 else "OUT"
                        current["punches"].append(punch)
                    current_y = row_y
            pages.append({"page": number, "days": days})
    finally:
        doc.close()
    return {"pages": pages}


def parse_document(path: str | Path, document_type: str) -> dict:
    if document_type == "holerite":
        result = parse_payroll(path)
        # `sections` auxilia layouts complexos internamente, mas o contrato
        # HTTP oficial aceita somente page/year/month/fields/bases.
        for page in result["pages"]:
            page.pop("sections", None)
        return result
    if document_type == "cartao-ponto":
        return parse_timecard(path)
    raise ValueError("tipo deve ser 'holerite' ou 'cartao-ponto'")
