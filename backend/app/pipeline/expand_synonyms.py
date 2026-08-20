import json
import logging
from typing import List, Dict
from app.config import settings
from app.models.schemas import ExtractedConcept, ExpandedSynonym

logger = logging.getLogger(__name__)

# Curated Medical Concept Synonym & MeSH Dictionary Fallback
MEDICAL_ONTOLOGY_MAP: Dict[str, Dict[str, str]] = {
    "metformin": {
        "synonyms": ["biguanides", "dimethylbiguanide"],
        "mesh": "Metformin"
    },
    "type 2 diabetes": {
        "synonyms": ["noninsulin dependent diabetes mellitus", "T2D", "T2DM"],
        "mesh": "Diabetes Mellitus, Type 2"
    },
    "glp-1": {
        "synonyms": ["glucagon-like peptide 1", "GLP-1 receptor agonist", "GLP-1 RA", "incretin mimetic"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "glp-1 receptor agonists": {
        "synonyms": ["glucagon-like peptide 1 agonists", "GLP-1 RA", "semaglutide", "liraglutide"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "diabetes": {
        "synonyms": ["diabetes mellitus", "diabetic", "hyperglycemia"],
        "mesh": "Diabetes Mellitus"
    },
    "cardiovascular disease": {
        "synonyms": ["CVD", "heart disease", "cardiovascular outcomes", "cardiac events", "MACE"],
        "mesh": "Cardiovascular Diseases"
    },
    "sglt-2": {
        "synonyms": ["SGLT2 inhibitors", "sodium-glucose cotransporter 2 inhibitors", "empagliflozin", "dapagliflozin"],
        "mesh": "Sodium-Glucose Transporter 2 Inhibitors"
    },
    "melanoma": {
        "synonyms": ["cutaneous melanoma", "malignant melanoma", "melanoma cancer"],
        "mesh": "Melanoma"
    },
    "sickle cell": {
        "synonyms": ["sickle cell anemia", "sickle cell disease", "HbS disease"],
        "mesh": "Anemia, Sickle Cell"
    },
    "crispr": {
        "synonyms": ["CRISPR-Cas9", "clustered regularly interspaced short palindromic repeats", "gene editing"],
        "mesh": "Clustered Regularly Interspaced Short Palindromic Repeats"
    }
}

async def expand_synonyms(concepts: List[ExtractedConcept], use_llm: bool = True) -> List[ExpandedSynonym]:
    """Step 3: Expand extracted concepts with medical synonyms and MeSH candidate terms using LLM or Medical Ontology."""
    expanded_list: List[ExpandedSynonym] = []

    for concept in concepts:
        raw_text = concept.text.strip().lower()
        
        dict_match = None
        for k, v in MEDICAL_ONTOLOGY_MAP.items():
            if k in raw_text or raw_text in k:
                dict_match = v
                break

        synonyms = []
        mesh_candidate = None

        if dict_match:
            synonyms = list(dict_match["synonyms"])
            mesh_candidate = dict_match["mesh"]

        if use_llm and settings.LLM_PROVIDER in ["openai", "gemini"]:
            try:
                llm_res = await _call_llm_synonym_expansion(concept.text)
                if llm_res.get("synonyms"):
                    synonyms = list(set(synonyms + llm_res["synonyms"]))
                if llm_res.get("mesh_heading"):
                    mesh_candidate = llm_res["mesh_heading"]
            except Exception as e:
                logger.warning(f"LLM expansion failed for '{concept.text}', falling back to dictionary: {e}")

        expanded_list.append(ExpandedSynonym(
            term=concept.text,
            synonyms=synonyms,
            mesh_heading=mesh_candidate
        ))

    return expanded_list

async def _call_llm_synonym_expansion(term: str) -> Dict:
    """Helper to call LLM for medical synonym expansion."""
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        # pyrefly: ignore [missing-import]
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            prompt = f"Given the medical term '{term}', provide a JSON object with: 1) 'synonyms' (list of 3-5 clinical synonyms/abbreviations) and 2) 'mesh_heading' (official Medical Subject Heading if applicable)."
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content)

    return {}
