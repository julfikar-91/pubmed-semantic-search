import pytest
import asyncio
from app.models.schemas import ExpandedSynonym
from app.pipeline.validate_mesh import validate_mesh

# 1. Valid Ground-Truth MeSH Terms
VALID_MESH_CASES = [
    ExpandedSynonym(term="metformin", synonyms=["Glucophage"], mesh_heading="Metformin"),
    ExpandedSynonym(term="type 2 diabetes", synonyms=["T2DM"], mesh_heading="Diabetes Mellitus, Type 2"),
    ExpandedSynonym(term="myocardial infarction", synonyms=["heart attack"], mesh_heading="Myocardial Infarction"),
    ExpandedSynonym(term="hypertension", synonyms=["high blood pressure"], mesh_heading="Hypertension"),
    ExpandedSynonym(term="asthma", synonyms=["bronchial asthma"], mesh_heading="Asthma"),
    ExpandedSynonym(term="melanoma", synonyms=["malignant melanoma"], mesh_heading="Melanoma"),
    ExpandedSynonym(term="pembrolizumab", synonyms=["Keytruda"], mesh_heading="Pembrolizumab"),
]

# 2. Adversarial & Fabricated / Hallucinated Terms
HALLUCINATED_TERMS = [
    ExpandedSynonym(term="metformin-induced hyperleptinemia", synonyms=["leptin overgrowth"], mesh_heading="Hyperleptinemia Metformin Disorder"),
    ExpandedSynonym(term="coronary pseudo-carditis", synonyms=["fake carditis"], mesh_heading="Pseudo-Carditis Coronaria"),
    ExpandedSynonym(term="pancreatic litholysis drug X", synonyms=["litho-dissolve"], mesh_heading="Litholysis Pancreatica Maxima"),
    ExpandedSynonym(term="neuro-glioma-3 mutant variant", synonyms=["glioma-3"], mesh_heading="Glioma Type 3 Subclass"),
    ExpandedSynonym(term="synthetic super-aspirin 9000", synonyms=["super-asa"], mesh_heading="Super-Acetylsalicylic Acid"),
    ExpandedSynonym(term="anti-aging telomere multiplier", synonyms=["telomere pill"], mesh_heading="Telomere Elongation Therapy Complex"),
]

@pytest.mark.asyncio
async def test_mesh_guardrail_accepts_valid_terms():
    """Verify that legitimate medical terms are approved with valid MeSH IDs."""
    results = await validate_mesh(VALID_MESH_CASES, enabled=True)
    assert len(results) == len(VALID_MESH_CASES)
    for res in results:
        assert res.is_valid is True, f"Expected {res.original_term} to be valid"
        assert res.mesh_heading is not None
        assert res.mesh_unique_id is not None or "Verified" in res.status_note

@pytest.mark.asyncio
async def test_mesh_guardrail_rejects_hallucinations():
    """Verify that LLM-hallucinated or non-existent medical terms are strictly rejected."""
    results = await validate_mesh(HALLUCINATED_TERMS, enabled=True)
    assert len(results) == len(HALLUCINATED_TERMS)
    for res in results:
        assert res.is_valid is False, f"Guardrail failed! Hallucinated term was accepted: '{res.mesh_heading}'"
        assert "Rejected" in res.status_note

@pytest.mark.asyncio
async def test_mesh_guardrail_disabled_passthrough():
    """Verify that disabling guardrail permits passthrough with explanatory note."""
    results = await validate_mesh(HALLUCINATED_TERMS, enabled=False)
    for res in results:
        assert res.is_valid is True
        assert "Guardrail disabled" in res.status_note

if __name__ == "__main__":
    asyncio.run(test_mesh_guardrail_accepts_valid_terms())
    asyncio.run(test_mesh_guardrail_rejects_hallucinations())
    print("All MeSH Guardrail stress tests passed successfully!")
