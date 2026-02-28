# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.assumptions import router as assumptions_router
from app.api.v1.deals import router as deals_router
from app.api.v1.documents import router as documents_router
from app.api.v1.exports import router as exports_router
from app.api.v1.model import router as model_router
from app.config import settings
from app.infrastructure.persistence.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
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
app.include_router(model_router, prefix="/v1")
app.include_router(exports_router, prefix="/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
