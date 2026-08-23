import os
import gzip
import pickle
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Set, Any, Optional, Tuple

logger = logging.getLogger(__name__)

POSSIBLE_DATA_DIRS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data")),            # backend/data (Primary)
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")),       # pubmed-semantic-search/data
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data")), # workspace/data
    r"E:\cognt\BetaGenx\data"
]

CACHE_PATH = ""
XML_PATH = ""

# 1. First priority: look for pre-compiled compressed cache (best for production / deploy)
for d in POSSIBLE_DATA_DIRS:
    candidate_cache = os.path.join(d, "mesh_dictionary_cache.pkl.gz")
    if os.path.exists(candidate_cache):
        CACHE_PATH = candidate_cache
        XML_PATH = os.path.join(d, "Offline Dictionary.xml")
        break

# 2. Second priority: look for raw XML file if cache not found
if not CACHE_PATH:
    for d in POSSIBLE_DATA_DIRS:
        candidate_xml = os.path.join(d, "Offline Dictionary.xml")
        if os.path.exists(candidate_xml):
            XML_PATH = candidate_xml
            CACHE_PATH = os.path.join(d, "mesh_dictionary_cache.pkl.gz")
            break

# 3. Default fallback paths
if not CACHE_PATH:
    default_dir = POSSIBLE_DATA_DIRS[0]
    CACHE_PATH = os.path.join(default_dir, "mesh_dictionary_cache.pkl.gz")
    XML_PATH = os.path.join(default_dir, "Offline Dictionary.xml")


