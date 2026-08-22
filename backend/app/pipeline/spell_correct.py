import re
import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from app.models.schemas import SpellCorrection
from app.services.mesh_data import MeshDictionaryManager

logger = logging.getLogger(__name__)

# RapidFuzz for high-speed C++ accelerated biomedical fuzzy matching
HAS_RAPIDFUZZ = False
try:
    # pyrefly: ignore [missing-import]
    from rapidfuzz import process, fuzz
    HAS_RAPIDFUZZ = True
    logger.info("RapidFuzz successfully initialized for high-speed biomedical spell correction.")
except ImportError:
    import difflib
    logger.info("RapidFuzz not found. Using standard library difflib fallback.")

# Common Modern Clinical & Pharmacological Entities (Supplementary to Core MeSH)
MODERN_CLINICAL_SUPPLEMENT: Dict[str, Dict[str, Any]] = {
    "diabetes": {
        "mesh_id": "D003920",
        "mesh_heading": "Diabetes Mellitus",
        "category": "Disease",
        "synonyms": ["diabetes mellitus", "diabetic", "hyperglycemia"]
    },
    "metformin": {
        "mesh_id": "D004559",
        "mesh_heading": "Metformin",
        "category": "Drug",
        "synonyms": ["glucophage", "dimethylbiguanide"]
    },
    "semaglutide": {
        "mesh_id": "D000077543",
        "mesh_heading": "Glucagon-Like Peptide-1 Receptor Agonists",
        "category": "Drug",
        "synonyms": ["ozempic", "wegovy", "rybelsus", "glp-1 agonist"]
    },
    "liraglutide": {
        "mesh_id": "D000077543",
        "mesh_heading": "Glucagon-Like Peptide-1 Receptor Agonists",
        "category": "Drug",
        "synonyms": ["victoza", "saxenda"]
    },
    "tirzepatide": {
        "mesh_id": "D000077543",
        "mesh_heading": "Tirzepatide",
        "category": "Drug",
        "synonyms": ["mounjaro", "zepbound", "gip/glp-1 agonist"]
    },
    "weight loss": {
        "mesh_id": "D015431",
        "mesh_heading": "Weight Loss",
        "category": "Outcome",
        "synonyms": ["weight reduction", "body weight changes"]
    },
    "obesity": {
        "mesh_id": "D009765",
        "mesh_heading": "Obesity",
        "category": "Disease",
        "synonyms": ["overweight", "adiposity"]
    },
    "melanoma": {
        "mesh_id": "D008545",
        "mesh_heading": "Melanoma",
        "category": "Disease",
        "synonyms": ["malignant melanoma"]
    },
    "pembrolizumab": {
        "mesh_id": "D000074322",
        "mesh_heading": "Pembrolizumab",
        "category": "Drug",
        "synonyms": ["keytruda", "anti-pd-1", "pd-1 inhibitor", "checkpoint inhibitor"]
    },
    "nivolumab": {
        "mesh_id": "D000074323",
        "mesh_heading": "Nivolumab",
        "category": "Drug",
        "synonyms": ["opdivo", "anti-pd-1", "checkpoint inhibitor"]
    },
    "empagliflozin": {
        "mesh_id": "D000077203",
        "mesh_heading": "Sodium-Glucose Transporter 2 Inhibitors",
        "category": "Drug",
        "synonyms": ["jardiance", "sglt2 inhibitor", "sglt-2 inhibitor"]
    },
    "dapagliflozin": {
        "mesh_id": "D000077203",
        "mesh_heading": "Sodium-Glucose Transporter 2 Inhibitors",
        "category": "Drug",
        "synonyms": ["farxiga", "forxiga", "sglt2 inhibitor"]
    },
    "crispr": {
        "mesh_id": "D000078326",
        "mesh_heading": "Clustered Regularly Interspaced Short Palindromic Repeats",
        "category": "Technology",
        "synonyms": ["crispr-cas9", "gene editing", "cas9"]
    },
    "covid-19": {
        "mesh_id": "D000086382",
        "mesh_heading": "COVID-19",
        "category": "Disease",
        "synonyms": ["sars-cov-2", "coronavirus disease 2019", "2019-ncov"]
    }
}

