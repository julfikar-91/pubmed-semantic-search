import re
from typing import List, Set, Dict

from app.models.schemas import ExtractedConcept
from app.services.mesh_data import MeshDictionaryManager


# ============================================================
# Biomedical Pattern Dictionaries
# ============================================================

# ============================================================
# Biomedical Pattern Dictionaries
# ============================================================

DISEASE_PATTERNS = [
    r"\bsugar disease\b",
    r"\bblood cancer\b",
    r"\bdiabetes(?: mellitus)?\b",
    r"\btype [12] diabetes\b",
    r"\bcardiovascular disease\b",
    r"\bheart attack\b",
    r"\bhigh blood pressure\b",
    r"\bmelanoma\b",
    r"\bcancer\b",
    r"\bsickle cell(?: anemia)?\b",
    r"\balzheimer'?s?(?: disease)?\b",
    r"\bhypertension\b",
    r"\bheart failure\b",
    r"\bkidney disease\b",
    r"\bnephropathy\b",
    r"\bmyocardial infarction\b",
    r"\bstroke\b",
    r"\bbreast cancer\b",
    r"\blung cancer\b",
    r"\brheumatoid arthritis\b",
    r"\basthma\b",
    r"\bobesity\b",
    r"\batherosclerosis\b",
    r"\bcrohn'?s disease\b",
    r"\bparkinson'?s?\b",
    r"\bmultiple sclerosis\b",
    r"\bacute myeloid leukemia\b",
    r"\bleukemia\b",
    r"\blymphoma\b",
]

DRUG_PATTERNS = [
    r"\bglp-?1(?: receptor agonists?)?\b",
    r"\bsemaglutide\b",
    r"\bliraglutide\b",
    r"\btirzepatide\b",
    r"\bsglt-?2(?: inhibitors?)?\b",
    r"\bdapagliflozin\b",
    r"\bempagliflozin\b",
    r"\bmetformin\b",
    r"\bpembrolizumab\b",
    r"\bnivolumab\b",
    r"\bstatins?\b",
    r"\baspirin\b",
    r"\bchemotherapy\b",
    r"\bace inhibitors?\b",
    r"\bcrispr(?:-cas9)?\b",
    r"\bcovid-19 vaccines?\b",
    r"\bmrna vaccines?\b",
    r"\bmonoclonal antibod(?:y|ies)\b",
    r"\bcheckpoint inhibitors?\b",
]

MECHANISM_OUTCOME_PATTERNS = [
    r"\btreatment(?:s)?\b",
    r"\btherap(?:y|ies)\b",
    r"\bbiomarkers?\b",
    r"\bcauses?\b",
    r"\bcomplications?\b",
    r"\bdrug resistance\b",
    r"\beffectiveness\b",
    r"\befficacy\b",
    r"\belderly(?: patients)?\b",
    r"\bcardiovascular outcomes?\b",
    r"\bmortality\b",
    r"\bglycemic control\b",
    r"\bgene editing\b",
    r"\bside effects?\b",
    r"\btoxicity\b",
    r"\bimmuno-oncology\b",
    r"\brenal protection\b",
    r"\bweight loss\b",
    r"\binsulin sensitivity\b",
    r"\bapoptosis\b",
]

# ============================================================
# True English Stop Words (Preserving all clinical concepts)
# ============================================================

STOP_WORDS = {
    "what", "which", "when", "where", "who", "why", "how",
    "with", "from", "that", "this", "these", "those", "were",
    "have", "has", "had", "been", "being", "about",
    "patient", "patients", "study", "studies", "using", "use",
    "used", "and", "the", "for", "are", "was", "is", "of",
    "in", "on", "to", "by", "at", "as", "an", "a", "or",
    "can", "may", "does", "do", "did", "vs", "versus", "between"
}


# ============================================================
# MeSH Category Mapping
# ============================================================

