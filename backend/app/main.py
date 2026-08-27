from __future__ import annotations

import json
import secrets
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel

from .exporter import export_csv, export_json, export_xlsx
from .transcription import parse_document
from .validation.timecard import validate_timecard_transcription


MAX_UPLOAD_BYTES = 15 * 1024 * 1024
STORE = Path(tempfile.gettempdir()) / "quick-filler"
STORE.mkdir(parents=True, exist_ok=True)
JOBS: dict[str, dict[str, Any]] = {}
LOCK = threading.Lock()

app = FastAPI(title="Quick Filler", version="1.0.0")


class Correction(BaseModel):
    value: dict[str, Any]

def _warnings_for(
    value: dict[str, Any],
    document_type: str,
) -> list[dict[str, Any]]:
    if document_type != "cartao-ponto":
        return []

    warnings = validate_timecard_transcription(value)

    return [
        {
            "code": warning.code,
            "message": warning.message,
            "page": warning.page,
            "row": warning.row,
            "severity": warning.severity.value,
        }
        for warning in warnings
    ]

def _has_extracted_data(
    value: dict[str, Any],
    document_type: str,
) -> bool:
    pages = value.get("pages")

    if not isinstance(pages, list):
        return False

    if document_type == "cartao-ponto":
        return any(
            isinstance(page, dict) and bool(page.get("days"))
            for page in pages
        )

    if document_type == "holerite":
        return any(
            isinstance(page, dict)
            and bool(page.get("fields") or page.get("bases"))
            for page in pages
        )

    return False

def _process(
    job_id: str,
    path: Path,
    document_type: str,
) -> None:
    try:
        value = parse_document(path, document_type)

        if not _has_extracted_data(value, document_type):
            with LOCK:
                JOBS[job_id].update(
                    status="erro",
                    erro=(
                        "Nenhum dado foi extraído do documento. "
                        "Verifique a qualidade do PDF ou do OCR."
                    ),
                    value=None,
                    warnings=[],
                )
            return

        warnings = _warnings_for(value, document_type)

        with LOCK:
            JOBS[job_id].update(
                status="concluido",
                erro=None,
                value=value,
                warnings=warnings,
            )
    except Exception as exc:
        with LOCK:
            JOBS[job_id].update(
                status="erro",
                erro=(
                    "Falha ao processar o PDF: "
                    f"{type(exc).__name__}"
                ),
                value=None,
                warnings=[],
            )

@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    static = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(static.read_text(encoding="utf-8"))


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/transcricoes", status_code=202)
async def create_transcription(
    background_tasks: BackgroundTasks,
    arquivo: UploadFile = File(...),
    tipo: str = Form(...),
) -> dict[str, str]:
    if tipo not in {"cartao-ponto", "holerite"}:
        raise HTTPException(422, "tipo inválido")

    content = await arquivo.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "PDF excede o limite de 15 MB")

    if not content.startswith(b"%PDF-"):
        raise HTTPException(415, "o arquivo enviado não é um PDF válido")

    job_id = secrets.token_urlsafe(9)
    job_dir = STORE / job_id
    job_dir.mkdir(parents=True, exist_ok=False)

    pdf_path = job_dir / "documento.pdf"
    pdf_path.write_bytes(content)

    with LOCK:
        JOBS[job_id] = {
            "id": job_id,
            "tipo": tipo,
            "status": "processando",
            "erro": None,
            "value": None,
            "warnings": [],
            "path": pdf_path,
        }

    background_tasks.add_task(_process, job_id, pdf_path, tipo)

    return {"id": job_id}

def _job(job_id: str) -> dict[str, Any]:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "transcrição não encontrada")
    return job


@app.get("/api/transcricoes/{job_id}")
def get_transcription(job_id: str) -> dict[str, Any]:
    job = _job(job_id)
    return {
    key: job[key]
    for key in ("id", "tipo", "status", "erro", "value", "warnings")
}


@app.put("/api/transcricoes/{job_id}")
def update_transcription(
    job_id: str,
    correction: Correction,
) -> dict[str, Any]:
    job = _job(job_id)

    if job["status"] != "concluido":
        raise HTTPException(
            409,
            "a transcrição ainda não foi concluída",
        )

    warnings = _warnings_for(
        correction.value,
        job["tipo"],
    )

    with LOCK:
        job["value"] = correction.value
        job["warnings"] = warnings

    return {
        "id": job_id,
        "tipo": job["tipo"],
        "status": "concluido",
        "erro": None,
        "value": job["value"],
        "warnings": job["warnings"],
    }


@app.get("/api/transcricoes/{job_id}/pdf")
def get_pdf(job_id: str) -> FileResponse:
    job = _job(job_id)
    return FileResponse(job["path"], media_type="application/pdf", filename="documento.pdf")


@app.get("/api/transcricoes/{job_id}/planilha")
def download(job_id: str, formato: str = "xlsx") -> Response:
    job = _job(job_id)
    if job["status"] != "concluido":
        raise HTTPException(409, "a transcrição ainda não foi concluída")
    if formato == "xlsx":
        data, media = export_xlsx(job["value"], job["tipo"]), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif formato == "csv":
        data, media = export_csv(job["value"], job["tipo"]), "text/csv; charset=utf-8"
    elif formato == "json":
        data, media = export_json(job["value"]), "application/json"
    else:
        raise HTTPException(422, "formato deve ser xlsx, csv ou json")
    return Response(data, media_type=media, headers={"Content-Disposition": f'attachment; filename="transcricao.{formato}"'})