# Standard English stop words and general biomedical terms that should NOT be modified
STOP_WORDS = {
    "what", "are", "the", "effects", "effect", "of", "on", "in", "with", "from",
    "that", "this", "these", "those", "were", "have", "has", "had", "been", "about",
    "role", "treatment", "treatments", "patient", "patients", "study", "studies",
    "risk", "and", "or", "for", "by", "is", "a", "an", "to", "not", "non",
    "versus", "vs", "between", "during", "after", "before", "impact", "efficacy",
    "evaluation", "analysis", "clinical", "trial", "trials", "human", "humans",
    "cancer", "cancers", "disease", "diseases", "drug", "drugs", "cell", "cells",
    "gene", "genes", "rate", "rates", "therapy", "therapies", "outcome", "outcomes",
    "weight", "loss", "adult", "adults", "elderly", "pediatric", "control", "placebo"
}

# Recognized standard biomedical acronyms that should be protected
PROTECTED_ACRONYMS = {
    "t2d", "t2dm", "t1d", "t1dm", "glp-1", "glp1", "sglt2", "sglt-2", "mrna", "dna",
    "rna", "hiv", "aids", "chf", "hfpef", "hfref", "mi", "cvd", "htn", "ckd",
    "nsclc", "sclc", "egfr", "her2", "kras", "pcr", "car-t", "cart", "bmi",
    "cad", "copd", "ra", "sle", "ibd", "afib", "dvt", "pe", "ards", "icu", "mace"
}

