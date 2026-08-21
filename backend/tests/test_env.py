import pytest
from app.config import settings

def test_env_variables_loaded():
    """Verify that settings correctly loads backend/.env variables."""
    assert settings.NCBI_API_KEY == "6714e80da3c772cc9a66997a45403e9b4008"
    assert settings.NCBI_EMAIL == "khustarjamal@gmail.com"
    assert settings.LLM_PROVIDER == "mock"
    assert settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2"
    assert settings.CACHE_TTL_SECONDS == 3600
    assert settings.DEBUG is True
    assert settings.GEMINI_API_KEY != ""
