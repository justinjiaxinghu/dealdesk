# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="DealDesk API", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
