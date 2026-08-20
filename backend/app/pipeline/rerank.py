from typing import List, Optional
from app.models.schemas import Article, SearchFilter

def rerank_and_fuse(
    articles: List[Article],
    alpha: float = 0.6,
    filters: Optional[SearchFilter] = None
) -> List[Article]:
    """Step 8: Execute Reciprocal Rank Fusion (RRF) & Weighted Hybrid Reranking."""
    if not articles:
        return []

    lexical_sorted = sorted(articles, key=lambda a: a.bm25_score, reverse=True)
    lexical_rank_map = {art.pmid: rank + 1 for rank, art in enumerate(lexical_sorted)}

    semantic_sorted = sorted(articles, key=lambda a: a.semantic_score, reverse=True)
    semantic_rank_map = {art.pmid: rank + 1 for rank, art in enumerate(semantic_sorted)}

    k = 60  # RRF constant factor

    for art in articles:
        lex_rank = lexical_rank_map.get(art.pmid, len(articles))
        sem_rank = semantic_rank_map.get(art.pmid, len(articles))

        # Reciprocal Rank Fusion
        rrf_score = (1.0 / (k + lex_rank)) + (1.0 / (k + sem_rank))

        # Weighted Hybrid Linear Combination
        combined_score = (alpha * art.semantic_score) + ((1.0 - alpha) * art.bm25_score)
        art.final_score = round(float(combined_score), 3)

        art.explanation = (
            f"Semantic Score: {art.semantic_score:.3f} | "
            f"BM25 Score: {art.bm25_score:.3f} | "
            f"Hybrid Score: {art.final_score:.3f}"
        )

    ranked_articles = sorted(articles, key=lambda a: a.final_score, reverse=True)

    if filters and filters.min_score > 0:
        ranked_articles = [a for a in ranked_articles if a.final_score >= filters.min_score]

    return ranked_articles