def _infer_category_from_mesh_entry(entry: Dict) -> str:
    """
    Infer a broad biomedical category from a MeSH entry.

    Note:
    MeSH tree numbers are hierarchical. Therefore this is
    intentionally a broad classification rather than claiming
    that every tree branch represents an exact semantic class.
    """

    tree_numbers = entry.get("tree_numbers", [])

    for tree_number in tree_numbers:

        if not tree_number:
            continue

        prefix = tree_number[0].upper()

        # C = Diseases
        if prefix == "C":
            return "Disease"

        # D = Chemicals and Drugs
        if prefix == "D":
            return "Drug"

        # A = Anatomy
        if prefix == "A":
            return "Anatomy"

        # E = Analytical, Diagnostic and Therapeutic Techniques
        if prefix == "E":
            return "Clinical/Diagnostic Concept"

        # G = Phenomena and Processes
        if prefix == "G":
            return "Biomedical Process"

    return "Biomedical Concept"


# ============================================================
# Concept Helper
# ============================================================

def _add_concept(
    concepts: List[ExtractedConcept],
    seen_texts: Set[str],
    text: str,
    category: str,
    confidence: float,
) -> None:
    """
    Add a concept only if it has not already been added.
    """

    clean_text = re.sub(r"\s+", " ", text.strip())

    if not clean_text:
        return

    normalized = clean_text.lower()

    if normalized in seen_texts:
        return

    seen_texts.add(normalized)

    concepts.append(
        ExtractedConcept(
            text=clean_text,
            category=category,
            confidence=confidence,
        )
    )


# ============================================================
# Redundancy Removal
# ============================================================

def _remove_redundant_concepts(
    concepts: List[ExtractedConcept],
) -> List[ExtractedConcept]:
    """
    Remove generic concepts when a more specific concept
    already contains them.

    Example:

        cancer
        breast cancer

    Keep:

        breast cancer
    """

    if len(concepts) <= 1:
        return concepts

    filtered = []

    for concept in concepts:

        current = concept.text.lower().strip()

        redundant = False

        for other in concepts:

            if concept is other:
                continue

            other_text = other.text.lower().strip()

            if current == other_text:
                continue

            # Example:
            # cancer -> breast cancer
            if current in other_text:

                # Make sure it is a meaningful word/phrase
                # relationship rather than partial substring.
                current_words = set(re.findall(r"\w+", current))
                other_words = set(re.findall(r"\w+", other_text))

                if current_words.issubset(other_words):
                    redundant = True
                    break

        if not redundant:
            filtered.append(concept)

    return filtered


# ============================================================
# Pattern Extraction
# ============================================================

def _extract_pattern_concepts(
    query: str,
    patterns: List[str],
    category: str,
    confidence: float,
    concepts: List[ExtractedConcept],
    seen_texts: Set[str],
) -> None:
    """
    Extract all matching concepts from a pattern list.
    """

    for pattern in patterns:

        matches = re.finditer(
            pattern,
            query,
            flags=re.IGNORECASE,
        )

        for match in matches:

            matched_text = match.group(0).strip()

            _add_concept(
                concepts=concepts,
                seen_texts=seen_texts,
                text=matched_text,
                category=category,
                confidence=confidence,
            )


# ============================================================
# MeSH Extraction
# ============================================================

def _extract_mesh_concepts(
    query: str,
    concepts: List[ExtractedConcept],
    seen_texts: Set[str],
) -> None:
    """
    Search 3-word, 2-word and 1-word spans against the
    local MeSH dictionary.

    Longer phrases are checked first so that:

        breast cancer

    is preferred over:

        cancer
    """

    mesh_manager = MeshDictionaryManager.get_instance()

    words = re.findall(r"[A-Za-z0-9'-]+", query)

    if not words:
        return

    # Check longer phrases first.
    for n in (3, 2, 1):

        if len(words) < n:
            continue

        for i in range(len(words) - n + 1):

            phrase = " ".join(words[i:i + n]).strip()

            normalized = phrase.lower()

            # Skip very short phrases
            if len(normalized) < 4:
                continue

            # Skip exact stop words
            if normalized in STOP_WORDS:
                continue

            # If already represented by a stronger concept,
            # don't add it again.
            if normalized in seen_texts:
                continue

            try:
                mesh_entry = mesh_manager.get_mesh_entry(
                    normalized
                )
            except Exception:
                # Do not break the complete extraction pipeline
                # if the local MeSH lookup fails.
                continue

            if not mesh_entry:
                continue

            category = _infer_category_from_mesh_entry(
                mesh_entry
            )

            _add_concept(
                concepts=concepts,
                seen_texts=seen_texts,
                text=phrase,
                category=category,
                confidence=0.95,
            )


