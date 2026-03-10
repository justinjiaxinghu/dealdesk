# backend/app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from app.api.v1.assumptions import router as assumptions_router
from app.api.v1.comps import router as comps_router
from app.api.v1.deals import router as deals_router
from app.api.v1.documents import router as documents_router
from app.api.v1.exports import router as exports_router
from app.api.v1.financial_model import router as financial_model_router
from app.api.v1.historical_financials import router as historical_financials_router
from app.api.v1.quick_extract import router as quick_extract_router
from app.api.v1.chat import router as chat_router
from app.api.v1.explorations import router as explorations_router
from app.api.v1.snapshots import router as snapshots_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.om_upload import router as om_upload_router
from app.api.v1.connectors import router as connectors_router
from app.api.v1.reports import router as reports_router
from app.api.v1.validation import router as validation_router
from app.config import settings
from app.infrastructure.persistence.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables (safe for SQLite dev; use Alembic migrations for PostgreSQL prod)
    from app.infrastructure.persistence.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="DealDesk API",
    version="0.1.0",
    description="AI-Assisted Real Estate Deal Evaluation",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deals_router, prefix="/v1")
app.include_router(documents_router, prefix="/v1")
app.include_router(assumptions_router, prefix="/v1")
app.include_router(exports_router, prefix="/v1")
app.include_router(quick_extract_router, prefix="/v1")
app.include_router(validation_router, prefix="/v1")
app.include_router(comps_router, prefix="/v1")
app.include_router(financial_model_router, prefix="/v1")
app.include_router(historical_financials_router, prefix="/v1")
app.include_router(explorations_router, prefix="/v1")
app.include_router(chat_router, prefix="/v1")
app.include_router(snapshots_router, prefix="/v1")
app.include_router(datasets_router, prefix="/v1")
app.include_router(om_upload_router, prefix="/v1")
app.include_router(connectors_router, prefix="/v1")
app.include_router(reports_router, prefix="/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
