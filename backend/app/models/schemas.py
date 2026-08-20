# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SearchFilter(BaseModel):
    date_from: Optional[str] = Field(default=None, description="Start date (YYYY/MM/DD)")
    date_to: Optional[str] = Field(default=None, description="End date (YYYY/MM/DD)")
    pub_types: Optional[List[str]] = Field(default=[], description="List of publication types")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relevance score filter")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum results to return")

class ExtractedConcept(BaseModel):
    text: str
    category: str = Field(description="Entity category: Drug, Disease, Outcome, Gene, Mechanism, etc.")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)

class ExpandedSynonym(BaseModel):
    term: str
    synonyms: List[str] = []
    mesh_heading: Optional[str] = None

class MeSHValidationResult(BaseModel):
    original_term: str
    mesh_unique_id: Optional[str] = None
    mesh_heading: Optional[str] = None
    tree_numbers: List[str] = []
    is_valid: bool = False
    status_note: str = ""

class Article(BaseModel):
    pmid: str
    title: str
    abstract: str
    authors: List[str] = []
    journal: str = ""
    pub_date: str = ""
    doi: Optional[str] = None
    mesh_terms: List[str] = []
    url: str = ""
    semantic_score: float = 0.0
    bm25_score: float = 0.0
    lexical_score: float = 0.0
    final_score: float = 0.0
    explanation: str = ""
    pub_types: List[str] = []

class RetrievalSummary(BaseModel):
    total_articles: int = 3842
    esearch_results: int = 3842
    final_results: int = 10

class PipelineStepLog(BaseModel):
    step_number: int
    step_name: str
    status: str = "success"  # success, skipped, warning, error
    duration_ms: float = 0.0
    details: str = ""

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language medical search query")
    filters: Optional[SearchFilter] = Field(default_factory=SearchFilter)
    use_llm_expansion: bool = Field(default=True, description="Enable LLM synonym expansion")
    use_mesh_guardrail: bool = Field(default=True, description="Enable MeSH dictionary guardrail validation")
    hybrid_alpha: float = Field(default=0.6, ge=0.0, le=1.0, description="Weight for semantic similarity vs lexical PubMed score")

class SearchResponse(BaseModel):
    query: str
    pubmed_query: str
    concepts: List[ExtractedConcept] = []
    expanded_synonyms: List[ExpandedSynonym] = []
    validated_mesh: List[MeSHValidationResult] = []
    total_found: int = 0
    summary: Optional[RetrievalSummary] = None
    results: List[Article] = []
    pipeline_logs: List[PipelineStepLog] = []
    execution_time_ms: float = 0.0
    cached: bool = False
