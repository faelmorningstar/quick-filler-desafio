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