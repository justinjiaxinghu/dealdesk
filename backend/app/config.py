# backend/app/config.py
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "DEALDESK_", "env_file": ".env", "env_file_encoding": "utf-8"}

    database_url: str = "sqlite+aiosqlite:///./dealdesk.db"
    database_url_sync: str = "sqlite:///./dealdesk.db"
    file_storage_path: Path = Path("./storage")
    openai_api_key: str = ""
    tavily_api_key: str = ""
    openai_model: str = "gpt-4o"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
