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
    NCBI_API_KEY: Optional[str] = os.environ.get("NCBI_API_KEY", "")
    NCBI_EMAIL: str = os.environ.get("NCBI_EMAIL", "jhakoyna@example.com")

    # LLM Settings (Gemini / Anthropic / Mock)
    LLM_PROVIDER: str = "gemini"
    OPENAI_API_KEY: Optional[str] = ""
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: Optional[str] = os.environ.get("ANTHROPIC_API_KEY", "")
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"

    # Vector store & Embedding settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384

    # Cache settings
    CACHE_TTL_SECONDS: int = 1800  # 30 minutes
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