class BiomedicalSpellChecker:
    _instance: Optional['BiomedicalSpellChecker'] = None

    def __init__(self):
        self.mesh_mgr = MeshDictionaryManager.get_instance()
        self.known_single_words: Set[str] = set()
        # Fast 1st-letter + length indexed buckets for single tokens
        self.single_buckets: Dict[str, List[str]] = {}
        # Multi-word indexed by first letter of 1st word & word length
        self.multi_buckets: Dict[str, List[str]] = {}
        self._init_vocabulary_index()

    @classmethod
    def get_instance(cls) -> 'BiomedicalSpellChecker':
        if cls._instance is None:
            cls._instance = BiomedicalSpellChecker()
        return cls._instance

    def _init_vocabulary_index(self):
        """Indexes vocabulary into lightweight letter+length partitions for sub-5ms lookup."""
        all_single = set(self.mesh_mgr.single_word_vocab)
        
        # Extract individual medical keywords from multi-word MeSH terms and descriptors
        for phrase in self.mesh_mgr.multi_word_vocab:
            clean_phrase = re.sub(r"[^\w\s-]", " ", phrase)
            for word in clean_phrase.split():
                w = word.strip().lower()
                if len(w) >= 3 and w not in STOP_WORDS:
                    all_single.add(w)

        for desc in self.mesh_mgr.descriptors.values():
            heading = desc.get("mesh_heading", "")
            clean_head = re.sub(r"[^\w\s-]", " ", heading)
            for word in clean_head.split():
                w = word.strip().lower()
                if len(w) >= 3 and w not in STOP_WORDS:
                    all_single.add(w)

        for term, data in MODERN_CLINICAL_SUPPLEMENT.items():
            if len(term.split()) == 1:
                all_single.add(term.lower())
            else:
                for word in term.split():
                    w = word.strip().lower()
                    if len(w) >= 3:
                        all_single.add(w)
            for syn in data.get("synonyms", []):
                if len(syn.split()) == 1:
                    all_single.add(syn.lower())

        self.known_single_words = all_single

        for term in all_single:
            if len(term) < 3:
                continue
            first_char = term[0]
            # Key: first char + length
            key = f"{first_char}_{len(term)}"
            self.single_buckets.setdefault(key, []).append(term)
            # Also bucket by just first char for length variance
            self.single_buckets.setdefault(first_char, []).append(term)

        # Multi-word phrases
        for phrase in self.mesh_mgr.multi_word_vocab:
            words = phrase.split()
            w_count = len(words)
            if 2 <= w_count <= 4:
                first_char = phrase[0]
                key = f"{first_char}_{w_count}"
                self.multi_buckets.setdefault(key, []).append(phrase)

        for phrase, data in MODERN_CLINICAL_SUPPLEMENT.items():
            words = phrase.split()
            w_count = len(words)
            if 2 <= w_count <= 4:
                first_char = phrase[0]
                key = f"{first_char}_{w_count}"
                self.multi_buckets.setdefault(key, []).append(phrase)

    def _get_single_candidates(self, token: str) -> List[str]:
        t_len = len(token)
        first_char = token[0]
        candidates = []

        # Exact first char + length within [-1, +1]
        for l in range(max(3, t_len - 1), t_len + 2):
            k = f"{first_char}_{l}"
            if k in self.single_buckets:
                candidates.extend(self.single_buckets[k])

        # If token starts with possible typo in 1st letter, fallback to letter partition
        if len(candidates) < 10 and first_char in self.single_buckets:
            candidates.extend(self.single_buckets[first_char][:150])

        return list(set(candidates))

    def fuzzy_match_token(self, token: str, threshold: float = 0.80) -> Optional[Tuple[str, float, List[str], Dict[str, Any]]]:
        token_clean = token.strip().lower()

        if (len(token_clean) < 4 or 
            token_clean in STOP_WORDS or 
            token_clean in PROTECTED_ACRONYMS or 
            token_clean in self.known_single_words or 
            token_clean in self.mesh_mgr.term_to_mesh or 
            token_clean in MODERN_CLINICAL_SUPPLEMENT):
            return None

        candidate_vocab = self._get_single_candidates(token_clean)
        if not candidate_vocab:
            return None

        best_term = None
        best_score = 0.0
        top_candidates = []

        if HAS_RAPIDFUZZ:
            matches = process.extract(
                token_clean,
                candidate_vocab,
                scorer=fuzz.ratio,
                limit=5
            )
            for cand, score, _ in matches:
                norm_score = score / 100.0
                if norm_score >= threshold:
                    top_candidates.append(cand)
                    if norm_score > best_score:
                        best_score = norm_score
                        best_term = cand
        else:
            import difflib
            matches = difflib.get_close_matches(token_clean, candidate_vocab, n=5, cutoff=threshold)
            for cand in matches:
                score = difflib.SequenceMatcher(None, token_clean, cand).ratio()
                top_candidates.append(cand)
                if score > best_score:
                    best_score = score
                    best_term = cand

        if best_term and best_score >= threshold:
            # Check if candidate is a known descriptor
            mesh_info = {}
            if best_term in MODERN_CLINICAL_SUPPLEMENT:
                mesh_info = MODERN_CLINICAL_SUPPLEMENT[best_term]
            else:
                m_entry = self.mesh_mgr.get_mesh_entry(best_term)
                if m_entry:
                    mesh_info = m_entry
                else:
                    mesh_id = self.mesh_mgr.term_to_mesh.get(best_term)
                    mesh_info = {
                        "mesh_id": mesh_id,
                        "mesh_heading": best_term.title()
                    }

            return best_term, best_score, top_candidates[:3], mesh_info

        return None

    def fuzzy_match_phrase(self, phrase: str, threshold: float = 0.84) -> Optional[Tuple[str, float, List[str], Dict[str, Any]]]:
        phrase_clean = phrase.strip().lower()
        words = phrase_clean.split()
        w_count = len(words)

        if phrase_clean in self.mesh_mgr.term_to_mesh or phrase_clean in MODERN_CLINICAL_SUPPLEMENT:
            return None

        first_char = phrase_clean[0]
        target_vocab = self.multi_buckets.get(f"{first_char}_{w_count}", [])
        if not target_vocab:
            return None

        best_term = None
        best_score = 0.0
        top_candidates = []

        if HAS_RAPIDFUZZ:
            matches = process.extract(
                phrase_clean,
                target_vocab,
                scorer=fuzz.ratio,
                limit=5
            )
            for cand, score, _ in matches:
                norm_score = score / 100.0
                if norm_score >= threshold:
                    top_candidates.append(cand)
                    if norm_score > best_score:
                        best_score = norm_score
                        best_term = cand
        else:
            import difflib
            matches = difflib.get_close_matches(phrase_clean, target_vocab, n=5, cutoff=threshold)
            for cand in matches:
                score = difflib.SequenceMatcher(None, phrase_clean, cand).ratio()
                top_candidates.append(cand)
                if score > best_score:
                    best_score = score
                    best_term = cand

        if best_term and best_score >= threshold:
            mesh_info = self.mesh_mgr.get_mesh_entry(best_term) or {
                "mesh_id": self.mesh_mgr.term_to_mesh.get(best_term),
                "mesh_heading": best_term.title()
            }
            return best_term, best_score, top_candidates[:3], mesh_info

        return None

