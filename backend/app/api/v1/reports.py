"""Report template and job API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.schemas import (
    AiFillRequest,
    CreateReportJobRequest,
    ReportJobResponse,
    ReportTemplateResponse,
    UpdateReportJobRequest,
)
from app.services.report_service import ReportService

router = APIRouter(tags=["reports"])


# ---------------------------------------------------------------------------
# DI
# ---------------------------------------------------------------------------

from app.api.dependencies import get_report_service  # noqa: E402


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


@router.post("/report-templates", response_model=ReportTemplateResponse, status_code=201)
async def upload_template(
    file: UploadFile,
    service: Annotated[ReportService, Depends(get_report_service)],
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("xlsx", "pptx"):
        raise HTTPException(status_code=400, detail="Only .xlsx and .pptx files are accepted")
    data = await file.read()
    try:
        template = await service.upload_template(file.filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ReportTemplateResponse.model_validate(template)


@router.get("/report-templates", response_model=list[ReportTemplateResponse])
async def list_templates(
    service: Annotated[ReportService, Depends(get_report_service)],
):
    templates = await service.list_templates()
    return [ReportTemplateResponse.model_validate(t) for t in templates]


@router.get("/report-templates/{template_id}", response_model=ReportTemplateResponse)
async def get_template(
    template_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
):
    template = await service.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return ReportTemplateResponse.model_validate(template)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


@router.post("/report-jobs", response_model=ReportJobResponse, status_code=201)
async def create_job(
    body: CreateReportJobRequest,
    service: Annotated[ReportService, Depends(get_report_service)],
):
    try:
        job = await service.create_job(body.template_id, body.name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ReportJobResponse.model_validate(job)


@router.get("/report-jobs", response_model=list[ReportJobResponse])
async def list_jobs(
    service: Annotated[ReportService, Depends(get_report_service)],
):
    jobs = await service.list_jobs()
    return [ReportJobResponse.model_validate(j) for j in jobs]


@router.get("/report-jobs/{job_id}", response_model=ReportJobResponse)
async def get_job(
    job_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
):
    job = await service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return ReportJobResponse.model_validate(job)


@router.patch("/report-jobs/{job_id}", response_model=ReportJobResponse)
async def update_fills(
    job_id: str,
    body: UpdateReportJobRequest,
    service: Annotated[ReportService, Depends(get_report_service)],
):
    try:
        job = await service.update_fills(job_id, body.fills)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return ReportJobResponse.model_validate(job)


@router.post("/report-jobs/{job_id}/generate", response_model=ReportJobResponse)
async def generate_report(
    job_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
):
    try:
        job = await service.generate(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ReportJobResponse.model_validate(job)


@router.post("/report-jobs/{job_id}/ai-fill", response_model=ReportJobResponse)
async def ai_fill(
    job_id: str,
    body: AiFillRequest,
    service: Annotated[ReportService, Depends(get_report_service)],
):
    try:
        job = await service.ai_fill(job_id, body.connectors, body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ReportJobResponse.model_validate(job)


@router.get("/report-jobs/{job_id}/download")
async def download_report(
    job_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
):
    try:
        file_bytes, filename = await service.download(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    media_types = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
