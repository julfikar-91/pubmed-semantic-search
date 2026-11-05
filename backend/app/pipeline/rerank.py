import re
from typing import List, Optional
from app.models.schemas import Article, SearchFilter, ExtractedConcept, MeSHValidationResult

def _normalize_score(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamps and normalizes a score to [0.0, 1.0]."""
    return max(0.0, min(1.0, (val - min_val) / (max_val - min_val + 1e-9)))

def rerank_and_fuse(
    articles: List[Article],
    query_text: str = "",
    concepts: Optional[List[ExtractedConcept]] = None,
    validated_mesh: Optional[List[MeSHValidationResult]] = None,
    alpha: float = 0.6,
    filters: Optional[SearchFilter] = None
) -> List[Article]:
    """
    Step 8: Calibrated 5-Factor Hybrid Relevance Scoring:
    FinalScore = 0.40 * SemanticSim + 0.25 * BM25Score + 0.15 * MeSHMatch + 0.10 * TitleRel + 0.10 * EntityCoverage
    """
    if not articles:
        return []

    # `alpha` remains accepted for backwards-compatible API calls.  The
    # reference architecture specifies the fixed 40/25/15/10/10 fusion below,
    # so it deliberately does not alter those published weights.

    # Extract target search terms & MeSH headings
    query_tokens = set(re.findall(r"\w+", query_text.lower())) if query_text else set()
    concept_phrases = [c.text.lower() for c in (concepts or [])]
    target_mesh_set = {
        m.mesh_heading.lower() for m in (validated_mesh or [])
        if m.is_valid and m.mesh_heading
    }

    for art in articles:
        t_lower = art.title.lower()
        a_lower = art.abstract.lower()
        comb_text = f"{t_lower} {a_lower}"
        art_mesh_lower = [m.lower() for m in art.mesh_terms]

        # 1. Semantic Similarity Score (0.0 to 1.0)
        sem_score = _normalize_score(art.semantic_score, min_val=0.0, max_val=1.0)

        # 2. MeSH Concept Match Score
        mesh_score = 0.0
        if target_mesh_set:
            mesh_matches = []
            for target_mesh in target_mesh_set:
                if target_mesh in art_mesh_lower:
                    mesh_matches.append(1.0)
                elif any(target_mesh in mesh or mesh in target_mesh for mesh in art_mesh_lower):
                    mesh_matches.append(0.5)
                else:
                    mesh_matches.append(0.0)
            mesh_score = sum(mesh_matches) / len(target_mesh_set)

        # 3. Title Relevance Score
        title_score = 0.0
        if query_text and query_text.lower() in t_lower:
            title_score = 1.0
        elif concept_phrases:
            matched_phrases = sum(1 for cp in concept_phrases if cp in t_lower)
            matched_tokens = sum(1 for tok in query_tokens if tok in t_lower)
            token_ratio = matched_tokens / max(1, len(query_tokens))
            title_score = min(1.0, (matched_phrases * 0.5) + (token_ratio * 0.5))
        elif query_tokens:
            matched_tokens = sum(1 for tok in query_tokens if tok in t_lower)
            title_score = matched_tokens / max(1, len(query_tokens))

        # 4. Multi-Entity / Concept Coverage Score.  Do not award a default
        # score: an article must cover an extracted query concept to earn it.
        coverage_score = 0.0
        if concept_phrases:
            covered = sum(
                1 for cp in concept_phrases
                if cp in comb_text or any(cp in mesh for mesh in art_mesh_lower)
            )
            coverage_score = covered / len(concept_phrases)

        # 6. Publication Type Prior Adjustment
        pub_boost = 0.0
        pub_types_str = " ".join(art.pub_types).lower()
        if any(pt in pub_types_str for pt in ["systematic review", "meta-analysis", "practice guideline", "consensus"]):
            pub_boost = 0.05
        elif any(pt in pub_types_str for pt in ["clinical trial", "randomized controlled trial", "multicenter study"]):
            pub_boost = 0.03
        elif "case reports" in pub_types_str:
            pub_boost = -0.04

        # Combine real hybrid feature scores
        bm25_val = max(0.0, float(art.bm25_score))
        hybrid_score = (
            (0.40 * sem_score) +
            (0.25 * bm25_val) +
            (0.15 * mesh_score) +
            (0.10 * title_score) +
            (0.10 * coverage_score) +
            pub_boost
        )

        art.final_score = round(float(max(0.0, min(1.0, hybrid_score))), 3)
        art.explanation = (
            f"Semantic: {sem_score:.2f} (40%) | "
            f"BM25: {bm25_val:.2f} (25%) | "
            f"MeSH: {mesh_score:.2f} (15%) | "
            f"Title: {title_score:.2f} (10%) | "
            f"Coverage: {coverage_score:.2f} (10%)"
        )


    # Sort strictly by calibrated final hybrid score
    ranked_articles = sorted(articles, key=lambda a: a.final_score, reverse=True)

    if filters and filters.min_score > 0:
        ranked_articles = [a for a in ranked_articles if a.final_score >= filters.min_score]

    return ranked_articles


def apply_final_filters(articles: List[Article], filters: Optional[SearchFilter]) -> List[Article]:
    """Defensively apply every UI filter after hybrid ranking.

    PubMed receives the same restrictions in the Boolean query, but applying
    them once more here guarantees that cached or partially populated records
    never leak outside the user's selected journal, publication type, date, or
    score range.
    """
    if not filters:
        return articles

    def publication_year(value: str) -> Optional[int]:
        match = re.search(r"\b(18|19|20|21)\d{2}\b", value or "")
        return int(match.group(0)) if match else None

    start_year = publication_year(filters.date_from or filters.start_date or "")
    end_year = publication_year(filters.date_to or filters.end_date or "")
    requested_types = {item.lower() for item in (filters.pub_types or [])}
    if filters.study_type:
        requested_types.add(filters.study_type.lower())

    filtered: List[Article] = []
    for article in articles:
        if filters.min_score > 0 and article.final_score < filters.min_score:
            continue
        if filters.journal and filters.journal.lower() not in article.journal.lower():
            continue
        if requested_types:
            article_types = {item.lower() for item in article.pub_types}
            if not any(
                requested in article_type or article_type in requested
                for requested in requested_types
                for article_type in article_types
            ):
                continue
        year = publication_year(article.pub_date)
        if start_year is not None and (year is None or year < start_year):
            continue
        if end_year is not None and (year is None or year > end_year):
            continue
        filtered.append(article)
    return filtered

