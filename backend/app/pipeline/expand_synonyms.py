import json
import logging
# pyrefly: ignore [missing-import]
import httpx
from typing import List, Dict, Optional, Any
from app.config import settings
from app.models.schemas import ExtractedConcept, ExpandedSynonym

logger = logging.getLogger(__name__)

# Comprehensive Medical Concept Synonym & MeSH Dictionary Fallback
MEDICAL_ONTOLOGY_MAP: Dict[str, Dict[str, Any]] = {
    "metformin": {
        "synonyms": ["biguanides", "dimethylbiguanide", "Glucophage"],
        "mesh": "Metformin"
    },
    "type 2 diabetes": {
        "synonyms": ["noninsulin dependent diabetes mellitus", "T2D", "T2DM", "type 2 diabetes mellitus"],
        "mesh": "Diabetes Mellitus, Type 2"
    },
    "glp-1": {
        "synonyms": ["glucagon-like peptide 1", "GLP-1 receptor agonist", "GLP-1 RA", "incretin mimetic"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "glp-1 receptor agonists": {
        "synonyms": ["glucagon-like peptide 1 agonists", "GLP-1 RA", "semaglutide", "liraglutide", "dulaglutide"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "semaglutide": {
        "synonyms": ["Ozempic", "Wegovy", "Rybelsus", "GLP-1 receptor agonist"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "liraglutide": {
        "synonyms": ["Victoza", "Saxenda", "GLP-1 agonist"],
        "mesh": "Glucagon-Like Peptide-1 Receptor Agonists"
    },
    "tirzepatide": {
        "synonyms": ["Mounjaro", "Zepbound", "GIP/GLP-1 dual receptor agonist"],
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
    "hypertension": {
        "synonyms": ["high blood pressure", "HTN", "essential hypertension", "arterial hypertension"],
        "mesh": "Hypertension"
    },
    "heart failure": {
        "synonyms": ["congestive heart failure", "CHF", "HFpEF", "HFrEF"],
        "mesh": "Heart Failure"
    },
    "myocardial infarction": {
        "synonyms": ["heart attack", "MI", "acute coronary syndrome", "coronary occlusion"],
        "mesh": "Myocardial Infarction"
    },
    "stroke": {
        "synonyms": ["cerebrovascular accident", "CVA", "ischemic stroke", "brain ischemia"],
        "mesh": "Stroke"
    },
    "sglt-2": {
        "synonyms": ["SGLT2 inhibitors", "sodium-glucose cotransporter 2 inhibitors", "empagliflozin", "dapagliflozin"],
        "mesh": "Sodium-Glucose Transporter 2 Inhibitors"
    },
    "dapagliflozin": {
        "synonyms": ["Farxiga", "SGLT2 inhibitor"],
        "mesh": "Sodium-Glucose Transporter 2 Inhibitors"
    },
    "empagliflozin": {
        "synonyms": ["Jardiance", "SGLT2 inhibitor"],
        "mesh": "Sodium-Glucose Transporter 2 Inhibitors"
    },
    "melanoma": {
        "synonyms": ["cutaneous melanoma", "malignant melanoma", "melanoma cancer"],
        "mesh": "Melanoma"
    },
    "pembrolizumab": {
        "synonyms": ["Keytruda", "anti-PD-1", "immune checkpoint inhibitor", "programmed death receptor 1 antibody"],
        "mesh": "Pembrolizumab"
    },
    "nivolumab": {
        "synonyms": ["Opdivo", "anti-PD-1 antibody", "immune checkpoint inhibitor"],
        "mesh": "Nivolumab"
    },
    "lung cancer": {
        "synonyms": ["non-small cell lung cancer", "NSCLC", "small cell lung cancer", "SCLC", "pulmonary neoplasm"],
        "mesh": "Carcinoma, Non-Small-Cell Lung"
    },
    "breast cancer": {
        "synonyms": ["mammary carcinoma", "breast neoplasm", "HER2 positive breast cancer", "TNBC"],
        "mesh": "Breast Neoplasms"
    },
    "alzheimer": {
        "synonyms": ["Alzheimer's disease", "AD", "senile dementia", "amyloid dementia"],
        "mesh": "Alzheimer Disease"
    },
    "rheumatoid arthritis": {
        "synonyms": ["RA", "inflammatory arthritis", "rheumatoid disease"],
        "mesh": "Arthritis, Rheumatoid"
    },
    "asthma": {
        "synonyms": ["bronchial asthma", "reactive airway disease", "asthmatic bronchospasm"],
        "mesh": "Asthma"
    },
    "obesity": {
        "synonyms": ["overweight", "adiposity", "high BMI", "metabolic syndrome"],
        "mesh": "Obesity"
    },
    "atherosclerosis": {
        "synonyms": ["arteriosclerosis", "arterial plaque", "coronary artery disease", "CAD"],
        "mesh": "Atherosclerosis"
    },
    "sickle cell": {
        "synonyms": ["sickle cell anemia", "sickle cell disease", "HbS disease"],
        "mesh": "Anemia, Sickle Cell"
    },
    "crispr": {
        "synonyms": ["CRISPR-Cas9", "clustered regularly interspaced short palindromic repeats", "gene editing"],
        "mesh": "Clustered Regularly Interspaced Short Palindromic Repeats"
    },
    "statins": {
        "synonyms": ["HMG-CoA reductase inhibitors", "atorvastatin", "rosuvastatin", "simvastatin", "lipid lowering"],
        "mesh": "Hydroxymethylglutaryl-CoA Reductase Inhibitors"
    },
    "kidney disease": {
        "synonyms": ["chronic kidney disease", "CKD", "renal disease", "nephropathy", "renal insufficiency"],
        "mesh": "Renal Insufficiency, Chronic"
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
        else:
            from app.services.mesh_data import MeshDictionaryManager
            m_entry = MeshDictionaryManager.get_instance().get_mesh_entry(raw_text)
            if m_entry:
                synonyms = list(m_entry.get("synonyms", []))
                mesh_candidate = m_entry.get("mesh_heading")

        if use_llm and settings.LLM_PROVIDER in ["openai", "gemini"]:
            try:
                llm_res = await _call_llm_synonym_expansion(concept.text)
                if llm_res.get("synonyms"):
                    synonyms = list(dict.fromkeys(synonyms + llm_res["synonyms"]))
                if llm_res.get("mesh_heading"):
                    mesh_candidate = llm_res["mesh_heading"]
            except Exception as e:
                logger.warning(f"LLM expansion failed for '{concept.text}', falling back to ontology dictionary: {e}")

        expanded_list.append(ExpandedSynonym(
            term=concept.text,
            synonyms=synonyms if synonyms else [concept.text],
            mesh_heading=mesh_candidate or concept.text.title()
        ))

    return expanded_list

async def _call_llm_synonym_expansion(term: str) -> Dict:
    """Helper to call Gemini or OpenAI LLM for medical synonym expansion."""
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-3.6-flash"]
        for model in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
                prompt = (
                    f"You are a medical informatics expert. Given the clinical/medical term '{term}', "
                    f"provide a JSON object with: 1) 'synonyms' (list of 3-5 clinical synonyms/abbreviations) "
                    f"and 2) 'mesh_heading' (official Medical Subject Heading if applicable). Return ONLY valid JSON."
                )
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.post(
                        url,
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"responseMimeType": "application/json"}
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        content_str = data["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(content_str)
            except Exception as ex:
                logger.debug(f"Gemini API model {model} error: {ex}")

    elif settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
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
        except Exception as ex:
            logger.debug(f"OpenAI API error: {ex}")

    return {}
