import logging
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.search import router as search_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from app.services.mesh_data import MeshDictionaryManager
from app.pipeline.spell_correct import BiomedicalSpellChecker

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NLM MeSH Dictionary & Spell Checker at startup...")
    MeshDictionaryManager.get_instance()
    BiomedicalSpellChecker.get_instance()
    logger.info("MeSH Biomedical Dictionary & Spell Checker ready!")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FastAPI Backend for PubMed Semantic Search & Medical NLP Pipeline",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Welcome to PubMed Semantic Search API",
        "docs_url": "/docs",
        "health_check": "/api/health",
        "evaluation_harness": "/api/evaluate"
    }

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