def correct_biomedical_query(query: str, similarity_threshold: float = 0.80) -> Tuple[str, List[SpellCorrection]]:
    """
    Step 0: Biomedical Spell Correction & Fuzzy Matching
    Executes high-speed partitioned fuzzy matching backed by the NLM MeSH Dictionary.
    """
    if not query or not query.strip():
        return query, []

    checker = BiomedicalSpellChecker.get_instance()
    
    # Instant O(1) Fast-Path: If all words in query exist in known vocab or stop words, return immediately (< 0.02ms)
    raw_tokens = [w.strip().lower() for w in re.findall(r"[\w'-]+", query)]
    has_unknown = any(
        (len(t) >= 4 and 
         t not in STOP_WORDS and 
         t not in PROTECTED_ACRONYMS and 
         t not in checker.known_single_words and 
         t not in checker.mesh_mgr.term_to_mesh and
         t not in MODERN_CLINICAL_SUPPLEMENT)
        for t in raw_tokens
    )
    if not has_unknown:
        return query, []

    corrected_query = query
    corrections: List[SpellCorrection] = []
    replaced_tokens: Set[str] = set()

    # Step 1: Scan Multi-word n-grams (3-grams and 2-grams)
    words = re.findall(r"[\w'-]+", query)
    for n in (3, 2):
        if len(words) < n:
            continue
        for i in range(len(words) - n + 1):
            span_words = words[i:i+n]
            # If start or end is generic stop word, skip phrase matching
            if span_words[0].lower() in STOP_WORDS or span_words[-1].lower() in STOP_WORDS:
                continue

            phrase = " ".join(span_words)
            phrase_lower = phrase.lower()

            if phrase_lower in replaced_tokens:
                continue

            phrase_match = checker.fuzzy_match_phrase(phrase_lower, threshold=similarity_threshold + 0.04)
            if phrase_match:
                canonical, score, top_cands, mesh_info = phrase_match
                for w in span_words:
                    replaced_tokens.add(w.lower())
                for w in canonical.split():
                    replaced_tokens.add(w.lower())

                pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
                corrected_query = pattern.sub(canonical, corrected_query, count=1)

                corrections.append(SpellCorrection(
                    original_term=phrase,
                    corrected_term=canonical,
                    mesh_id=mesh_info.get("mesh_id"),
                    mesh_heading=mesh_info.get("mesh_heading", canonical.title()),
                    confidence=round(score, 3),
                    candidates=top_cands
                ))

    # Step 2: Scan Single Tokens
    tokens = re.findall(r"[\w'-]+", corrected_query)
    for token in tokens:
        token_clean = token.strip().lower()
        if (token_clean in STOP_WORDS or 
            token_clean in PROTECTED_ACRONYMS or 
            len(token_clean) < 4 or 
            token_clean in replaced_tokens):
            continue

        match_res = checker.fuzzy_match_token(token_clean, threshold=similarity_threshold)
        if match_res:
            canonical, score, top_cands, mesh_info = match_res
            replaced_tokens.add(token_clean)
            for w in canonical.split():
                replaced_tokens.add(w.lower())

            pattern = re.compile(r'\b' + re.escape(token) + r'\b', re.IGNORECASE)
            corrected_query = pattern.sub(canonical, corrected_query, count=1)

            corrections.append(SpellCorrection(
                original_term=token,
                corrected_term=canonical,
                mesh_id=mesh_info.get("mesh_id"),
                mesh_heading=mesh_info.get("mesh_heading", canonical.title()),
                confidence=round(score, 3),
                candidates=top_cands
            ))

    return corrected_query, corrections