# ============================================================
# Fallback Extraction
# ============================================================

def _extract_fallback_concepts(
    query: str,
    concepts: List[ExtractedConcept],
    seen_texts: Set[str],
) -> None:
    """
    Preserve meaningful unmatched biomedical-looking terms.

    This is intentionally conservative so generic English words
    do not pollute the biomedical search query.
    """

    words = re.findall(
        r"[A-Za-z0-9'-]+",
        query,
    )

    existing_tokens = set()

    for concept in concepts:

        existing_tokens.update(
            re.findall(
                r"[a-z0-9'-]+",
                concept.text.lower(),
            )
        )

    added = 0

    for word in words:

        normalized = word.lower().strip()

        if len(normalized) < 4:
            continue

        if normalized in STOP_WORDS:
            continue

        if normalized in seen_texts:
            continue

        # Don't add words that are already part of
        # an extracted biomedical concept.
        if normalized in existing_tokens:
            continue

        _add_concept(
            concepts=concepts,
            seen_texts=seen_texts,
            text=word,
            category="General Biomedical Concept",
            confidence=0.75,
        )

        added += 1

        # Avoid flooding the result with generic terms.
        if added >= 4:
            break


# ============================================================
# Main Concept Extraction Function
# ============================================================

def extract_concepts(
    query: str,
) -> List[ExtractedConcept]:
    """
    Biomedical Concept & Entity Extraction.

    Pipeline:

        Query
          ↓
        Regex extraction
          ↓
        MeSH dictionary lookup
          ↓
        Duplicate removal
          ↓
        Redundant concept removal
          ↓
        Conservative fallback
          ↓
        ExtractedConcept[]
    """

    concepts: List[ExtractedConcept] = []

    seen_texts: Set[str] = set()

    if not query or not query.strip():
        return concepts

    query = query.strip()

    # --------------------------------------------------------
    # 1. Known Drugs
    # --------------------------------------------------------

    _extract_pattern_concepts(
        query=query,
        patterns=DRUG_PATTERNS,
        category="Drug",
        confidence=0.98,
        concepts=concepts,
        seen_texts=seen_texts,
    )

    # --------------------------------------------------------
    # 2. Known Diseases
    # --------------------------------------------------------

    _extract_pattern_concepts(
        query=query,
        patterns=DISEASE_PATTERNS,
        category="Disease",
        confidence=0.99,
        concepts=concepts,
        seen_texts=seen_texts,
    )

    # --------------------------------------------------------
    # 3. Mechanisms / Outcomes
    # --------------------------------------------------------

    _extract_pattern_concepts(
        query=query,
        patterns=MECHANISM_OUTCOME_PATTERNS,
        category="Outcome",
        confidence=0.90,
        concepts=concepts,
        seen_texts=seen_texts,
    )

    # --------------------------------------------------------
    # 4. MeSH Dictionary Extraction
    # --------------------------------------------------------

    _extract_mesh_concepts(
        query=query,
        concepts=concepts,
        seen_texts=seen_texts,
    )

    # --------------------------------------------------------
    # 5. Remove Generic Concepts
    # --------------------------------------------------------

    concepts = _remove_redundant_concepts(
        concepts
    )

    # Rebuild seen set after filtering.
    seen_texts = {
        concept.text.lower()
        for concept in concepts
    }

    # --------------------------------------------------------
    # 6. Conservative Fallback
    # --------------------------------------------------------

    _extract_fallback_concepts(
        query=query,
        concepts=concepts,
        seen_texts=seen_texts,
    )

    # --------------------------------------------------------
    # 7. Final Redundancy Check
    # --------------------------------------------------------

    concepts = _remove_redundant_concepts(
        concepts
    )

    return concepts