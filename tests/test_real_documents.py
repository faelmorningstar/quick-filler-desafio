from app.transcription import parse_document, parse_payroll, parse_timecard


def test_payroll_03_page_1_matches_minimum_visual_reference():
    page = parse_payroll("payroll-03.pdf")["pages"][0]
    assert (page["year"], page["month"]) == ("2019", "10")
    fields = {item["code"]: item for item in page["fields"]}
    assert fields["0105"] == {"code": "0105", "label": "Dias Trabalhados", "reference": "30,00", "value": "1.678,61"}
    assert fields["2007"]["value"] == "76,30"
    assert fields["/314"]["value"] == "177,03"
    bases = {(item["label"], item["value"]) for item in page["bases"]}
    assert ("Total Proventos", "1.967,07") in bases
    assert ("Total Descontos", "859,46") in bases
    assert ("Valor Líquido", "1.107,61") in bases
    assert ("Base INSS", "1.967,07") in bases
    assert ("Base IRRF", "1.790,04") in bases
    assert ("Base FGTS", "1.967,07") in bases


def test_native_timecard_preserves_pages_and_produces_days():
    result = parse_timecard("time-card-01.pdf")
    assert [page["page"] for page in result["pages"]] == [1, 2, 3, 4, 5]
    assert all(page["days"] for page in result["pages"])


def test_payroll_02_preserves_sections_and_text_reference():
    page = parse_payroll("payroll-02.pdf")["pages"][0]
    assert [section["payroll_type"] for section in page["sections"]] == ["MÊS", "ACERTO"]
    acerto = page["sections"][1]
    field = next(item for item in acerto["fields"] if item["code"] == "058")
    assert field == {
        "code": "058",
        "label": "HORA EXTRA-BCO HORAS-CONV",
        "reference": "JULHO/18",
        "value": "-12,89",
    }
    summaries = {(item["label"], item["value"]) for item in acerto["bases"]}
    assert ("Provisão FGTS", "-1,04") in summaries
    assert ("Margem (70%)", "0,00") in summaries
    assert ("Proventos Líquidos", "-76,37") in summaries
    mes_summaries = {
        (item["label"], item["value"]) for item in page["sections"][0]["bases"]
    }
    assert ("Remuneração Função Vl. Ref.", "5.017,04") in mes_summaries


def test_public_payroll_output_matches_literal_contract():
    result = parse_document("payroll-03.pdf", "holerite")
    page = result["pages"][0]
    assert set(page) == {"page", "year", "month", "fields", "bases"}
    assert set(page["fields"][0]) == {"code", "label", "reference", "value"}
