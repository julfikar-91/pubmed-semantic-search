import json
import asyncio
import logging
from typing import List, Dict, Optional, Any
from app.config import settings
from app.models.schemas import ExtractedConcept, ExpandedSynonym
from app.services.http_client import HttpClientPool, execute_with_retry
from app.services.mesh_data import MeshDictionaryManager
from app.services.cache_service import cache_service
from app.services.metrics import metrics_tracker

logger = logging.getLogger(__name__)

# Comprehensive Medical Concept Synonym & MeSH Dictionary Fallback
MEDICAL_ONTOLOGY_MAP: Dict[str, Dict[str, Any]] = {
    "sugar disease": {
        "synonyms": ["sugar disease", "diabetes mellitus", "diabetes", "diabetic", "type 2 diabetes"],
        "mesh": "Diabetes Mellitus"
    },
    "blood cancer": {
        "synonyms": ["blood cancer", "hematologic neoplasms", "hematological malignancies", "leukemia", "lymphoma", "multiple myeloma"],
        "mesh": "Hematologic Neoplasms"
    },
    "heart attack": {
        "synonyms": ["heart attack", "myocardial infarction", "acute myocardial infarction", "acute coronary syndrome", "MI"],
        "mesh": "Myocardial Infarction"
    },
    "high blood pressure": {
        "synonyms": ["high blood pressure", "hypertension", "HTN", "essential hypertension", "arterial hypertension"],
        "mesh": "Hypertension"
    },
    "stroke": {
        "synonyms": ["stroke", "cerebrovascular accident", "ischemic stroke", "cerebral infarction", "apoplexy"],
        "mesh": "Stroke"
    },
    "metformin": {
        "synonyms": ["metformin", "biguanides", "dimethylbiguanide", "Glucophage"],
        "mesh": "Metformin"
    },
    "type 2 diabetes": {
        "synonyms": ["type 2 diabetes", "noninsulin dependent diabetes mellitus", "T2D", "T2DM", "type 2 diabetes mellitus"],
        "mesh": "Diabetes Mellitus, Type 2"
    },
    "glp-1": {
        "synonyms": ["glp-1", "glucagon-like peptide 1", "GLP-1 receptor agonist", "GLP-1 RA", "incretin mimetic"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "glp-1 receptor agonists": {
        "synonyms": ["GLP-1 receptor agonists", "glucagon-like peptide 1 agonists", "GLP-1 RA", "semaglutide", "liraglutide", "dulaglutide"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "semaglutide": {
        "synonyms": ["semaglutide", "Ozempic", "Wegovy", "Rybelsus", "GLP-1 receptor agonist"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "liraglutide": {
        "synonyms": ["liraglutide", "Victoza", "Saxenda", "GLP-1 agonist"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "tirzepatide": {
        "synonyms": ["tirzepatide", "Mounjaro", "Zepbound", "GIP/GLP-1 dual receptor agonist"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "weight loss": {
        "synonyms": ["weight loss", "weight reduction", "body weight changes", "anti-obesity"],
        "mesh": "Weight Loss"
    },
    "obesity": {
        "synonyms": ["obesity", "overweight", "adiposity", "obese"],
        "mesh": "Obesity"
    },
    "non-diabetic": {
        "synonyms": ["non-diabetic", "nondiabetic", "without diabetes", "euglycemic"],
        "mesh": "Non-Diabetic"
    },
    "melanoma": {
        "synonyms": ["melanoma", "malignant melanoma", "cutaneous melanoma"],
        "mesh": "Melanoma"
    },
    "diabetes": {
        "synonyms": ["diabetes", "diabetes mellitus", "diabetic", "hyperglycemia"],
        "mesh": "Diabetes Mellitus"
    },
    "cardiovascular disease": {
        "synonyms": ["cardiovascular disease", "CVD", "heart disease", "cardiovascular outcomes", "cardiac events", "MACE"],
        "mesh": "Cardiovascular Diseases"
    },
    "hypertension": {
        "synonyms": ["hypertension", "high blood pressure", "HTN", "essential hypertension", "arterial hypertension"],
        "mesh": "Hypertension"
    },
    "heart failure": {
        "synonyms": ["heart failure", "congestive heart failure", "CHF", "HFpEF", "HFrEF"],
        "mesh": "Heart Failure"
    },
    "myocardial infarction": {
        "synonyms": ["myocardial infarction", "heart attack", "MI", "acute coronary syndrome", "coronary occlusion"],
        "mesh": "Myocardial Infarction"
    },
    "alzheimer's disease": {
        "synonyms": ["Alzheimer's disease", "Alzheimer disease", "AD", "Alzheimer dementia"],
        "mesh": "Alzheimer Disease"
    },
    "alzheimers": {
        "synonyms": ["Alzheimer's disease", "Alzheimer disease", "AD", "Alzheimer dementia"],
        "mesh": "Alzheimer Disease"
    },
    "acute myeloid leukemia": {
        "synonyms": ["acute myeloid leukemia", "AML", "acute myelogenous leukemia", "acute nonlymphocytic leukemia"],
        "mesh": "Leukemia, Myeloid, Acute"
    },
    "leukemia": {
        "synonyms": ["leukemia", "leukemias", "hematologic malignancy"],
        "mesh": "Leukemia"
    },
    "breast cancer": {
        "synonyms": ["breast cancer", "breast neoplasms", "mammary carcinoma", "breast carcinoma"],
        "mesh": "Breast Neoplasms"
    },
    "chemotherapy": {
        "synonyms": ["chemotherapy", "antineoplastic chemotherapy", "cytotoxic therapy", "chemotherapeutic agents"],
        "mesh": "Drug Therapy"
    },
    "biomarkers": {
        "synonyms": ["biomarkers", "biological markers", "surrogate markers", "molecular markers"],
        "mesh": "Biomarkers"
    },
    "covid-19 vaccine": {
        "synonyms": ["COVID-19 vaccine", "SARS-CoV-2 vaccine", "COVID-19 vaccination", "mRNA vaccine"],
        "mesh": "COVID-19 Vaccines"
    },
    "vaccine effectiveness": {
        "synonyms": ["vaccine effectiveness", "vaccine efficacy", "vaccine protection"],
        "mesh": "Vaccine Efficacy"
    },
    "elderly": {
        "synonyms": ["elderly", "older adults", "geriatric patients", "aged"],
        "mesh": "Aged"
    },
    "treatment": {
        "synonyms": ["treatment", "therapy", "therapeutic intervention", "management", "clinical trial"],
        "mesh": "Therapeutics"
    },
    "causes": {
        "synonyms": ["causes", "etiology", "pathogenesis", "risk factors"],
        "mesh": "Etiology"
    },
    "drug resistance": {
        "synonyms": ["drug resistance", "chemoresistance", "refractory disease", "therapy resistance"],
        "mesh": "Drug Resistance, Neoplasm"
    },
    "complications": {
        "synonyms": ["complications", "adverse outcomes", "secondary disorders", "clinical sequelae"],
        "mesh": "Complications"
    },
    "pembrolizumab": {
        "synonyms": ["pembrolizumab", "Keytruda", "anti-PD-1", "immune checkpoint inhibitor", "lambrolizumab"],
        "mesh": "Pembrolizumab"
    },
    "nivolumab": {
        "synonyms": ["nivolumab", "Opdivo", "anti-PD-1", "immune checkpoint inhibitor"],
        "mesh": "Nivolumab"
    },
    "non-small cell lung cancer": {
        "synonyms": ["non-small cell lung cancer", "NSCLC", "lung adenocarcinoma", "squamous cell lung carcinoma", "non-small cell lung carcinoma"],
        "mesh": "Carcinoma, Non-Small-Cell Lung"
    },
    "lung cancer": {
        "synonyms": ["lung cancer", "lung neoplasms", "bronchogenic carcinoma", "NSCLC", "SCLC"],
        "mesh": "Lung Neoplasms"
    },
    "statins": {
        "synonyms": ["statins", "HMG-CoA reductase inhibitors", "atorvastatin", "rosuvastatin", "simvastatin", "lipid lowering agents"],
        "mesh": "Hydroxymethylglutaryl-CoA Reductase Inhibitors"
    },
    "statin": {
        "synonyms": ["statin", "HMG-CoA reductase inhibitors", "atorvastatin", "rosuvastatin", "simvastatin"],
        "mesh": "Hydroxymethylglutaryl-CoA Reductase Inhibitors"
    },
    "aspirin": {
        "synonyms": ["aspirin", "acetylsalicylic acid", "ASA", "antiplatelet therapy"],
        "mesh": "Aspirin"
    },
    "renal function": {
        "synonyms": ["renal function", "kidney function", "eGFR", "renal clearance", "glomerular filtration"],
        "mesh": "Kidney Function Tests"
    },
    "kidney disease": {
        "synonyms": ["kidney disease", "chronic kidney disease", "CKD", "renal disease", "nephropathy", "renal insufficiency"],
        "mesh": "Renal Insufficiency, Chronic"
    }
}

async def _expand_single_concept(concept: ExtractedConcept, use_llm: bool = True) -> ExpandedSynonym:
    raw_text = concept.text.strip().lower()
    
    # 1. Check Intermediate Term Cache (O(1) memory lookup)
    cached = cache_service.get_term_expansion(raw_text)
    if cached:
        syns, mesh_head = cached
        # Ensure concept.text is always included
        combined = [concept.text] + [s for s in syns if s.lower() != raw_text]
        return ExpandedSynonym(
            term=concept.text,
            synonyms=list(dict.fromkeys(combined)),
            mesh_heading=mesh_head or concept.text.title()
        )

    # 2. Check Static Medical Ontology Map
    dict_match = None
    for k, v in MEDICAL_ONTOLOGY_MAP.items():
        if k == raw_text or (len(raw_text) > 4 and k in raw_text):
            dict_match = v
            break

    synonyms: List[str] = []
    mesh_candidate = None

    if dict_match:
        synonyms = list(dict_match["synonyms"])
        mesh_candidate = dict_match["mesh"]
    else:
        # 3. Check loaded MeSH Dictionary Manager
        m_entry = MeshDictionaryManager.get_instance().get_mesh_entry(raw_text)
        if m_entry:
            synonyms = list(m_entry.get("synonyms", []))
            mesh_candidate = m_entry.get("mesh_heading")

    # 4. If not resolved offline, try LLM expansion with strict resilience & fast timeout
    if not synonyms and use_llm and settings.LLM_PROVIDER in ["openai", "gemini"]:
        try:
            llm_res = await asyncio.wait_for(_call_llm_synonym_expansion(concept.text), timeout=4.0)
            if llm_res.get("synonyms"):
                synonyms = list(dict.fromkeys(synonyms + llm_res["synonyms"]))
            if llm_res.get("mesh_heading"):
                mesh_candidate = llm_res["mesh_heading"]
        except Exception as e:
            metrics_tracker.record_llm_failure(fell_back=True)
            logger.debug(f"LLM fast expansion fallback for '{concept.text}': {e}")

    # Fallback to concept text if no synonyms found; ensure concept.text is always first
    unique_synonyms = [concept.text] + [s for s in synonyms if s.lower() != raw_text]
    final_synonyms = list(dict.fromkeys(unique_synonyms))
    final_heading = mesh_candidate or concept.text.title()

    # Cache intermediate expansion
    cache_service.set_term_expansion(raw_text, final_synonyms, final_heading)

    return ExpandedSynonym(
        term=concept.text,
        synonyms=final_synonyms,
        mesh_heading=final_heading
    )

async def expand_synonyms(concepts: List[ExtractedConcept], use_llm: bool = True) -> List[ExpandedSynonym]:
    """Parallel concept expansion with multi-tier local MeSH fast-path and cache."""
    if not concepts:
        return []

    tasks = [_expand_single_concept(c, use_llm=use_llm) for c in concepts]
    return await asyncio.gather(*tasks)

async def _call_llm_synonym_expansion(term: str) -> Dict:
    """Fast non-blocking LLM synonym expansion with retry & backoff."""
    client = HttpClientPool.get_client()

    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = (
                f"Medical expert: for term '{term}', return JSON with: "
                f"'synonyms' (list of 3 clinical synonyms) and 'mesh_heading'. Return JSON only."
            )
            resp = await execute_with_retry(
                lambda: client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json"}
                    },
                    timeout=3.5
                ),
                max_retries=2,
                initial_delay=0.2
            )
            if resp.status_code == 200:
                data = resp.json()
                content_str = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(content_str)
        except Exception as ex:
            logger.debug(f"Gemini API call error: {ex}")

    elif settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            response = await execute_with_retry(
                lambda: client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": f"Given medical term '{term}', return JSON with: 'synonyms' and 'mesh_heading'."}],
                        "response_format": {"type": "json_object"}
                    },
                    timeout=1.4
                ),
                max_retries=2,
                initial_delay=0.2
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as ex:
            logger.debug(f"OpenAI API error: {ex}")

    return {}
