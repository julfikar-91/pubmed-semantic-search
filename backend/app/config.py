import os
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    APP_NAME: str = "PubMed Semantic Search API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # NCBI Entrez PubMed API settings
    NCBI_API_KEY: Optional[str] = os.getenv("NCBI_API_KEY", "")
    NCBI_EMAIL: str = os.getenv("NCBI_EMAIL", "researcher@example.com")

    # LLM Settings (OpenAI / Gemini / Mock)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")  # "openai", "gemini", "mock"
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")

    # Vector store & Embedding settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
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

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
