import shutil

import pytest

from app.transcription import parse_payroll


pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="Teste de OCR exige Tesseract; execute a suíte completa no Docker.",
)


def test_payroll_04_ocr_extracts_competence_and_totals():
    page = parse_payroll("payroll-04.pdf")["pages"][0]

    assert (page["year"], page["month"]) == ("2019", "09")

    bases = {(item["label"], item["value"]) for item in page["bases"]}

    assert ("Total Proventos", "2.227,04") in bases
    assert ("Total Descontos", "211,43") in bases
    assert ("Valor Líquido", "2.015,61") in bases

    fields = {(item["label"], item["value"]) for item in page["fields"]}

    assert ("SALARIO", "953,36") in fields
    assert ("INSS MES", "200,43") in fields

    assert ("REMUNERACAO VARIAVEL", "1.100,00") in fields
    assert ("IREMUNERACAO VARIAVEL", "1.100,00") not in fields