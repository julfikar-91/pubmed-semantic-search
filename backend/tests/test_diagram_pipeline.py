"""Regression tests for the approved eight-stage pipeline diagram."""

from app.api import search as search_api
from app.models.schemas import Article, ExpandedSynonym, ExtractedConcept, MeSHValidationResult, SearchFilter, SearchRequest
from app.pipeline.build_query import build_pubmed_query
from app.pipeline.spell_correct import MODERN_CLINICAL_SUPPLEMENT
from app.pipeline.validate_mesh import _discard_unverified_synonym_candidates
from app.services.mesh_data import MeshDictionaryManager


def test_search_uses_strict_query_once_then_scores_the_candidate_pool(monkeypatch):
    """The free-form legacy query must never replace the strict MeSH query."""
    calls = {}

    async def fake_expand(concepts, use_llm=True):
        return [ExpandedSynonym(term="metformin", synonyms=["metformin", "biguanides"], mesh_heading="Metformin")]

    async def fake_validate(expanded, enabled=True):
        return [MeSHValidationResult(
            original_term="metformin",
            mesh_heading="Metformin",
            mesh_unique_id="D008687",
            is_valid=True,
        )]

    async def fake_search(query, max_results, fallback_query=None):
        calls["query"] = query
        calls["max_results"] = max_results
        calls["fallback_query"] = fallback_query
        return 137, [Article(
            pmid="1",
            title="Metformin in type 2 diabetes",
            abstract="Metformin treatment improves glycemic outcomes in type 2 diabetes patients.",
            journal="Clinical Medicine",
            pub_date="2024",
            mesh_terms=["Metformin"],
            pub_types=["Clinical Trial"],
        )]

    def fake_score(query, articles, vector_store):
        for article in articles:
            article.semantic_score = 0.9
            article.bm25_score = 0.8
            article.lexical_score = 0.8
        return articles

    monkeypatch.setattr(search_api, "expand_synonyms", fake_expand)
    monkeypatch.setattr(search_api, "validate_mesh", fake_validate)
    monkeypatch.setattr(search_api, "search_pubmed", fake_search)
    monkeypatch.setattr(search_api, "embed_and_score_articles", fake_score)
    monkeypatch.setattr(search_api, "extract_concepts", lambda _: [ExtractedConcept(text="metformin", category="Drug")])
    monkeypatch.setattr(search_api, "correct_biomedical_query", lambda query: (query, []))

    search_api.cache_service.clear()
    request = SearchRequest(
        query="metformin for diabetes",
        use_llm_expansion=False,
        filters=SearchFilter(max_results=5, pub_types=["Clinical Trial"]),
    )
    # Every patched I/O dependency completes immediately, so directly advancing
    # the coroutine avoids opening an OS event loop in the Windows test sandbox.
    pipeline = search_api.perform_search(request)
    try:
        pipeline.send(None)
    except StopIteration as completed:
        response = completed.value
    else:
        raise AssertionError("The mocked pipeline unexpectedly awaited external I/O")

    assert len(response.pipeline_logs) == 8
    assert calls["query"] == response.pubmed_query
    assert '"Metformin"[MeSH]' in calls["query"]
    assert calls["max_results"] == search_api.CANDIDATE_POOL_SIZE
    assert len(response.results) == 1
    assert response.results[0].relevance_score == response.results[0].final_score
    assert response.results[0].similarity_score == response.results[0].semantic_score
    assert response.results[0].citation_verified is True

    # The same orchestrated request returns from the Tier-1 query cache before
    # opening any later pipeline stage.
    cached_pipeline = search_api.perform_search(request)
    try:
        cached_pipeline.send(None)
    except StopIteration as completed:
        cached_response = completed.value
    else:
        raise AssertionError("The cached response unexpectedly awaited pipeline I/O")
    assert cached_response.cached is True
    assert cached_response.from_cache is True
    search_api.cache_service.clear()


def test_final_filters_do_not_award_unmatched_mesh_or_concept_credit():
    article = Article(
        pmid="1",
        title="Unrelated hypertension paper",
        abstract="A report about hypertension.",
        journal="Journal A",
        pub_date="2021",
        semantic_score=0.5,
        bm25_score=0.5,
        mesh_terms=["Hypertension"],
        pub_types=["Review"],
    )
    concept = ExtractedConcept(text="metformin", category="Drug")
    mesh = MeSHValidationResult(original_term="metformin", mesh_heading="Metformin", is_valid=True)

    ranked = search_api.rerank_and_fuse([article], "metformin", [concept], [mesh])
    assert ranked[0].final_score == 0.325  # 40% semantic + 25% BM25 only

    filtered = search_api.apply_final_filters(
        ranked,
        SearchFilter(date_from="2022/01/01", pub_types=["Clinical Trial"], max_results=5),
    )
    assert filtered == []


def test_rejected_mesh_candidate_cannot_put_llm_synonyms_into_strict_query():
    expanded = [ExpandedSynonym(
        term="invented medicine",
        synonyms=["invented medicine", "metformin", "imaginary molecule"],
        mesh_heading="Imaginary Molecule",
    )]
    rejected = [MeSHValidationResult(
        original_term="invented medicine",
        mesh_heading="Imaginary Molecule",
        is_valid=False,
    )]

    query = build_pubmed_query("invented medicine", expanded, rejected)
    assert '"invented medicine"[tiab]' in query
    assert "metformin[tiab]" not in query
    assert '"imaginary molecule"[tiab]' not in query


def test_guardrail_discards_unknown_llm_synonym_before_query_builder():
    item = ExpandedSynonym(
        term="metformin",
        synonyms=["metformin", "biguanides", "imaginary molecule"],
        mesh_heading="Metformin",
    )
    _discard_unverified_synonym_candidates(
        item,
        MeshDictionaryManager.get_instance(),
        MODERN_CLINICAL_SUPPLEMENT,
    )
    assert "metformin" in item.synonyms
    assert "biguanides" in item.synonyms
    assert "imaginary molecule" not in item.synonyms
