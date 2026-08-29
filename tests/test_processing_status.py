from pathlib import Path

import pytest

from app import main


@pytest.mark.parametrize(
    ("document_type", "empty_value"),
    [
        (
            "cartao-ponto",
            {"pages": [{"page": 1, "days": []}]},
        ),
        (
            "holerite",
            {
                "pages": [
                    {
                        "page": 1,
                        "year": "",
                        "month": "",
                        "fields": [],
                        "bases": [],
                    }
                ]
            },
        ),
    ],
)
def test_fully_empty_extraction_ends_with_error(
    monkeypatch,
    tmp_path: Path,
    document_type: str,
    empty_value: dict,
):
    job_id = f"empty-{document_type}"
    pdf_path = tmp_path / "documento.pdf"

    monkeypatch.setitem(
        main.JOBS,
        job_id,
        {
            "id": job_id,
            "tipo": document_type,
            "status": "processando",
            "erro": None,
            "value": None,
            "warnings": [],
            "path": pdf_path,
        },
    )

    monkeypatch.setattr(
        main,
        "parse_document",
        lambda path, tipo: empty_value,
    )

    main._process(job_id, pdf_path, document_type)

    job = main.JOBS[job_id]

    assert job["status"] == "erro"
    assert job["value"] is None
    assert job["warnings"] == []
    assert "nenhum dado" in job["erro"].lower()

def test_pdf_response_is_displayed_inline(
    monkeypatch,
    tmp_path: Path,
):
    job_id = "inline-pdf"
    pdf_path = tmp_path / "documento.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setitem(
        main.JOBS,
        job_id,
        {
            "id": job_id,
            "tipo": "cartao-ponto",
            "status": "concluido",
            "erro": None,
            "value": {"pages": []},
            "warnings": [],
            "path": pdf_path,
        },
    )

    response = main.get_pdf(job_id)

    assert response.media_type == "application/pdf"
    assert response.headers["content-disposition"] == (
        'inline; filename="documento.pdf"'
    )

def test_payroll_warnings_are_exposed_by_api_helper():
    value = {
        "pages": [
            {
                "page": 1,
                "year": "2020",
                "month": "01",
                "fields": [
                    {
                        "code": "0010",
                        "label": "Salário Base",
                        "reference": "220,00",
                        "value": "2.389,77",
                    }
                ],
                "bases": [],
            },
            {
                "page": 2,
                "year": "2020",
                "month": "03",
                "fields": [],
                "bases": [],
            },
        ]
    }

    warnings = main._warnings_for(value, "holerite")
    codes = {warning["code"] for warning in warnings}

    assert codes == {
        "EMPTY_PAGE",
        "NON_SEQUENTIAL_MONTH",
    }
    assert all(warning["page"] == 2 for warning in warnings)