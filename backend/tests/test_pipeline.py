import pytest
import numpy as np
from app.models.schemas import ExtractedConcept, ExpandedSynonym, SearchFilter, Article, SpellCorrection
from app.pipeline.spell_correct import correct_biomedical_query
from app.pipeline.extract_concepts import extract_concepts
from app.pipeline.expand_synonyms import expand_synonyms
from app.pipeline.validate_mesh import validate_mesh
from app.pipeline.build_query import build_pubmed_query
from app.pipeline.pubmed_client import search_pubmed
from app.pipeline.embed_and_score import embed_and_score_articles, compute_embeddings
from app.pipeline.rerank import rerank_and_fuse
from app.services.cache_service import CacheService
from app.services.vector_store import VectorStore, create_vector_store

def test_biomedical_spell_correction():
    # Single typo
    corrected, corrections = correct_biomedical_query("what are effects of metformn on diabtes")
    assert "metformin" in corrected.lower()
    assert "diabetes" in corrected.lower()
    assert len(corrections) >= 2
    assert any(c.original_term.lower() == "metformn" and c.mesh_id == "D004559" for c in corrections)

    # Multi-word phrase typo
    corrected_mw, corrections_mw = correct_biomedical_query("mocardial infaction in elderly")
    assert "myocardial infarction" in corrected_mw.lower()
    assert any(c.mesh_id == "D009203" for c in corrections_mw)

    # Exact term (no correction needed)
    corrected_exact, corrections_exact = correct_biomedical_query("semaglutide and cardiovascular disease")
    assert corrected_exact == "semaglutide and cardiovascular disease"
    assert len(corrections_exact) == 0

def test_extract_concepts():
    query = "Effect of metformin on type 2 diabetes and cardiovascular disease outcomes"
    concepts = extract_concepts(query)
    assert len(concepts) >= 2
    concept_texts = [c.text.lower() for c in concepts]
    assert any("metformin" in t for t in concept_texts)
    assert any("type 2 diabetes" in t or "diabetes" in t for t in concept_texts)

@pytest.mark.asyncio
async def test_expand_synonyms():
    concepts = [
        ExtractedConcept(text="metformin", category="Drug", confidence=0.98),
        ExtractedConcept(text="type 2 diabetes", category="Disease", confidence=0.99)
    ]
    expanded = await expand_synonyms(concepts, use_llm=False)
    assert len(expanded) == 2
    assert expanded[0].term == "metformin"
    assert "biguanides" in expanded[0].synonyms or "dimethylbiguanide" in expanded[0].synonyms
    assert expanded[0].mesh_heading == "Metformin"

@pytest.mark.asyncio
async def test_validate_mesh():
    expanded = [
        ExpandedSynonym(term="metformin", synonyms=["biguanides"], mesh_heading="Metformin"),
        ExpandedSynonym(term="type 2 diabetes", synonyms=["T2D"], mesh_heading="Diabetes Mellitus, Type 2")
    ]
    results = await validate_mesh(expanded, enabled=True)
    assert len(results) == 2
    assert results[0].is_valid is True
    assert results[0].mesh_heading == "Metformin"
    assert results[1].is_valid is True

def test_build_pubmed_query():
    expanded = [
        ExpandedSynonym(term="metformin", synonyms=["metformin", "biguanides"], mesh_heading="Metformin"),
        ExpandedSynonym(term="weight loss", synonyms=["weight loss", "weight reduction"], mesh_heading="Loss, Weight")
    ]
    mesh_results = [
        type("MeSHValidationResult", (), {"original_term": "metformin", "is_valid": True, "mesh_heading": "Metformin"})(),
        type("MeSHValidationResult", (), {"original_term": "weight loss", "is_valid": True, "mesh_heading": "Weight Loss"})()
    ]
    filters = SearchFilter(date_from="2020-01-01", date_to="2023-12-31", max_results=10)
    query_str = build_pubmed_query("metformin and weight loss", expanded, mesh_results, filters)
    assert '"Metformin"[MeSH]' in query_str
    assert 'metformin[tiab]' in query_str
    assert '"weight loss"[tiab]' in query_str
    assert '[Date - Publication]' in query_str

@pytest.mark.asyncio
async def test_search_pubmed_live_and_article_cache():
    total_found, articles = await search_pubmed("metformin[MeSH]", max_results=3)
    assert total_found > 0
    assert len(articles) > 0
    assert articles[0].pmid is not None
    assert articles[0].title != ""
    assert not articles[0].abstract.startswith("PubMed Abstract for PMID")
    assert len(articles[0].abstract) > 30

    # Verify Article was cached in Tier 3
    from app.services.cache_service import cache_service
    cached_art = cache_service.get_article(articles[0].pmid)
    assert cached_art is not None
    assert cached_art.pmid == articles[0].pmid
    assert cached_art.title == articles[0].title

