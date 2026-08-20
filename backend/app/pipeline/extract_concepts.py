import re
from typing import List
from app.models.schemas import ExtractedConcept

DISEASE_PATTERNS = [
    r"diabetes( mellitus)?", r"type [12] diabetes", r"cardiovascular disease",
    r"melanoma", r"cancer", r"sickle cell( anemia)?", r"alzheimer'?s",
    r"hypertension", r"heart failure", r"kidney disease", r"nephropathy",
    r"myocardial infarction", r"stroke", r"breast cancer", r"lung cancer",
    r"rheumatoid arthritis", r"asthma", r"obesity", r"atherosclerosis"
]

DRUG_PATTERNS = [
    r"glp-?1( receptor agonists?)?", r"semaglutide", r"liraglutide", r"tirzepatide",
    r"sglt-?2( inhibitors?)?", r"dapagliflozin", r"empagliflozin", r"metformin",
    r"pembrolizumab", r"nivolumab", r"statins?", r"aspirin", r"ACE inhibitors?",
    r"crispr(-cas9)?", r"mrna vaccine", r"monoclonal antibod(y|ies)"
]

MECHANISM_OUTCOME_PATTERNS = [
    r"cardiovascular outcomes?", r"mortality", r"glycemic control", r"gene editing",
    r"side effects?", r"toxicity", r"efficacy", r"immuno-oncology",
    r"renal protection", r"weight loss", r"insulin sensitivity", r"apoptosis"
]

def extract_concepts(query: str) -> List[ExtractedConcept]:
    """Step 1 & 2: Extract key medical concepts and entities from a natural language query."""
    concepts: List[ExtractedConcept] = []
    seen_texts = set()
    query_lower = query.lower()

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

    if not concepts:
        words = [w for w in re.split(r"\W+", query) if len(w) > 3]
        stop_words = {"what", "with", "from", "that", "this", "were", "have", "been", "about", "effect", "effects", "role", "treatment", "patients"}
        filtered = [w for w in words if w.lower() not in stop_words]
        for term in filtered[:4]:
            if term.lower() not in seen_texts:
                seen_texts.add(term.lower())
                concepts.append(ExtractedConcept(
                    text=term,
                    category="General Concept",
                    confidence=0.80
                ))

    return concepts
