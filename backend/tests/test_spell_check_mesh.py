import time
import pytest
from app.pipeline.spell_correct import correct_biomedical_query, BiomedicalSpellChecker

def test_biomedical_spell_corrections():
    # Warmup / Singleton load
    BiomedicalSpellChecker.get_instance()

    cases = [
        ("What are the effects of metformn on type 2 diabtes?", "metformin", "diabetes"),
        ("semaglutid cardiovaskular outcoms", "semaglutide", "cardiovascular"),
        ("pembrolizumb in lung cancer", "pembrolizumab", "cancer"),
        ("aspirn and hypertenshun", "aspirin", "hypertension"),
    ]

    for q, exp_term1, exp_term2 in cases:
        t0 = time.time()
        corrected, corrs = correct_biomedical_query(q)
        duration_ms = (time.time() - t0) * 1000

        print(f"\nQuery: {q}")
        print(f"Corrected: {corrected} (took {duration_ms:.2f}ms)")
        for c in corrs:
            print(f"  Fix: '{c.original_term}' -> '{c.corrected_term}' [MeSH: {c.mesh_id}]")

        corrected_lower = corrected.lower()
        assert exp_term1 in corrected_lower
        assert len(corrs) >= 1
        assert duration_ms < 500  # Must be sub-second

if __name__ == "__main__":
    test_biomedical_spell_corrections()
    print("\nALL SPELL CORRECTION TESTS PASSED!")