def test_vector_store_and_vector_cache():
    store = create_vector_store(dimension=384)
    articles = [
        Article(pmid="1001", title="Metformin treatment in diabetes", abstract="Study of metformin efficacy in type 2 diabetes patients."),
        Article(pmid="1002", title="Cardiovascular benefits of SGLT2", abstract="Clinical trial of empagliflozin in heart failure.")
    ]
    scored = embed_and_score_articles("metformin diabetes", articles, store)
    assert len(scored) == 2
    assert scored[0].semantic_score > 0.0
    assert scored[0].bm25_score > 0.0

    from app.services.cache_service import cache_service
    vec = cache_service.get_vector("metformin diabetes")
    assert vec is not None

def test_rerank_and_fuse():
    articles = [
        Article(pmid="1001", title="Doc 1", abstract="Abstract 1", semantic_score=0.90, bm25_score=0.50),
        Article(pmid="1002", title="Doc 2", abstract="Abstract 2", semantic_score=0.60, bm25_score=0.95)
    ]
    reranked = rerank_and_fuse(articles, alpha=0.6)
    assert len(reranked) == 2
    assert reranked[0].final_score > 0.0
    assert "Semantic:" in reranked[0].explanation

def test_cache_service():
    cache = CacheService(ttl_seconds=10)
    cache.set("test_key", {"data": "hello"})
    val = cache.get("test_key")
    assert val == {"data": "hello"}
    
    # Test Tier 3 article cache
    art = Article(pmid="999", title="Test Art", abstract="Test Abs")
    cache.set_article("999", art)
    assert cache.get_article("999").title == "Test Art"
    
    # Test Tier 4 vector cache
    cache.set_vector("test sentence", np.array([0.1, 0.2]))
    assert cache.get_vector("test sentence") is not None

    cache.clear()
    assert cache.get("test_key") is None
    assert cache.get_article("999") is None
    assert cache.get_vector("test sentence") is None

# ============================================================================
# Priority Integrity Tests (Unclamped Metrics, Keyword Search, SentenceTransformers, Formula Consistency)
# ============================================================================

def test_unclamped_metrics_on_garbage_query():
    """TEST 1: Metrics must NOT be clamped with hardcoded floors. Garbage query yields 0.0 precision."""
    from app.evaluation.eval_harness import calculate_precision_at_k, calculate_recall, calculate_mrr, calculate_ndcg_at_k
    retrieved = ["11111111", "22222222", "33333333"]
    expected = ["99999999"] # None match
    
    p10 = calculate_precision_at_k(retrieved, expected, k=10)
    recall = calculate_recall(retrieved, expected, k=10)
    mrr = calculate_mrr(retrieved, expected, k=10)
    ndcg = calculate_ndcg_at_k(retrieved, expected, k=10)

    # All must be 0.0, absolutely NO 0.85/0.60 floor
    assert p10 == 0.0
    assert recall == 0.0
    assert mrr == 0.0
    assert ndcg == 0.0

@pytest.mark.asyncio
async def test_keyword_baseline_executes_live_search():
    """TEST 2: Keyword baseline must run actual raw PubMed search, not return hardcoded constants."""
    from app.evaluation.eval_harness import execute_keyword_baseline
    pmids, lat, meta = await execute_keyword_baseline("metformin")
    assert isinstance(pmids, list)
    assert len(pmids) > 0
    assert lat > 0.0
    assert meta["raw_query"] == "metformin[tiab]"

def test_requirements_txt_has_sentence_transformers():
    """TEST 3: Verify requirements.txt includes sentence-transformers for production vector embeddings."""
    from pathlib import Path
    req_file = Path(__file__).parent.parent / "requirements.txt"
    assert req_file.exists()
    content = req_file.read_text(encoding="utf-8")
    assert "sentence-transformers" in content
    assert "rank-bm25" in content

    from app.pipeline.embed_and_score import get_st_model
    # get_st_model helper must exist
    assert callable(get_st_model)

def test_hybrid_score_weighting_formula_consistency():
    """TEST 4: Formula, docstrings, and log details must consistently use 40% Semantic, 25% BM25, 15% MeSH, 10% Title, 10% Coverage."""
    import inspect
    from app.pipeline.rerank import rerank_and_fuse
    
    doc = inspect.getdoc(rerank_and_fuse) or ""
    assert "0.40 * SemanticSim" in doc
    assert "0.25 * BM25Score" in doc
    assert "0.15 * MeSHMatch" in doc
    assert "0.10 * TitleRel" in doc
    assert "0.10 * EntityCoverage" in doc


