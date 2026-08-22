import pytest
from app.config import settings

def test_env_variables_loaded():
    """Verify that settings correctly loads backend environment variables."""
    assert isinstance(settings.NCBI_EMAIL, str)
    assert settings.LLM_PROVIDER in ["gemini", "openai", "mock"]
    assert settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2"
    assert settings.CACHE_TTL_SECONDS > 0
    assert settings.DEBUG is True
