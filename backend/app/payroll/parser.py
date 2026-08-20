from __future__ import annotations

import re
from collections.abc import Sequence

from .schemas import (
    PayrollBase,
    PayrollDocument,
    PayrollExtractedPage,
    PayrollField,
    PayrollPage,
)


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# Valores monetários no formato brasileiro.
#
# Exemplos aceitos:
#   2.389,77
#   155,91
#   0,00
#   -262,87
#
# Também aceita valores contendo "?" para preservar incerteza do OCR:
#   2.3?9,77
#   ?62,87
#
MONEY_PATTERN = re.compile(
    r"(?<![\d?])"
    r"-?"
    r"(?:[\d?]{1,3}(?:\.[\d?]{3})+|[\d?]+)"
    r",[\d?]{2}"
    r"(?![\d?])"
)


# Código típico de verba:
#
#   0010 Salário Base
#   5560 Horas Extras
#
CODE_PATTERN = re.compile(r"^\s*(\d{2,6})\s+(.*)$")


# Competências comuns:
#
#   01/2020
#   2020/01
#   2020-01
#
COMPETENCE_PATTERN = re.compile(
    r"\b("
    r"(?:0[1-9]|1[0-2])[/.-](?:19|20)\d{2}"
    r"|"
    r"(?:19|20)\d{2}[/.-](?:0[1-9]|1[0-2])"
    r")\b"
)


# ---------------------------------------------------------------------------
# Base / total detection
# ---------------------------------------------------------------------------

BASE_LABEL_PREFIXES = (
    "base inss",
    "base ir",
    "base irrf",
    "base fgts",
    "base iss",
    "base previdenciária",
    "base de cálculo",
    "total vencimentos",
    "total proventos",
    "total descontos",
    "total líquido",
    "valor líquido",
    "líquido",
)


# Cabeçalhos que não devem virar verbas.
HEADER_WORDS = {
    "código",
    "codigo",
    "descrição",
    "descricao",
    "referência",
    "referencia",
    "quantidade",
    "qtde",
    "ref",
    "vencimentos",
    "descontos",
    "proventos",
    "valor",
}


