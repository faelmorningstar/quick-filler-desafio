from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PayrollExtractedLine(BaseModel):
    """
    Representa uma linha textual produzida pelo Native Extractor ou OCR.

    O parser de holerite não sabe nem deve saber se a linha veio de
    texto nativo ou de OCR.
    """

    model_config = ConfigDict(extra="forbid")

    text: str
    order: int = Field(ge=0)


class PayrollExtractedPage(BaseModel):
    """
    Representa o conteúdo textual de uma página após a extração.

    A página é preservada mesmo quando não possui texto útil.
    Isso é necessário para representar corretamente páginas vazias.
    """

    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    lines: list[PayrollExtractedLine] = Field(default_factory=list)


class PayrollField(BaseModel):
    """
    Verba pertencente à tabela principal do holerite.

    Exemplo:
        {
            "code": "0010",
            "label": "Salário Base",
            "reference": "220,00",
            "value": "2.389,77"
        }
    """

    model_config = ConfigDict(extra="forbid")

    code: str = ""
    label: str = ""
    reference: str = ""
    value: str = ""


class PayrollBase(BaseModel):
    """
    Base ou total pertencente à seção separada do holerite.

    Exemplo:
        {
            "label": "Base INSS",
            "value": "2.545,68"
        }
    """

    model_config = ConfigDict(extra="forbid")

    label: str = ""
    value: str = ""


class PayrollPage(BaseModel):
    """
    Resultado estruturado de uma página de holerite.

    A ordem das páginas é preservada pelo parser.
    """

    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    year: str = ""
    month: str = ""
    fields: list[PayrollField] = Field(default_factory=list)
    bases: list[PayrollBase] = Field(default_factory=list)


class PayrollDocument(BaseModel):
    """
    Contrato completo de saída para um holerite.
    """

    model_config = ConfigDict(extra="forbid")

    pages: list[PayrollPage] = Field(default_factory=list)