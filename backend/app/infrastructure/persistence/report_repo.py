"""Report template and job repositories."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.report import ReportTemplate, ReportJob
from app.infrastructure.persistence.mappers import (
    report_template_entity_to_model, report_template_model_to_entity,
    report_job_entity_to_model, report_job_model_to_entity,
)
from app.infrastructure.persistence.models import ReportTemplateModel, ReportJobModel


class SqlAlchemyReportTemplateRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: ReportTemplate) -> ReportTemplate:
        model = report_template_entity_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return report_template_model_to_entity(model)

    async def get_by_id(self, template_id: str) -> ReportTemplate | None:
        result = await self._session.execute(
            select(ReportTemplateModel).where(ReportTemplateModel.id == template_id)
        )
        model = result.scalar_one_or_none()
        return report_template_model_to_entity(model) if model else None

    async def list_all(self) -> list[ReportTemplate]:
        result = await self._session.execute(
            select(ReportTemplateModel).order_by(ReportTemplateModel.created_at.desc())
        )
        return [report_template_model_to_entity(m) for m in result.scalars().all()]


class SqlAlchemyReportJobRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: ReportJob) -> ReportJob:
        model = report_job_entity_to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return report_job_model_to_entity(model)

    async def get_by_id(self, job_id: str) -> ReportJob | None:
        result = await self._session.execute(
            select(ReportJobModel).where(ReportJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        return report_job_model_to_entity(model) if model else None

    async def update(self, entity: ReportJob) -> ReportJob:
        model = report_job_entity_to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()
        return report_job_model_to_entity(merged)

    async def list_all(self) -> list[ReportJob]:
        result = await self._session.execute(
            select(ReportJobModel).order_by(ReportJobModel.created_at.desc())
        )
        return [report_job_model_to_entity(m) for m in result.scalars().all()]
