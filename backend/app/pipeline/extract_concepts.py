import re
from typing import List, Set
from app.models.schemas import ExtractedConcept
from app.services.mesh_data import MeshDictionaryManager

DISEASE_PATTERNS = [
    r"diabetes( mellitus)?", r"type [12] diabetes", r"cardiovascular disease",
    r"melanoma", r"cancer", r"sickle cell( anemia)?", r"alzheimer'?s?",
    r"hypertension", r"heart failure", r"kidney disease", r"nephropathy",
    r"myocardial infarction", r"stroke", r"breast cancer", r"lung cancer",
    r"rheumatoid arthritis", r"asthma", r"obesity", r"atherosclerosis",
    r"crohn'?s disease", r"parkinson'?s?", r"multiple sclerosis", r"leukemia", r"lymphoma"
]

DRUG_PATTERNS = [
    r"glp-?1( receptor agonists?)?", r"semaglutide", r"liraglutide", r"tirzepatide",
    r"sglt-?2( inhibitors?)?", r"dapagliflozin", r"empagliflozin", r"metformin",
    r"pembrolizumab", r"nivolumab", r"statins?", r"aspirin", r"ACE inhibitors?",
    r"crispr(-cas9)?", r"mrna vaccine", r"monoclonal antibod(y|ies)", r"checkpoint inhibitors?"
]

MECHANISM_OUTCOME_PATTERNS = [
    r"cardiovascular outcomes?", r"mortality", r"glycemic control", r"gene editing",
    r"side effects?", r"toxicity", r"efficacy", r"immuno-oncology",
    r"renal protection", r"weight loss", r"insulin sensitivity", r"apoptosis"
]

def _infer_category_from_mesh_entry(entry: dict) -> str:
    tree_numbers = entry.get("tree_numbers", [])
    for tn in tree_numbers:
        if tn.startswith("D"):
            return "Drug"
        elif tn.startswith("C"):
            return "Disease"
        elif tn.startswith("G") or tn.startswith("E"):
            return "Outcome"
        elif tn.startswith("A"):
            return "Anatomy"
    return "Biomedical Concept"

def extract_concepts(query: str) -> List[ExtractedConcept]:
    """
    Biomedical Concept & Entity Extraction (Step 1 / NER):
    Extracts clinical entities (Drugs, Diseases, Outcomes, Mechanisms)
    from the spell-corrected query using pattern rules + NLM MeSH Tree Taxonomies.
    """
    concepts: List[ExtractedConcept] = []
    seen_texts: Set[str] = set()
    query_lower = query.lower()

    # Step 1: Explicit pattern matches
    for pattern in DRUG_PATTERNS:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            matched_text = match.group(0).strip()
            if matched_text not in seen_texts:
                seen_texts.add(matched_text)
                concepts.append(ExtractedConcept(
                    text=matched_text,
                    category="Drug",
                    confidence=0.98
                ))

    for pattern in DISEASE_PATTERNS:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            matched_text = match.group(0).strip()
            if matched_text not in seen_texts:
                seen_texts.add(matched_text)
                concepts.append(ExtractedConcept(
                    text=matched_text,
                    category="Disease",
                    confidence=0.99
                ))

    for pattern in MECHANISM_OUTCOME_PATTERNS:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            matched_text = match.group(0).strip()
            if matched_text not in seen_texts:
                seen_texts.add(matched_text)
                concepts.append(ExtractedConcept(
                    text=matched_text,
                    category="Outcome",
                    confidence=0.90
                ))

    # Step 2: Extract additional terms matching MeSH database
    mesh_mgr = MeshDictionaryManager.get_instance()
    words = re.findall(r"[\w'-]+", query)
    stop_words = {
        "what", "with", "from", "that", "this", "were", "have", "been", "about",
        "effect", "effects", "role", "treatment", "patients", "study", "studies", "risk",
        "and", "the", "for", "are", "impact", "dose"
    }

    # Check 2-word and 1-word spans
    for n in (2, 1):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i+n]).lower()
            if phrase in stop_words or len(phrase) < 4:
                continue
            if any(phrase in s or s in phrase for s in seen_texts):
                continue

            m_entry = mesh_mgr.get_mesh_entry(phrase)
            if m_entry:
                cat = _infer_category_from_mesh_entry(m_entry)
                seen_texts.add(phrase)
                concepts.append(ExtractedConcept(
                    text=phrase,
                    category=cat,
                    confidence=0.95
                ))

    # Fallback to general tokens if no concept matched
    if not concepts:
        filtered = [w for w in words if w.lower() not in stop_words and len(w) >= 3]
        for term in filtered[:4]:
            if term.lower() not in seen_texts:
                seen_texts.add(term.lower())
                concepts.append(ExtractedConcept(
                    text=term,
                    category="General Concept",
                    confidence=0.85
                ))

    return concepts