class PayrollParser:
    """
    Parser responsável por transformar texto extraído de um holerite
    no contrato PayrollDocument.

    O parser é deliberadamente independente de OCR/PDF.

    Entrada:
        PayrollExtractedPage[]

    Saída:
        PayrollDocument
    """

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------

    def parse(
        self,
        pages: Sequence[PayrollExtractedPage],
    ) -> PayrollDocument:
        """
        Processa todas as páginas preservando a ordem original.

        Uma página vazia continua existindo no resultado.
        """

        parsed_pages: list[PayrollPage] = []

        for page in pages:
            parsed_pages.append(self._parse_page(page))

        return PayrollDocument(pages=parsed_pages)

    # ------------------------------------------------------------------
    # Page
    # ------------------------------------------------------------------

    def _parse_page(
        self,
        page: PayrollExtractedPage,
    ) -> PayrollPage:
        lines = page.lines

        year, month = self._extract_competence(page)

        fields: list[PayrollField] = []
        bases: list[PayrollBase] = []

        # A classificação é feita linha a linha.
        #
        # Não ordenamos nada por data, valor ou label.
        # A ordem da extração é a ordem do documento.
        for line in lines:
            text = line.text.strip()

            if not text:
                continue

            if self._is_header(text):
                continue

            base = self._parse_base(text)

            if base is not None:
                bases.append(base)
                continue

            field = self._parse_field(text)

            if field is not None:
                fields.append(field)

        return PayrollPage(
            page=page.page,
            year=year,
            month=month,
            fields=fields,
            bases=bases,
        )

    # ------------------------------------------------------------------
    # Competence
    # ------------------------------------------------------------------

    def _extract_competence(
        self,
        page: PayrollExtractedPage,
    ) -> tuple[str, str]:
        """
        Extrai ano e mês da competência da página.

        Quando a competência não puder ser identificada com segurança,
        retorna strings vazias.

        Não inventamos competência.
        """

        for line in page.lines:
            match = COMPETENCE_PATTERN.search(line.text)

            if not match:
                continue

            raw = match.group(1)

            parsed = self._parse_competence(raw)

            if parsed is not None:
                return parsed

        return "", ""

    @staticmethod
    def _parse_competence(
        value: str,
    ) -> tuple[str, str] | None:
        """
        Converte uma competência encontrada para:

            (year, month)

        Exemplos:

            01/2020 -> ("2020", "01")
            2020/01 -> ("2020", "01")
        """

        parts = re.split(r"[/.-]", value)

        if len(parts) != 2:
            return None

        first, second = parts

        if len(first) == 4:
            year = first
            month = second
        else:
            month = first
            year = second

        if not year.isdigit() or not month.isdigit():
            return None

        month_number = int(month)

        if not 1 <= month_number <= 12:
            return None

        return year, f"{month_number:02d}"

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    @staticmethod
    def _is_header(text: str) -> bool:
        """
        Detecta cabeçalhos comuns da tabela.

        Evita transformar "Código Descrição Referência Valor"
        em uma verba.
        """

        normalized = " ".join(text.lower().split())

        words = set(normalized.split())

        if not words:
            return True

        return len(words.intersection(HEADER_WORDS)) >= 2

    @staticmethod
    def _is_base_label(label: str) -> bool:
        """
        Decide se uma descrição pertence à seção de bases/totais.

        A comparação é feita pelo início da descrição para evitar
        classificar qualquer verba contendo "inss" como base.
        """

        normalized = " ".join(label.lower().split())

        return normalized.startswith(BASE_LABEL_PREFIXES)

    # ------------------------------------------------------------------
    # Bases
    # ------------------------------------------------------------------

    def _parse_base(
        self,
        text: str,
    ) -> PayrollBase | None:
        """
        Tenta interpretar uma linha como base/total.

        Exemplos:

            Base INSS 2.545,68
            Valor Líquido 2.282,81
            Total Vencimentos 2.545,68
        """

        value_match = self._find_money(text)

        if value_match is None:
            return None

        label = text[: value_match.start()].strip()

        if not label:
            return None

        if not self._is_base_label(label):
            return None

        value = value_match.group(0)

        return PayrollBase(
            label=label,
            value=value,
        )

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------

    def _parse_field(
        self,
        text: str,
    ) -> PayrollField | None:
        """
        Tenta interpretar uma linha como verba da tabela principal.

        Exemplos:

            0010 Salário Base 220,00 2.389,77
            5560 Horas Extras - 50% 8,00 155,91
            0998 INSS 262,87

        O parser trabalha da direita para a esquerda porque os valores
        monetários normalmente aparecem no final da linha.
        """

        money_matches = list(MONEY_PATTERN.finditer(text))

        if not money_matches:
            return None

        value_match = money_matches[-1]

        value = value_match.group(0)

        prefix = text[: value_match.start()].strip()

        reference = ""

        # Se houver um segundo valor antes do valor principal,
        # tratamos como referência/quantidade.
        if len(money_matches) >= 2:
            reference_match = money_matches[-2]

            reference = reference_match.group(0)

            label_end = reference_match.start()

            prefix = text[:label_end].strip()

        code = ""
        label = prefix

        code_match = CODE_PATTERN.match(prefix)

        if code_match:
            code = code_match.group(1)
            label = code_match.group(2).strip()

        if not label:
            return None

        # Uma linha que já foi identificada semanticamente como base
        # jamais deve cair em fields.
        if self._is_base_label(label):
            return None

        return PayrollField(
            code=code,
            label=label,
            reference=reference,
            value=value,
        )

    # ------------------------------------------------------------------
    # Money
    # ------------------------------------------------------------------

    @staticmethod
    def _find_money(text: str) -> re.Match[str] | None:
        matches = list(MONEY_PATTERN.finditer(text))

        if not matches:
            return None

        return matches[-1]