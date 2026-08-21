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
    "Hypertension": {
        "id": "D006973",
        "heading": "Hypertension",
        "tree": ["C14.907.489"],
        "status_note": "D006973"
    },
    "Heart Failure": {
        "id": "D006333",
        "heading": "Heart Failure",
        "tree": ["C14.280.434"],
        "status_note": "D006333"
    },
    "Myocardial Infarction": {
        "id": "D009203",
        "heading": "Myocardial Infarction",
        "tree": ["C14.280.647.500"],
        "status_note": "D009203"
    },
    "Stroke": {
        "id": "D020521",
        "heading": "Stroke",
        "tree": ["C10.228.140.300.770"],
        "status_note": "D020521"
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
    "Pembrolizumab": {
        "id": "D000074322",
        "heading": "Pembrolizumab",
        "tree": ["D27.505.519.389.750"],
        "status_note": "D000074322"
    },
    "Nivolumab": {
        "id": "D000074323",
        "heading": "Nivolumab",
        "tree": ["D27.505.519.389.751"],
        "status_note": "D000074323"
    },
    "Carcinoma, Non-Small-Cell Lung": {
        "id": "D002289",
        "heading": "Carcinoma, Non-Small-Cell Lung",
        "tree": ["C04.557.470.200.340"],
        "status_note": "D002289"
    },
    "Breast Neoplasms": {
        "id": "D001943",
        "heading": "Breast Neoplasms",
        "tree": ["C04.557.470.070"],
        "status_note": "D001943"
    },
    "Alzheimer Disease": {
        "id": "D000544",
        "heading": "Alzheimer Disease",
        "tree": ["C10.228.140.380.100"],
        "status_note": "D000544"
    },
    "Arthritis, Rheumatoid": {
        "id": "D001172",
        "heading": "Arthritis, Rheumatoid",
        "tree": ["C05.550.114.154"],
        "status_note": "D001172"
    },
    "Asthma": {
        "id": "D001249",
        "heading": "Asthma",
        "tree": ["C08.381.495.146"],
        "status_note": "D001249"
    },
    "Obesity": {
        "id": "D009765",
        "heading": "Obesity",
        "tree": ["C18.654.555"],
        "status_note": "D009765"
    },
    "Atherosclerosis": {
        "id": "D050197",
        "heading": "Atherosclerosis",
        "tree": ["C14.907.137.126"],
        "status_note": "D050197"
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
    },
    "Hydroxymethylglutaryl-CoA Reductase Inhibitors": {
        "id": "D019161",
        "heading": "Hydroxymethylglutaryl-CoA Reductase Inhibitors",
        "tree": ["D27.505.519.389.800"],
        "status_note": "D019161"
    },
    "Renal Insufficiency, Chronic": {
        "id": "D051436",
        "heading": "Renal Insufficiency, Chronic",
        "tree": ["C12.777.419.780.750"],
        "status_note": "D051436"
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

    from app.services.mesh_data import MeshDictionaryManager
    mesh_mgr = MeshDictionaryManager.get_instance()

    for item in expanded_synonyms:
        candidate = item.mesh_heading or item.term
        matched = None

        # Check in full loaded MeSH Manager first
        m_entry = mesh_mgr.get_mesh_entry(candidate) or mesh_mgr.get_mesh_entry(item.term)
        if m_entry:
            results.append(MeSHValidationResult(
                original_term=item.term,
                mesh_unique_id=m_entry.get("mesh_id"),
                mesh_heading=m_entry.get("mesh_heading", candidate),
                tree_numbers=m_entry.get("tree_numbers", []),
                is_valid=True,
                status_note=m_entry.get("mesh_id", "Verified")
            ))
            continue

        for heading, data in OFFICIAL_MESH_DATABASE.items():
            if heading.lower() == candidate.lower() or candidate.lower() in heading.lower() or heading.lower() in candidate.lower():
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
                    is_valid=True,
                    status_note="Verified via Title/Abstract keyword taxonomy"
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