class MeshDictionaryManager:
    _instance: Optional['MeshDictionaryManager'] = None

    def __init__(self):
        self.descriptors: Dict[str, Dict[str, Any]] = {}  # mesh_id -> {name, synonyms, tree_numbers}
        self.term_to_mesh: Dict[str, str] = {}            # lower_term -> mesh_id
        self.canonical_names: Set[str] = set()
        self.single_word_vocab: List[str] = []
        self.multi_word_vocab: List[str] = []
        self.is_loaded: bool = False

    @classmethod
    def get_instance(cls) -> 'MeshDictionaryManager':
        if cls._instance is None:
            cls._instance = MeshDictionaryManager()
            cls._instance.load()
        return cls._instance

    def load(self, force_rebuild: bool = False):
        """Loads from compressed cache if available, otherwise parses Offline Dictionary.xml"""
        if self.is_loaded and not force_rebuild:
            return

        if not force_rebuild and os.path.exists(CACHE_PATH):
            try:
                logger.info(f"Loading MeSH dictionary from compressed cache: {CACHE_PATH}")
                with gzip.open(CACHE_PATH, "rb") as f:
                    data = pickle.load(f)
                    self.descriptors = data["descriptors"]
                    self.term_to_mesh = data["term_to_mesh"]
                    self.canonical_names = data["canonical_names"]
                    self.single_word_vocab = data["single_word_vocab"]
                    self.multi_word_vocab = data["multi_word_vocab"]
                    self.is_loaded = True
                    logger.info(f"Successfully loaded {len(self.descriptors):,} MeSH descriptors ({len(self.term_to_mesh):,} indexed terms) from cache.")
                    return
            except Exception as e:
                logger.warning(f"Failed to load cache ({e}), falling back to XML parsing.")

        # Parse from XML
        if os.path.exists(XML_PATH):
            self._parse_xml(XML_PATH)
            self._save_cache()
        else:
            logger.warning(f"MeSH XML dictionary not found at {XML_PATH}. Using fallback dataset.")
            self._load_fallback()

        self.is_loaded = True

    def _parse_xml(self, xml_path: str):
        logger.info(f"Parsing NLM MeSH XML file: {xml_path} (This takes a few seconds on first run)...")
        descriptors: Dict[str, Dict[str, Any]] = {}
        term_to_mesh: Dict[str, str] = {}
        canonical_names: Set[str] = set()

        try:
            for event, elem in ET.iterparse(xml_path, events=('end',)):
                if elem.tag == 'DescriptorRecord':
                    d_ui = elem.findtext('DescriptorUI')
                    d_name = elem.findtext('DescriptorName/String')

                    if d_ui and d_name:
                        d_name_clean = d_name.strip()
                        canonical_names.add(d_name_clean)

                        # Extract synonyms / terms
                        synonyms: Set[str] = set()
                        for term in elem.findall('.//TermList/Term/String'):
                            if term.text and term.text.strip():
                                t_clean = term.text.strip()
                                if t_clean.lower() != d_name_clean.lower():
                                    synonyms.add(t_clean)

                        # Extract Tree Numbers (Categories)
                        tree_numbers: List[str] = []
                        for tn in elem.findall('.//TreeNumberList/TreeNumber'):
                            if tn.text:
                                tree_numbers.append(tn.text.strip())

                        descriptors[d_ui] = {
                            "mesh_id": d_ui,
                            "mesh_heading": d_name_clean,
                            "synonyms": list(synonyms)[:15],
                            "tree_numbers": tree_numbers
                        }

                        term_to_mesh[d_name_clean.lower()] = d_ui
                        for syn in synonyms:
                            syn_lower = syn.lower()
                            if syn_lower not in term_to_mesh:
                                term_to_mesh[syn_lower] = d_ui

                    elem.clear()

            self.descriptors = descriptors
            self.term_to_mesh = term_to_mesh
            self.canonical_names = canonical_names
            self._build_vocabularies()
            logger.info(f"Parsed {len(descriptors):,} MeSH descriptors with {len(term_to_mesh):,} vocabulary terms.")

        except Exception as e:
            logger.error(f"Error parsing MeSH XML: {e}")
            self._load_fallback()

    def _build_vocabularies(self):
        single_words = set()
        multi_words = set()

        for term in self.term_to_mesh.keys():
            words = term.split()
            if len(words) == 1:
                if len(term) >= 3:
                    single_words.add(term)
            elif len(words) <= 4:
                multi_words.add(term)

        self.single_word_vocab = sorted(list(single_words))
        self.multi_word_vocab = sorted(list(multi_words), key=lambda x: len(x.split()), reverse=True)

    def _save_cache(self):
        try:
            logger.info(f"Saving compiled MeSH cache to {CACHE_PATH}...")
            data = {
                "descriptors": self.descriptors,
                "term_to_mesh": self.term_to_mesh,
                "canonical_names": self.canonical_names,
                "single_word_vocab": self.single_word_vocab,
                "multi_word_vocab": self.multi_word_vocab
            }
            with gzip.open(CACHE_PATH, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            logger.info("MeSH dictionary cache saved successfully.")
        except Exception as e:
            logger.warning(f"Could not save MeSH cache: {e}")

    def _load_fallback(self):
        """Minimal fallback in case XML is absent."""
        fallback_data = {
            "D004559": {"mesh_id": "D004559", "mesh_heading": "Metformin", "synonyms": ["Glucophage", "Dimethylbiguanide"]},
            "D003920": {"mesh_id": "D003920", "mesh_heading": "Diabetes Mellitus", "synonyms": ["Diabetes"]},
            "D003924": {"mesh_id": "D003924", "mesh_heading": "Diabetes Mellitus, Type 2", "synonyms": ["Type 2 Diabetes", "T2DM"]},
            "D000077543": {"mesh_id": "D000077543", "mesh_heading": "Glucagon-Like Peptide-1 Receptor Agonists", "synonyms": ["GLP-1", "Semaglutide", "Ozempic", "Liraglutide"]},
            "D002318": {"mesh_id": "D002318", "mesh_heading": "Cardiovascular Diseases", "synonyms": ["Heart Disease", "CVD"]},
            "D006973": {"mesh_id": "D006973", "mesh_heading": "Hypertension", "synonyms": ["High Blood Pressure", "HTN"]},
            "D009203": {"mesh_id": "D009203", "mesh_heading": "Myocardial Infarction", "synonyms": ["Heart Attack", "MI"]},
            "D008545": {"mesh_id": "D008545", "mesh_heading": "Melanoma", "synonyms": ["Malignant Melanoma"]},
            "D000074322": {"mesh_id": "D000074322", "mesh_heading": "Pembrolizumab", "synonyms": ["Keytruda"]},
            "D019161": {"mesh_id": "D019161", "mesh_heading": "Hydroxymethylglutaryl-CoA Reductase Inhibitors", "synonyms": ["Statins", "Atorvastatin"]},
            "D001241": {"mesh_id": "D001241", "mesh_heading": "Aspirin", "synonyms": ["Acetylsalicylic Acid"]},
            "D000544": {"mesh_id": "D000544", "mesh_heading": "Alzheimer Disease", "synonyms": ["Alzheimers", "Dementia"]},
        }
        self.descriptors = fallback_data
        for ui, entry in fallback_data.items():
            self.canonical_names.add(entry["mesh_heading"])
            self.term_to_mesh[entry["mesh_heading"].lower()] = ui
            for s in entry["synonyms"]:
                self.term_to_mesh[s.lower()] = ui
        self._build_vocabularies()

    def get_mesh_entry(self, term: str) -> Optional[Dict[str, Any]]:
        t_clean = term.strip().lower()
        mesh_id = self.term_to_mesh.get(t_clean)
        if mesh_id and mesh_id in self.descriptors:
            return self.descriptors[mesh_id]
        return None
