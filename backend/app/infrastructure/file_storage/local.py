# backend/app/infrastructure/file_storage/local.py
from __future__ import annotations

from pathlib import Path

import aiofiles

from app.config import settings
from app.domain.interfaces.providers import FileStorage


class LocalFileStorage(FileStorage):
    """File storage backed by local filesystem."""

    def __init__(self, base_path: Path | None = None) -> None:
        self._base = base_path or settings.file_storage_path

    async def store(self, data: bytes, path: str) -> str:
        full_path = self._base / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)
        return path

    async def retrieve(self, path: str) -> Path:
        full_path = self._base / path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        return full_path

    async def delete(self, path: str) -> None:
        full_path = self._base / path
        if full_path.exists():
            full_path.unlink()
