# backend/app/infrastructure/document_processing/pdfplumber_processor.py
from __future__ import annotations

import asyncio
from pathlib import Path

import pdfplumber

from app.domain.interfaces.providers import DocumentProcessor
from app.domain.value_objects.types import ExtractedTable, PageText


class PdfPlumberProcessor(DocumentProcessor):
    """Document processor using pdfplumber for PDF text and table extraction."""

    async def extract_text(self, file_path: Path) -> list[PageText]:
        return await asyncio.to_thread(self._extract_text_sync, file_path)

    async def extract_tables(self, file_path: Path) -> list[ExtractedTable]:
        return await asyncio.to_thread(self._extract_tables_sync, file_path)

    @staticmethod
    def _extract_text_sync(file_path: Path) -> list[PageText]:
        pages: list[PageText] = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append(PageText(page_number=i + 1, text=text))
        return pages

    @staticmethod
    def _extract_tables_sync(file_path: Path) -> list[ExtractedTable]:
        tables: list[ExtractedTable] = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                raw_tables = page.extract_tables() or []
                for raw_table in raw_tables:
                    if not raw_table or len(raw_table) < 2:
                        continue
                    # First row as headers, rest as data rows
                    headers = [str(cell or "") for cell in raw_table[0]]
                    rows = [
                        [str(cell or "") for cell in row]
                        for row in raw_table[1:]
                    ]
                    tables.append(
                        ExtractedTable(
                            page_number=i + 1,
                            headers=headers,
                            rows=rows,
                            confidence=0.8,  # Default confidence for pdfplumber
                        )
                    )
        return tables
