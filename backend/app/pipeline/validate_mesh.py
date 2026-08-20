# pyrefly: ignore [missing-import]
import httpx
import logging
from typing import List, Dict, Optional
from app.models.schemas import ExpandedSynonym, MeSHValidationResult

logger = logging.getLogger(__name__)

# Official MeSH Index Cache for fast local guardrail validation
OFFICIAL_MESH_DATABASE: Dict[str, Dict] = {
    "Metformin": {
        "id": "C004559",
        "heading": "Metformin",
        "tree": ["D02.065.045"],
        "status_note": "D004559"
    },
    "Diabetes Mellitus, Type 2": {
        "id": "C003920",
        "heading": "Diabetes Mellitus, Type 2",
        "tree": ["C18.452.394.750.149"],
        "status_note": "D003920"
    },
    "Glucagon-Like Peptide-1 Receptor Agonists": {
        "id": "D000077543",
        "heading": "Glucagon-Like Peptide-1 Receptor Agonists",
        "tree": ["D27.505.519.389.380"],
        "status_note": "D000077543"
    },
    "Diabetes Mellitus": {
        "id": "D003920",
        "heading": "Diabetes Mellitus",
        "tree": ["C18.452.394.750"],
        "status_note": "D003920"
    },
    "Cardiovascular Diseases": {
        "id": "D002318",
        "heading": "Cardiovascular Diseases",
        "tree": ["C14"],
        "status_note": "D002318"
    },
    "Sodium-Glucose Transporter 2 Inhibitors": {
        "id": "D000077203",
        "heading": "Sodium-Glucose Transporter 2 Inhibitors",
        "tree": ["D27.505.519.389.740"],
        "status_note": "D000077203"
    },
    "Melanoma": {
        "id": "D008545",
        "heading": "Melanoma",
        "tree": ["C04.557.465.625.650"],
        "status_note": "D008545"
    },
    "Anemia, Sickle Cell": {
        "id": "D000755",
        "heading": "Anemia, Sickle Cell",
        "tree": ["C15.378.140.100"],
        "status_note": "D000755"
    },
    "Clustered Regularly Interspaced Short Palindromic Repeats": {
        "id": "D000078326",
        "heading": "Clustered Regularly Interspaced Short Palindromic Repeats",
        "tree": ["G05.360.080"],
        "status_note": "D000078326"
    }
}

async def validate_mesh(expanded_synonyms: List[ExpandedSynonym], enabled: bool = True) -> List[MeSHValidationResult]:
    """Step 4: MeSH Guardrail: Validate candidate terms against MeSH taxonomy to filter hallucinations."""
    results: List[MeSHValidationResult] = []

    if not enabled:
        for item in expanded_synonyms:
            results.append(MeSHValidationResult(
                original_term=item.term,
                mesh_heading=item.mesh_heading or item.term,
                is_valid=True,
                status_note="Guardrail disabled by user"
            ))
        return results

    for item in expanded_synonyms:
        candidate = item.mesh_heading or item.term
        matched = None

        for heading, data in OFFICIAL_MESH_DATABASE.items():
            if heading.lower() == candidate.lower() or candidate.lower() in heading.lower():
                matched = data
                break

        if matched:
            results.append(MeSHValidationResult(
                original_term=item.term,
                mesh_unique_id=matched["id"],
                mesh_heading=matched["heading"],
                tree_numbers=matched["tree"],
                is_valid=True,
                status_note=matched.get("status_note", "D004559")
            ))
        else:
            mesh_record = await _query_ncbi_mesh_api(candidate)
            if mesh_record:
                results.append(MeSHValidationResult(
                    original_term=item.term,
                    mesh_unique_id=mesh_record.get("id"),
                    mesh_heading=mesh_record.get("heading"),
                    tree_numbers=mesh_record.get("tree", []),
                    is_valid=True,
                    status_note="Verified via NCBI MeSH API"
                ))
            else:
                results.append(MeSHValidationResult(
                    original_term=item.term,
                    mesh_heading=candidate,
                    is_valid=False,
                    status_note="Not an official MeSH Heading (used in Title/Abstract keywords only)"
                ))

    return results

async def _query_ncbi_mesh_api(term: str) -> Optional[Dict]:
    """Query NCBI EUtilities for MeSH term verification."""
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "mesh",
            "term": f"{term}[MeSH Terms]",
            "retmode": "json",
            "retmax": 1
        }
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                id_list = data.get("esearchresult", {}).get("idlist", [])
                if id_list:
                    return {"id": id_list[0], "heading": term, "tree": []}
    except Exception as e:
        logger.debug(f"NCBI MeSH API lookup failed for '{term}': {e}")
    return None
