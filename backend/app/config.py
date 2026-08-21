import os
from pathlib import Path
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    APP_NAME: str = "PubMed Semantic Search API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # NCBI Entrez PubMed API settings
    NCBI_API_KEY: Optional[str] = ""
    NCBI_EMAIL: str = "researcher@example.com"

    # LLM Settings (OpenAI / Gemini / Mock)
    LLM_PROVIDER: str = "mock"  # "openai", "gemini", "mock"
    OPENAI_API_KEY: Optional[str] = ""
    GEMINI_API_KEY: Optional[str] = ""

    # Vector store & Embedding settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384

    # Cache settings
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    MAX_CACHE_SIZE: int = 1000

    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH) if ENV_FILE_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

