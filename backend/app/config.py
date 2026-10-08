"""
Application Configuration Module.

Loads environment variables from the .env file using Pydantic Settings
to guarantee type validation and application safety.
"""

from typing import List, Union
import json
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "AI-Driven Individualized Learning Journey Generator"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_learning_db"

    # Security & Auth
    SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_chars_long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # AI Configuration (Gemini)
    GEMINI_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=[ENV_FILE, ".env"],
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Instantiate a singleton settings object to be imported across the backend
settings = Settings()
