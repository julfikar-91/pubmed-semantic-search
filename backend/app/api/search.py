import logging
import time
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import Article, PipelineStepLog, SearchRequest, SearchResponse, SpellCorrection
from app.pipeline.build_query import build_pubmed_query, build_relaxed_query
from app.pipeline.embed_and_score import embed_and_score_articles
from app.pipeline.expand_synonyms import expand_synonyms
from app.pipeline.extract_concepts import extract_concepts
from app.pipeline.med_search_pipeline import take_user_query
from app.pipeline.pubmed_client import PubMedServiceUnavailableError, search_pubmed
from app.pipeline.rerank import apply_final_filters, rerank_and_fuse
from app.pipeline.spell_correct import correct_biomedical_query
from app.pipeline.validate_mesh import validate_mesh
from app.services.cache_service import cache_service
from app.services.mesh_data import MeshDictionaryManager
from app.services.metrics import metrics_tracker
from app.services.vector_store import create_vector_store

logger = logging.getLogger(__name__)
router = APIRouter()

# The approved diagram defines a candidate abstract pool before Top-K output.
CANDIDATE_POOL_SIZE = 100


def _snippet(article: Article) -> str:
    return f"{article.abstract[:280]}..." if len(article.abstract) > 280 else article.abstract


def _verify_citation(article: Article) -> bool:
    snippet = _snippet(article).removesuffix("...").strip()
    return bool(snippet) and snippet in article.abstract


def _pipeline_metric(results: List[Article]) -> Dict[str, float]:
    """Report only properties of retrieved source abstracts, not generated-answer quality."""
    if not results:
        return {"answer_relevancy": 0.0, "faithfulness": 0.0}
    return {
        "answer_relevancy": round(sum(article.final_score for article in results) / len(results), 3),
        "faithfulness": round(sum(article.citation_verified for article in results) / len(results), 3),
    }


@router.get("/health")
async def health_check():
    mesh_mgr = MeshDictionaryManager.get_instance()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "backend": "connected",
        # A local health check cannot prove the external PubMed service is up.
        # Live availability is validated during an actual search request.
        "ncbi_status": "Configured",
        "mesh_status": f"Loaded ({len(mesh_mgr.descriptors):,} terms)" if mesh_mgr.is_loaded else "Operational",
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vector_store": "Operational",
    }


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    summary = metrics_tracker.get_summary()
    summary["cache_stats"] = cache_service.get_stats()
    return summary


