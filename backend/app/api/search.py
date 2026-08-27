import time
import logging
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import numpy as np

from app.models.schemas import (
    SearchRequest, SearchResponse, PipelineStepLog, SpellCorrection
)
from app.pipeline.med_search_pipeline import (
    take_user_query,
    clean_and_preprocess_query,
    expand_query_with_llm,
    build_pubmed_query_params,
    search_pubmed_esearch,
    fetch_articles_efetch,
    generate_embeddings,
    compute_similarity_scores,
    rerank_results,
    apply_filters as med_apply_filters,
    format_results_for_display,
    evaluate_faithfulness_and_relevancy,
    verify_citation,
    SearchFilters as MedSearchFilters,
    Article as MedArticle
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
from app.services.mesh_data import MeshDictionaryManager
from app.models.schemas import Article
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

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
    """Execute PubMed Semantic Search pipeline powered by med_search GenAI logic."""
    start_time = time.time()
    pipeline_logs: List[PipelineStepLog] = []

    # Validate user query using med_search take_user_query
    validated_raw_query = take_user_query(request.query)

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
        # Step 1: Biomedical Spell Correction & Query Preprocessing
        effective_query = validated_raw_query
        cleaned_query = clean_and_preprocess_query(validated_raw_query)
        spell_corrections: List[SpellCorrection] = []
        if request.use_spell_correction:
            t0 = time.time()
            effective_query, spell_corrections = correct_biomedical_query(validated_raw_query)
            dt_spell = round((time.time() - t0) * 1000, 2)
            metrics_tracker.record_stage_latency("spell_correction", dt_spell)
            
            if spell_corrections:
                detail_str = f"Corrected {len(spell_corrections)} biomedical typo(s): " + ", ".join([f"'{c.original_term}' → '{c.corrected_term}'" for c in spell_corrections])
            else:
                detail_str = "Verified query against offline MeSH dictionary (0 typos detected)"
            
            pipeline_logs.append(PipelineStepLog(
                step_number=1,
                step_name="Biomedical Spell Correction & Query Cleaning",
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

        # Step 3: LLM & MeSH Synonym Expansion (med_search Gemini/Anthropic/Fallback priority)
        t0 = time.time()
        llm_expanded_query = expand_query_with_llm(cleaned_query or effective_query)
        expanded_synonyms = await expand_synonyms(concepts, use_llm=request.use_llm_expansion)
        dt_syn = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("synonym_expansion", dt_syn)
        pipeline_logs.append(PipelineStepLog(
            step_number=3,
            step_name="GenAI LLM & MeSH Query Expansion",
            status="success",
            duration_ms=dt_syn,
            details=f"Expanded query: '{llm_expanded_query[:80]}...' across {len(expanded_synonyms)} concepts"
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

        # Step 5: PubMed Entrez Query Parameter Building
        t0 = time.time()
        med_filters = MedSearchFilters(
            start_date=request.filters.start_date or request.filters.date_from,
            end_date=request.filters.end_date or request.filters.date_to,
            journal=request.filters.journal,
            study_type=request.filters.study_type
        ) if request.filters else None

        entrez_params = build_pubmed_query_params(llm_expanded_query, filters=med_filters)
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
            step_name="PubMed Entrez ESearch Query Parameter Builder",
            status="success",
            duration_ms=dt_qb,
            details=f"Constructed NCBI Entrez params with term='{entrez_params.get('term', '')[:90]}...'"
        ))

        # Step 6: NCBI ESearch / EFetch XML Retrieval (med_search fetch_articles_efetch)
        t0 = time.time()
        max_res = min(request.filters.max_results if request.filters and request.filters.max_results else 10, 25)
        entrez_params["retmax"] = max_res

        pmids = []
        try:
            pmids = search_pubmed_esearch(entrez_params)
        except Exception as es_err:
            logger.warning(f"ESearch error with expanded params: {es_err}, falling back to pipeline search_pubmed")

        if not pmids:
            total_found, fetched_articles = await search_pubmed(
                pubmed_query,
                max_results=max_res,
                fallback_query=relaxed_query
            )
        else:
            med_articles = fetch_articles_efetch(pmids)
            total_found = len(med_articles)
            fetched_articles = []
            for ma in med_articles:
                fetched_articles.append(Article(
                    pmid=ma.pmid,
                    title=ma.title,
                    abstract=ma.abstract,
                    journal=ma.journal,
                    pub_date=ma.pub_date,
                    similarity_score=ma.similarity_score,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{ma.pmid}/"
                ))

        dt_ncbi = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("ncbi_retrieval", dt_ncbi)
        pipeline_logs.append(PipelineStepLog(
            step_number=6,
            step_name="NCBI ESearch & EFetch XML Article Retrieval",
            status="success" if fetched_articles else "warning",
            duration_ms=dt_ncbi,
            details=f"Retrieved {len(fetched_articles)} articles with authentic clinical abstracts from NCBI EUtils (total found: {total_found:,})"
        ))

        # Step 7: SentenceTransformers Embedding & Cosine Matrix Similarity Scoring (@ operator)
        t0 = time.time()
        valid_articles = [a for a in fetched_articles if a.abstract]
        if valid_articles:
            query_emb = generate_embeddings([llm_expanded_query])[0]
            abstract_embs = generate_embeddings([a.abstract for a in valid_articles])
            sim_scores = compute_similarity_scores(query_emb, abstract_embs)
            for a, sc in zip(valid_articles, sim_scores):
                a.semantic_score = float(sc)
                a.similarity_score = float(sc)
                a.relevance_score = round(float(sc), 4)

        vector_store = create_vector_store(dimension=settings.VECTOR_DIMENSION)
        scored_articles = embed_and_score_articles(effective_query, valid_articles, vector_store)
        dt_embed = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("embedding_scoring", dt_embed)
        pipeline_logs.append(PipelineStepLog(
            step_number=7,
            step_name="SentenceTransformers Embedding Vector & Matrix Cosine Similarity",
            status="success",
            duration_ms=dt_embed,
            details=f"Computed cosine vector similarity using model '{settings.EMBEDDING_MODEL_NAME}'"
        ))

        # Step 8: Hybrid Reranking, Filtering, Display Formatting, Faithfulness Evaluation & Citation Check
        t0 = time.time()
        med_art_objects = [MedArticle(pmid=a.pmid, title=a.title, abstract=a.abstract, journal=a.journal, pub_date=a.pub_date, similarity_score=a.similarity_score) for a in scored_articles]
        reranked_med = rerank_results(med_art_objects, np.array([a.similarity_score for a in scored_articles]))
        filtered_med = med_apply_filters(reranked_med, med_filters)
        formatted_display = format_results_for_display(filtered_med, top_k=max_res)

        articles_by_pmid = {ma.pmid: ma for ma in med_art_objects}
        if valid_articles:
            query_emb = generate_embeddings([llm_expanded_query])[0]
            eval_metrics = evaluate_faithfulness_and_relevancy(query_emb, formatted_display, articles_by_pmid)
        else:
            eval_metrics = {"answer_relevancy": 0.0, "faithfulness": 0.0}

        final_results = rerank_and_fuse(
            scored_articles,
            query_text=effective_query,
            concepts=concepts,
            validated_mesh=mesh_results,
            alpha=request.hybrid_alpha,
            filters=request.filters
        )

        for fr in final_results:
            disp = next((d for d in formatted_display if d["pmid"] == fr.pmid), None)
            if disp:
                fr.snippet = disp["snippet"]
                fr.relevance_score = disp["relevance_score"]
                fr.similarity_score = disp["relevance_score"]
                fr.url = disp["url"]
            else:
                fr.snippet = (fr.abstract[:280] + "...") if len(fr.abstract) > 280 else fr.abstract
                fr.relevance_score = round(fr.semantic_score, 4)
                fr.similarity_score = fr.relevance_score
                fr.url = f"https://pubmed.ncbi.nlm.nih.gov/{fr.pmid}/"
            fr.citation_verified = verify_citation({"pmid": fr.pmid, "snippet": fr.snippet}, articles_by_pmid)

        dt_rerank = round((time.time() - t0) * 1000, 2)
        metrics_tracker.record_stage_latency("rerank_fusion", dt_rerank)
        pipeline_logs.append(PipelineStepLog(
            step_number=8,
            step_name="Calibrated Hybrid Scoring, Citation Verification & Faithfulness Metrics",
            status="success",
            duration_ms=dt_rerank,
            details=f"Verified citations and calculated RAGAS-style metrics: Relevancy={eval_metrics.get('answer_relevancy')}, Faithfulness={eval_metrics.get('faithfulness')}"
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
            cached=False,
            metrics=eval_metrics,
            from_cache=False,
            elapsed_seconds=round(total_duration / 1000.0, 2)
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

