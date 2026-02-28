# backend/app/domain/interfaces/providers.py
from abc import ABC, abstractmethod
from pathlib import Path

from app.domain.entities import Assumption, Deal
from app.domain.value_objects import (
    BenchmarkSuggestion,
    ExtractedTable,
    Location,
    NormalizedField,
    PageText,
    PropertyType,
    QuickExtractResult,
    RawField,
)


class DocumentProcessor(ABC):
    @abstractmethod
    async def extract_text(self, file_path: Path) -> list[PageText]: ...

    @abstractmethod
    async def extract_tables(self, file_path: Path) -> list[ExtractedTable]: ...


class LLMProvider(ABC):
    @abstractmethod
    async def generate_benchmarks(
        self, location: Location, property_type: PropertyType
    ) -> list[BenchmarkSuggestion]: ...

    @abstractmethod
    async def normalize_extracted_fields(
        self, raw_fields: list[RawField]
    ) -> list[NormalizedField]: ...

    @abstractmethod
    async def quick_extract_deal_info(
        self, pages: list[PageText]
    ) -> QuickExtractResult: ...


class FileStorage(ABC):
    @abstractmethod
    async def store(self, data: bytes, path: str) -> str: ...

    @abstractmethod
    async def retrieve(self, path: str) -> Path: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...


class ExcelExporter(ABC):
    @abstractmethod
    async def export(
        self, deal: Deal, assumptions: list[Assumption]
    ) -> bytes: ...
