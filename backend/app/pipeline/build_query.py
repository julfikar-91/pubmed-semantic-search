from typing import List, Optional
from app.models.schemas import ExpandedSynonym, MeSHValidationResult, SearchFilter

def build_pubmed_query(
    query_text: str,
    expanded_synonyms: List[ExpandedSynonym],
    mesh_results: List[MeSHValidationResult],
    filters: Optional[SearchFilter] = None
) -> str:
    """Step 5: Build an optimized boolean PubMed query string using MeSH terms ([MeSH]) and synonyms ([tiab])."""
    concept_blocks: List[str] = []
    mesh_map = {m.original_term: m for m in mesh_results}

    for item in expanded_synonyms:
        term_parts: List[str] = []
        mesh_info = mesh_map.get(item.term)

        if mesh_info and mesh_info.is_valid and mesh_info.mesh_heading:
            term_parts.append(f'"{mesh_info.mesh_heading}"[MeSH]')

        for syn in item.synonyms:
            clean_syn = syn.strip().replace('"', '')
            if clean_syn:
                term_parts.append(f'{clean_syn}[tiab]')

        if term_parts:
            unique_parts = list(dict.fromkeys(term_parts))
            block = f"({' OR '.join(unique_parts)})"
            concept_blocks.append(block)

    if not concept_blocks:
        clean_query = query_text.strip().replace('"', '')
        query_string = f'"{clean_query}"[tiab]'
    else:
        query_string = " AND ".join(concept_blocks)

    if filters:
        filter_parts: List[str] = []
        if filters.pub_types:
            pub_type_terms = [f'"{pt}"[Publication Type]' for pt in filters.pub_types]
            if pub_type_terms:
                filter_parts.append(f"({' OR '.join(pub_type_terms)})")

        if filters.date_from or filters.date_to:
            date_from_str = filters.date_from.replace("-", "/").replace(".", "/") if filters.date_from else "1900/01/01"
            date_to_str = filters.date_to.replace("-", "/").replace(".", "/") if filters.date_to else "3000/12/31"
            filter_parts.append(f'"{date_from_str}"[Date - Publication] : "{date_to_str}"[Date - Publication]')

        if filter_parts:
            query_string += " AND " + " AND ".join(filter_parts)

    return query_string