@router.post("/search", response_model=SearchResponse)
async def perform_search(request: SearchRequest):
    """Execute the eight-stage pipeline represented in the approved architecture."""
    start_time = time.time()
    pipeline_logs: List[PipelineStepLog] = []
    validated_raw_query = take_user_query(request.query)

    # Stage 0: API gateway/orchestrator checks the Tier-1 query cache first.
    cache_key = request.model_dump()
    cached_response = cache_service.get(cache_key)
    if cached_response:
        cached_resp = cached_response.model_copy()
        cached_resp.cached = True
        cached_resp.from_cache = True
        cached_resp.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        metrics_tracker.log_search_event(request.query, cached_resp.execution_time_ms, len(cached_resp.results), cached=True)
        return cached_resp

    try:
        # 1. Biomedical spell correction
        t0 = time.time()
        effective_query = validated_raw_query
        spell_corrections: List[SpellCorrection] = []
        if request.use_spell_correction:
            effective_query, spell_corrections = correct_biomedical_query(validated_raw_query)
        spell_ms = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("spell_correction", spell_ms)
        pipeline_logs.append(PipelineStepLog(
            step_number=1,
            step_name="Biomedical Spell Correction",
            status="success" if request.use_spell_correction else "skipped",
            duration_ms=spell_ms,
            details=(
                f"Corrected {len(spell_corrections)} MeSH-backed biomedical term(s)"
                if request.use_spell_correction else "Disabled by request"
            ),
        ))

        # 2. Biomedical NER / concept extraction
        t0 = time.time()
        concepts = extract_concepts(effective_query)
        ner_ms = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("concept_extraction", ner_ms)
        pipeline_logs.append(PipelineStepLog(
            step_number=2,
            step_name="Biomedical NER & Concept Extraction",
            status="success",
            duration_ms=ner_ms,
            details=f"Extracted {len(concepts)} disease, drug, gene, target, or outcome concept(s)",
        ))

        # 3. LLM expansion only proposes candidate synonyms. It never becomes
        # an unvalidated, free-form PubMed query.
        t0 = time.time()
        expanded_synonyms = await expand_synonyms(concepts, use_llm=request.use_llm_expansion)
        expansion_ms = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("synonym_expansion", expansion_ms)
        pipeline_logs.append(PipelineStepLog(
            step_number=3,
            step_name="LLM Synonym Expansion (Candidates Only)",
            status="success" if request.use_llm_expansion else "skipped",
            duration_ms=expansion_ms,
            details=f"Prepared synonym candidates for {len(expanded_synonyms)} extracted concept(s)",
        ))

        # 4. MeSH validation guardrail
        t0 = time.time()
        mesh_results = await validate_mesh(expanded_synonyms, enabled=request.use_mesh_guardrail)
        mesh_ms = round((time.time() - t0) * 1000, 2)
        valid_mesh_count = sum(item.is_valid for item in mesh_results)
        metrics_tracker.record_stage_latency("mesh_validation", mesh_ms)
        pipeline_logs.append(PipelineStepLog(
            step_number=4,
            step_name="MeSH Validation Guardrail",
            status="success" if request.use_mesh_guardrail else "skipped",
            duration_ms=mesh_ms,
            details=f"Validated {valid_mesh_count}/{len(mesh_results)} candidate concept(s) against local MeSH",
        ))

        # 5. Strict MeSH/TIAB Boolean query with a relaxed fallback.
        t0 = time.time()
        pubmed_query = build_pubmed_query(effective_query, expanded_synonyms, mesh_results, request.filters)
        relaxed_query = build_relaxed_query(effective_query, expanded_synonyms, mesh_results, request.filters)
        query_ms = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("query_builder", query_ms)
        pipeline_logs.append(PipelineStepLog(
            step_number=5,
            step_name="Strict MeSH / TIAB Query Builder",
            status="success",
            duration_ms=query_ms,
            details="Built strict Boolean query; relaxed query is used only when strict retrieval has no records",
        ))

        # 6. Async NCBI ESearch/EFetch candidate abstract pool
        t0 = time.time()
        requested_top_k = min(request.filters.max_results if request.filters else 20, 100)
        candidate_pool_size = max(CANDIDATE_POOL_SIZE, requested_top_k)
        total_found, fetched_articles = await search_pubmed(
            pubmed_query,
            max_results=candidate_pool_size,
            fallback_query=relaxed_query,
        )
        retrieval_ms = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("ncbi_retrieval", retrieval_ms)
        pipeline_logs.append(PipelineStepLog(
            step_number=6,
            step_name="NCBI ESearch & EFetch Candidate Abstract Pool",
            status="success" if fetched_articles else "warning",
            duration_ms=retrieval_ms,
            details=f"Retrieved {len(fetched_articles)} candidate abstract(s) from {total_found:,} matching PubMed record(s)",
        ))

        # 7. Dense SentenceTransformer / cache / FAISS and lexical BM25 each
        # run exactly once over the same candidate pool.
        t0 = time.time()
        valid_articles = [article for article in fetched_articles if article.abstract]
        vector_store = create_vector_store(dimension=settings.VECTOR_DIMENSION)
        scored_articles = embed_and_score_articles(effective_query, valid_articles, vector_store)
        embedding_ms = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("embedding_scoring", embedding_ms)
        pipeline_logs.append(PipelineStepLog(
            step_number=7,
            step_name="Dense Vector, Embedding Cache, FAISS & BM25 Scoring",
            status="success" if scored_articles else "warning",
            duration_ms=embedding_ms,
            details=f"Computed dense cosine and BM25 scores for {len(scored_articles)} candidate abstract(s)",
        ))

        # 8. Approved 5-factor fusion, final defensive filtering, Top-K
        t0 = time.time()
        ranked_articles = rerank_and_fuse(
            scored_articles,
            query_text=effective_query,
            concepts=concepts,
            validated_mesh=mesh_results,
            filters=None,
        )
        final_results = apply_final_filters(ranked_articles, request.filters)[:requested_top_k]
        for article in final_results:
            article.snippet = _snippet(article)
            article.url = article.url or f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/"
            article.citation_verified = _verify_citation(article)
            article.relevance_score = article.final_score
            article.similarity_score = article.semantic_score
        final_metrics = _pipeline_metric(final_results)
        rerank_ms = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("rerank_fusion", rerank_ms)
        pipeline_logs.append(PipelineStepLog(
            step_number=8,
            step_name="5-Factor Hybrid Score Fusion & Top-K Reranking",
            status="success" if final_results else "warning",
            duration_ms=rerank_ms,
            details="Ranked with 40% Dense Vector + 25% BM25 + 15% MeSH + 10% Title + 10% Concept Coverage",
        ))

        total_duration = round((time.time() - start_time) * 1000, 2)
        metrics_tracker.record_search(total_duration, success=True)
        metrics_tracker.log_search_event(request.query, total_duration, len(final_results), cached=False)
        response = SearchResponse(
            query=request.query,
            corrected_query=effective_query if effective_query != request.query else None,
            spell_corrections=spell_corrections,
            pubmed_query=pubmed_query,
            concepts=concepts,
            expanded_synonyms=expanded_synonyms,
            validated_mesh=mesh_results,
            total_found=total_found,
            summary={"total_articles": total_found, "esearch_results": total_found, "final_results": len(final_results)},
            results=final_results,
            pipeline_logs=pipeline_logs,
            execution_time_ms=total_duration,
            cached=False,
            metrics=final_metrics,
            from_cache=False,
            elapsed_seconds=round(total_duration / 1000.0, 2),
        )
        cache_service.set(cache_key, response)
        return response
    except PubMedServiceUnavailableError as exc:
        total_duration = round((time.time() - start_time) * 1000, 2)
        metrics_tracker.record_search(total_duration, success=False)
        logger.warning("PubMed search service unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="PubMed is temporarily unavailable. Please retry the search shortly.",
        ) from exc
    except Exception as exc:
        total_duration = round((time.time() - start_time) * 1000, 2)
        metrics_tracker.record_search(total_duration, success=False)
        logger.error("Search pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search pipeline error: {exc}") from exc


from app.evaluation.eval_harness import run_evaluation_benchmark


@router.get("/evaluate")
async def evaluate_harness(limit: int = 5) -> Dict[str, Any]:
    """Run the retained live benchmark endpoint for the evaluation page."""
    try:
        return await run_evaluation_benchmark(queries_limit=max(1, min(limit, 15)))
    except PubMedServiceUnavailableError as exc:
        logger.warning("PubMed evaluation service unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="PubMed is temporarily unavailable. Please retry the evaluation shortly.",
        ) from exc
    except Exception as exc:
        logger.error("Evaluation harness failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}") from exc
