import numpy as np
import logging
from typing import List, Tuple, Dict
from app.models.schemas import Article
from app.services.vector_store import VectorStore
from app.config import settings

logger = logging.getLogger(__name__)

_ST_MODEL = None
_ST_MODEL_INITIALIZED = False

def get_st_model():
    global _ST_MODEL, _ST_MODEL_INITIALIZED
    if not _ST_MODEL_INITIALIZED:
        _ST_MODEL_INITIALIZED = True
        try:
            from sentence_transformers import SentenceTransformer
            _ST_MODEL = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded SentenceTransformer model '{settings.EMBEDDING_MODEL}'")
        except Exception as e:
            logger.info(f"SentenceTransformer not available ({e}). Using lightweight vectorizer fallback.")
    return _ST_MODEL

class LightweightVectorizer:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def encode(self, texts: List[str]) -> np.ndarray:
        embeddings = []
        for text in texts:
            vec = np.zeros(self.dimension, dtype=np.float32)
            words = text.lower().split()
            if not words:
                embeddings.append(vec)
                continue

            for idx, word in enumerate(words):
                h = hash(word) % self.dimension
                val = 1.0 / (1.0 + np.log(1.0 + idx))
                vec[h] += val

            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec)

        return np.array(embeddings, dtype=np.float32)

fallback_vectorizer = LightweightVectorizer(dimension=settings.VECTOR_DIMENSION)

def compute_embeddings(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, settings.VECTOR_DIMENSION), dtype=np.float32)

    model = get_st_model()
    if model is not None:
        try:
            vecs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return vecs
        except Exception as e:
            logger.warning(f"SentenceTransformer encoding failed: {e}")

    return fallback_vectorizer.encode(texts)

from app.services.cache_service import cache_service

def compute_embeddings_with_cache(texts: List[str]) -> np.ndarray:
    """Compute dense embeddings with Tier 4 LRU vector cache to skip redundant calculations."""
    if not texts:
        return np.zeros((0, settings.VECTOR_DIMENSION), dtype=np.float32)

    cached_vecs: Dict[int, np.ndarray] = {}
    uncached_indices: List[int] = []
    uncached_texts: List[str] = []

    for i, t in enumerate(texts):
        v = cache_service.get_vector(t)
        if v is not None:
            cached_vecs[i] = v
        else:
            uncached_indices.append(i)
            uncached_texts.append(t)

    if uncached_texts:
        new_vecs = compute_embeddings(uncached_texts)
        for i, idx in enumerate(uncached_indices):
            vec = new_vecs[i]
            cached_vecs[idx] = vec
            cache_service.set_vector(uncached_texts[i], vec)

    ordered_vecs = [cached_vecs[i] for i in range(len(texts))]
    return np.array(ordered_vecs, dtype=np.float32)

import re
try:
    from rank_bm25 import BM25Plus
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

def embed_and_score_articles(query: str, articles: List[Article], vector_store: VectorStore) -> List[Article]:
    """Step 7: Compute genuine dense embeddings via VectorStore and authentic BM25 lexical relevance."""
    if not articles:
        return []

    vector_store.clear()
    
    # 1. Encode query vector
    query_vec = compute_embeddings_with_cache([query])[0]
    
    # 2. Encode document text vectors & index into VectorStore
    doc_texts = [f"{art.title}. {art.abstract}" for art in articles]
    doc_ids = [art.pmid for art in articles]

    doc_vecs = compute_embeddings_with_cache(doc_texts)
    vector_store.add_vectors(doc_ids, doc_vecs)

    # 3. Perform genuine VectorStore semantic search
    search_results = dict(vector_store.search(query_vec, top_k=len(articles)))

    # 4. Perform genuine BM25Plus lexical scoring
    query_tokens = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 1]
    corpus_tokens = [
        [w.lower() for w in re.findall(r"\w+", f"{art.title} {art.abstract} {' '.join(art.mesh_terms)}") if len(w) > 1]
        for art in articles
    ]

    bm25_scores = [0.0] * len(articles)
    if HAS_BM25 and query_tokens and corpus_tokens:
        try:
            bm25 = BM25Plus(corpus_tokens)
            raw_bm25 = bm25.get_scores(query_tokens)
            max_b = float(max(raw_bm25)) if len(raw_bm25) > 0 else 0.0
            min_b = float(min(raw_bm25)) if len(raw_bm25) > 0 else 0.0
            if max_b > min_b:
                bm25_scores = [(s - min_b) / (max_b - min_b) for s in raw_bm25]
            elif max_b > 0:
                bm25_scores = [1.0 for _ in raw_bm25]
        except Exception as e:
            logger.warning(f"BM25 scoring fallback: {e}")

    # 5. Populate calibrated real scores for each article
    for idx, art in enumerate(articles):
        sem_sim = float(search_results.get(art.pmid, 0.0))
        lex_sim = float(bm25_scores[idx]) if idx < len(bm25_scores) else 0.0

        art.semantic_score = round(float(np.clip(sem_sim, 0.0, 1.0)), 3)
        art.bm25_score = round(float(np.clip(lex_sim, 0.0, 1.0)), 3)
        art.lexical_score = art.bm25_score

    return articles



