import React, { useState } from 'react';
import { ChevronDown, ChevronLeft, ChevronRight, Loader2, SearchX } from 'lucide-react';
import { SearchBar } from '../components/SearchBar';
import { PipelineStepper } from '../components/PipelineStepper';
import { QueryProcessingDetails } from '../components/QueryProcessingDetails';
import { ResultCard } from '../components/ResultCard';
import { executeSemanticSearch } from '../api/searchApi';
import { SearchResponse } from '../types';

export const SearchPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [activeStep, setActiveStep] = useState(1);
  const [sortBy, setSortBy] = useState("Hybrid Score");
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (queryText: string, bypassSpellCorrection = false) => {
    setIsLoading(true);
    setError(null);
    setActiveStep(1);

    try {
      const res = await executeSemanticSearch({
        query: queryText,
        use_spell_correction: !bypassSpellCorrection,
        use_llm_expansion: true,
        use_mesh_guardrail: true,
        hybrid_alpha: 0.6,
      });
      setResponse(res);
      setActiveStep(7);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to execute search query against PubMed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="biosearch-page-container">
      <SearchBar onSearch={(q) => handleSearch(q, false)} isLoading={isLoading} />

      {response && (
        <PipelineStepper currentStep={activeStep} onStepClick={(s) => setActiveStep(s)} />
      )}

      {isLoading ? (
        <div className="search-loading-container">
          <Loader2 className="spinner-icon text-blue-600" size={36} />
          <p className="mt-2 text-slate-600 font-medium">Executing 8-step pipeline: Fuzzy MeSH Check → Concept Extraction → NCBI ESearch → Vector Embedding → Hybrid Reranking...</p>
        </div>
      ) : error ? (
        <div className="error-card bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-center my-6">
          <p>{error}</p>
        </div>
      ) : response ? (
        <div className="biosearch-main-grid">
          {/* Left Column: Query Processing Details */}
          <aside className="grid-left-col">
            <QueryProcessingDetails
              originalQuery={response.query}
              correctedQuery={response.corrected_query}
              concepts={response.concepts}
              validatedMesh={response.validated_mesh}
              expandedSynonyms={response.expanded_synonyms}
              pubmedQuery={response.pubmed_query}
              summary={response.summary}
              spellCorrections={response.spell_corrections}
              pipelineLogs={response.pipeline_logs}
              executionTimeMs={response.execution_time_ms}
              cached={response.cached}
            />
          </aside>

          {/* Right Column: Top Re-ranked Results */}
          <main className="grid-right-col">
            {response.corrected_query && response.corrected_query !== response.query && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between text-xs text-blue-900 shadow-sm">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-blue-800">Showing results for:</span>
                  <span className="font-bold text-blue-950 underline decoration-blue-400 underline-offset-2">
                    {response.corrected_query}
                  </span>
                  <span className="text-slate-500 italic ml-1">
                    (Search instead for{" "}
                    <button
                      type="button"
                      onClick={() => handleSearch(response.query, true)}
                      className="underline cursor-pointer text-blue-700 hover:text-blue-900 font-medium"
                    >
                      {response.query}
                    </button>
                    )
                  </span>
                </div>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full font-medium text-[11px]">
                  MeSH Auto-Corrected
                </span>
              </div>
            )}

            <div className="results-card-container">
              <div className="results-header-row">
                <h2 className="results-title">Re-ranked Results ({response.results.length})</h2>
                <div className="sort-dropdown-wrapper">
                  <span className="sort-label">Sort by:</span>
                  <div className="sort-select-box">
                    <span>{sortBy}</span>
                    <ChevronDown size={14} />
                  </div>
                </div>
              </div>

              {response.results.length === 0 ? (
                <div className="no-results-box text-center py-12 text-slate-500">
                  <SearchX size={40} className="mx-auto mb-3 text-slate-400" />
                  <p className="font-semibold text-slate-700">No PubMed articles matched this search criteria.</p>
                  <p className="text-xs text-slate-500 mt-1">Try refining your query or searching with different clinical terms.</p>
                </div>
              ) : (
                <div className="results-items-list">
                  {response.results.map((article, idx) => (
                    <ResultCard key={article.pmid || idx} article={article} rank={idx + 1} />
                  ))}
                </div>
              )}

              {/* Bottom Pagination Bar */}
              {response.results.length > 0 && (
                <div className="results-pagination-footer">
                  <span className="pagination-info">
                    Showing 1 to {response.results.length} of {response.total_found || response.results.length} results
                  </span>

                  <div className="pagination-controls">
                    <button type="button" className="btn-page-nav disabled">
                      <ChevronLeft size={14} /> Previous
                    </button>
                    <button type="button" className="btn-page-num active">
                      1
                    </button>
                    <button type="button" className="btn-page-nav disabled">
                      Next <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          </main>
        </div>
      ) : (
        <div className="empty-search-prompt text-center py-12 text-slate-400">
          <p className="text-sm font-medium">Enter a medical query above or click one of the preset examples to search live PubMed literature.</p>
        </div>
      )}
    </div>
  );
};
