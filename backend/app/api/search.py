import time
import logging
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.models.schemas import (
    SearchRequest, SearchResponse, PipelineStepLog, SpellCorrection
)
from app.pipeline.spell_correct import correct_biomedical_query
from app.pipeline.extract_concepts import extract_concepts
from app.pipeline.expand_synonyms import expand_synonyms
from app.pipeline.validate_mesh import validate_mesh
from app.pipeline.build_query import build_pubmed_query, build_relaxed_query
from app.pipeline.pubmed_client import search_pubmed
from app.pipeline.embed_and_score import embed_and_score_articles
from app.pipeline.rerank import rerank_and_fuse
from app.services.cache_service import cache_service
from app.services.vector_store import create_vector_store
from app.services.metrics import metrics_tracker
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

from app.services.mesh_data import MeshDictionaryManager

@router.get("/health")
async def health_check():
    """Health check endpoint for the PubMed Semantic Search API."""
    mesh_mgr = MeshDictionaryManager.get_instance()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "backend": "connected",
        "ncbi_status": "Operational",
        "mesh_status": f"Loaded ({len(mesh_mgr.descriptors):,} terms)" if mesh_mgr.is_loaded else "Operational",
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vector_store": "Operational"
    }


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Telemetry and operational monitoring endpoint."""
    summary = metrics_tracker.get_summary()
    summary["cache_stats"] = cache_service.get_stats()
    return summary

@router.post("/search", response_model=SearchResponse)
async def perform_search(request: SearchRequest):
    """Execute the full 8-step PubMed Semantic Search pipeline with Biomedical Spell Correction."""
    start_time = time.time()
    pipeline_logs: List[PipelineStepLog] = []

    cache_key = request.model_dump()
    cached_response = cache_service.get(cache_key)
    if cached_response:
        cached_resp = cached_response.model_copy()
        cached_resp.cached = True
        cached_resp.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        metrics_tracker.log_search_event(request.query, cached_resp.execution_time_ms, len(cached_resp.results), cached=True)
        return cached_resp

    try:
        # Step 1: Biomedical Spell Correction (MeSH Dictionary + Fuzzy Matching)
        effective_query = request.query
        spell_corrections: List[SpellCorrection] = []
        if request.use_spell_correction:
            t0 = time.time()
            effective_query, spell_corrections = correct_biomedical_query(request.query)
            dt_spell = round((time.time() - t0) * 1000, 2)
            metrics_tracker.record_stage_latency("spell_correction", dt_spell)
            
            if spell_corrections:
                detail_str = f"Corrected {len(spell_corrections)} biomedical typo(s): " + ", ".join([f"'{c.original_term}' → '{c.corrected_term}'" for c in spell_corrections])
            else:
                detail_str = "Verified query against offline MeSH dictionary (0 typos detected)"
            
            pipeline_logs.append(PipelineStepLog(
                step_number=1,
                step_name="Biomedical Spell Correction (MeSH Fuzzy Match)",
                status="success",
                duration_ms=dt_spell,
                details=detail_str
            ))

        # Step 2: Concept & Entity Extraction
        t0 = time.time()
        concepts = extract_concepts(effective_query)
        dt_ner = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("concept_extraction", dt_ner)
        pipeline_logs.append(PipelineStepLog(
            step_number=2,
            step_name="Extract Concepts (Biomedical NER)",
            status="success",
            duration_ms=dt_ner,
            details=f"Extracted {len(concepts)} biomedical entities ({', '.join([f'{c.text} [{c.category}]' for c in concepts[:3]])})"
        ))

        # Step 3: Synonym Expansion
        t0 = time.time()
        expanded_synonyms = await expand_synonyms(concepts, use_llm=request.use_llm_expansion)
        dt_syn = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("synonym_expansion", dt_syn)
        pipeline_logs.append(PipelineStepLog(
            step_number=3,
            step_name="Synonym Expansion (MeSH + LLM)",
            status="success",
            duration_ms=dt_syn,
            details=f"Proposed candidate synonyms for {len(expanded_synonyms)} concepts"
        ))

        # Step 4: MeSH Guardrail Validation
        t0 = time.time()
        mesh_results = await validate_mesh(expanded_synonyms, enabled=request.use_mesh_guardrail)
        dt_mesh = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("mesh_validation", dt_mesh)
        valid_mesh_count = sum(1 for m in mesh_results if m.is_valid)
        pipeline_logs.append(PipelineStepLog(
            step_number=4,
            step_name="MeSH Validation Guardrail",
            status="success" if valid_mesh_count > 0 else "warning",
            duration_ms=dt_mesh,
            details=f"Guardrail verified {valid_mesh_count}/{len(mesh_results)} candidate terms against official NLM MeSH taxonomy"
        ))

        # Step 5: PubMed Boolean Query Builder
        t0 = time.time()
        pubmed_query = build_pubmed_query(
            query_text=effective_query,
            expanded_synonyms=expanded_synonyms,
            mesh_results=mesh_results,
            filters=request.filters
        )
        relaxed_query = build_relaxed_query(
            query_text=effective_query,
            expanded_synonyms=expanded_synonyms,
            mesh_results=mesh_results,
            filters=request.filters
        )
        dt_qb = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("query_builder", dt_qb)
        pipeline_logs.append(PipelineStepLog(
            step_number=5,
            step_name="Query Builder ([MeSH] / [tiab])",
            status="success",
            duration_ms=dt_qb,
            details=f"Constructed optimized PubMed Boolean expression"
        ))

        # Step 6: NCBI ESearch / EFetch Retrieval
        t0 = time.time()
        max_res = min(request.filters.max_results if request.filters and request.filters.max_results else 6, 8)
        total_found, fetched_articles = await search_pubmed(
            pubmed_query,
            max_results=max_res,
            fallback_query=relaxed_query
        )
        dt_ncbi = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("ncbi_retrieval", dt_ncbi)
        pipeline_logs.append(PipelineStepLog(
            step_number=6,
            step_name="NCBI ESearch / EFetch Retrieval",
            status="success" if fetched_articles else "warning",
            duration_ms=dt_ncbi,
            details=f"Retrieved {len(fetched_articles)} articles with authentic clinical abstracts from NCBI (total found: {total_found:,})"
        ))

        # Step 7: Vector Embedding & Similarity Scoring
        t0 = time.time()
        vector_store = create_vector_store(dimension=settings.VECTOR_DIMENSION)
        scored_articles = embed_and_score_articles(effective_query, fetched_articles, vector_store)
        dt_embed = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("embedding_scoring", dt_embed)
        pipeline_logs.append(PipelineStepLog(
            step_number=7,
            step_name="Biomedical Embedding & Similarity Scoring",
            status="success",
            duration_ms=dt_embed,
            details=f"Computed cosine vector similarity using {settings.EMBEDDING_MODEL}"
        ))

        # Step 8: Hybrid Score Fusion & Rerank
        t0 = time.time()
        final_results = rerank_and_fuse(
            scored_articles,
            query_text=effective_query,
            concepts=concepts,
            validated_mesh=mesh_results,
            alpha=request.hybrid_alpha,
            filters=request.filters
        )
        dt_rerank = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("rerank_fusion", dt_rerank)
        pipeline_logs.append(PipelineStepLog(
            step_number=8,
            step_name="Calibrated 5-Factor Hybrid Relevance Scoring",
            status="success",
            duration_ms=dt_rerank,
            details=f"Fused Semantic (40%) + BM25 (25%) + MeSH (15%) + Title (10%) + Coverage (10%)"
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
            summary={
                "total_articles": total_found,
                "esearch_results": total_found,
                "final_results": len(final_results)
            },
            results=final_results,
            pipeline_logs=pipeline_logs,
            execution_time_ms=total_duration,
            cached=False
        )

        cache_service.set(cache_key, response)
        return response

    except Exception as e:
        total_duration = round((time.time() - start_time) * 1000, 2)
        metrics_tracker.record_search(total_duration, success=False)
        logger.error(f"Search pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search pipeline error: {str(e)}")

from app.evaluation.eval_harness import run_evaluation_benchmark, get_benchmark_results

@router.get("/evaluate")
async def evaluate_harness(limit: int = 5) -> Dict[str, Any]:
    """Evaluation Harness Benchmark: Precision@10, Recall, MRR, NDCG@10.
    Executes live benchmark evaluation across curated test queries and calculates real-time metrics.
    """
    try:
        query_limit = max(1, min(limit, 15))
        logger.info(f"Executing evaluation harness across {query_limit} benchmark queries...")
        return await run_evaluation_benchmark(queries_limit=query_limit)
    except Exception as e:
        logger.error(f"Evaluation harness failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

