import re
from typing import List, Optional
from app.models.schemas import ExpandedSynonym, MeSHValidationResult, SearchFilter

def _clean_inverted_mesh(term: str) -> str:
    """Converts inverted MeSH headings like 'Loss, Weight' -> 'Weight Loss'."""
    term = term.strip().replace('"', '')
    if "," in term:
        parts = [p.strip() for p in term.split(",")]
        if len(parts) == 2 and not any(char.isdigit() for char in parts[1]):
            return f"{parts[1]} {parts[0]}"
    return term

def _format_tiab_term(term: str) -> str:
    """Formats a term for PubMed [tiab] search with quotes for multi-word or special character phrases."""
    clean = term.strip().replace('"', '')
    if not clean:
        return ""
    if " " in clean or "-" in clean or "," in clean:
        return f'"{clean}"[tiab]'
    return f"{clean}[tiab]"

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

        # 1. Official MeSH descriptor tag if validated
        if mesh_info and mesh_info.is_valid and mesh_info.mesh_heading:
            clean_mesh = mesh_info.mesh_heading.strip().replace('"', '')
            term_parts.append(f'"{clean_mesh}"[MeSH]')

        # 2. Always include the primary concept text in [tiab]
        primary_tiab = _format_tiab_term(item.term)
        if primary_tiab:
            term_parts.append(primary_tiab)

        # 3. Add synonym terms with proper phrase quoting and inverted-term normalization
        for syn in item.synonyms:
            cleaned_syn = _clean_inverted_mesh(syn)
            formatted_syn = _format_tiab_term(cleaned_syn)
            if formatted_syn and formatted_syn not in term_parts:
                term_parts.append(formatted_syn)

        if term_parts:
            # Preserve uniqueness and limit to top 5 most specific representations
            unique_parts = list(dict.fromkeys(term_parts))[:5]
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

        date_from_val = filters.date_from.strip() if filters.date_from else ""
        date_to_val = filters.date_to.strip() if filters.date_to else ""

        if date_from_val or date_to_val:
            if len(date_from_val) == 4 and date_from_val.isdigit():
                date_from_str = f"{date_from_val}/01/01"
            else:
                date_from_str = date_from_val.replace("-", "/").replace(".", "/") if date_from_val else "1900/01/01"

            if len(date_to_val) == 4 and date_to_val.isdigit():
                date_to_str = f"{date_to_val}/12/31"
            else:
                date_to_str = date_to_val.replace("-", "/").replace(".", "/") if date_to_val else "3000/12/31"

            filter_parts.append(f'"{date_from_str}"[Date - Publication] : "{date_to_str}"[Date - Publication]')

        if filter_parts:
            query_string += " AND " + " AND ".join(filter_parts)

    return query_string

def build_relaxed_query(
    query_text: str,
    expanded_synonyms: List[ExpandedSynonym],
    mesh_results: List[MeSHValidationResult],
    filters: Optional[SearchFilter] = None
) -> str:
    """Builds a relaxed fallback query focusing on the top 2 key concepts to prevent empty result sets."""
    if not expanded_synonyms:
        clean_q = re.sub(r"[^\w\s-]", " ", query_text).strip()
        return clean_q

    # Take the top 2 primary concepts
    top_synonyms = expanded_synonyms[:2]
    return build_pubmed_query(query_text, top_synonyms, mesh_results, filters=filters)

