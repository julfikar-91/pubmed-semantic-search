import sys
import time
import asyncio
import numpy as np
from typing import List
from app.models.schemas import Article
from app.services.vector_store import create_vector_store
from app.pipeline.embed_and_score import embed_and_score_articles
from app.pipeline.rerank import rerank_and_fuse
from app.config import settings

def generate_mock_articles(count: int) -> List[Article]:
    """Generates synthetic candidate PubMed articles for load & latency testing."""
    articles = []
    topics = [
        ("Type 2 Diabetes Mellitus", "Clinical investigation on metformin and glycemic control in adult patients with metabolic syndrome."),
        ("Semaglutide Weight Loss", "Randomized trial evaluating GLP-1 receptor agonist semaglutide on body weight reduction and cardiovascular risk."),
        ("Myocardial Infarction", "Secondary prevention outcomes using high-intensity statins and dual antiplatelet therapy in acute coronary syndrome."),
        ("Pembrolizumab Melanoma", "Phase 3 overall survival analysis of anti-PD-1 checkpoint inhibitor monotherapy in metastatic melanoma."),
        ("Chronic Kidney Disease", "Renal protection and reduction in eGFR decline with sodium-glucose cotransporter 2 (SGLT2) inhibitors in CKD."),
        ("Alzheimer Disease Pathology", "Amyloid beta clearance and cognitive trajectory in mild cognitive impairment treated with monoclonal antibodies."),
        ("Rheumatoid Arthritis", "Longitudinal efficacy of tumor necrosis factor alpha inhibitors versus methotrexate in active rheumatoid arthritis.")
    ]

    for i in range(1, count + 1):
        topic_title, topic_abs = topics[i % len(topics)]
        title = f"{topic_title} - Multi-Center Trial Volume {i}"
        abstract = f"{topic_abs} Results demonstrate statistically significant clinical improvements (p < 0.001) across cohort {i}."
        
        articles.append(Article(
            pmid=str(10000000 + i),
            title=title,
            abstract=abstract,
            authors=[f"Researcher {i}A", f"Researcher {i}B"],
            journal="New England Journal of Medicine",
            pub_date="2025/01/15",
            bm25_score=round(max(0.3, 0.95 - (i * 0.001)), 3),
            lexical_score=round(max(0.3, 0.95 - (i * 0.001)), 3),
            pub_types=["Clinical Trial", "Journal Article"]
        ))
    return articles

def benchmark_pool_scaling():
    """Tests latency of Vector Embedding + FAISS/Cosine Similarity + Reranking across pool sizes."""
    pool_sizes = [20, 50, 100, 200, 500]
    query = "semaglutide for weight reduction and cardiovascular outcomes in type 2 diabetes"

    print("\n================================================================================")
    print("LOAD TEST: VECTOR EMBEDDING & RERANK SCALING BENCHMARK")
    print("================================================================================")
    print(f"{'Pool Size':<12} | {'Embed & Score (ms)':<20} | {'Rerank Fusion (ms)':<20} | {'Total Stage (ms)':<18}")
    print("-" * 80)

    for size in pool_sizes:
        articles = generate_mock_articles(size)
        vector_store = create_vector_store(dimension=settings.VECTOR_DIMENSION)

        t0 = time.time()
        scored = embed_and_score_articles(query, articles, vector_store)
        t1 = time.time()
        embed_ms = round((t1 - t0) * 1000, 2)

        t2 = time.time()
        reranked = rerank_and_fuse(scored, alpha=0.6)
        t3 = time.time()
        rerank_ms = round((t3 - t2) * 1000, 2)

        total_ms = round(embed_ms + rerank_ms, 2)
        print(f"{size:<12} | {embed_ms:<20.2f} | {rerank_ms:<20.2f} | {total_ms:<18.2f}")

    print("================================================================================\n")

async def benchmark_concurrency():
    """Simulates 30 simultaneous concurrent search requests through vector scoring."""
    query = "metformin and SGLT2 inhibitors renal protection"
    concurrency_count = 30
    articles_per_req = 50

    print("LOAD TEST: CONCURRENT BATCH REQUESTS (30 simultaneous queries)")
    print("-" * 80)

    async def single_worker(worker_id: int):
        articles = generate_mock_articles(articles_per_req)
        vector_store = create_vector_store(dimension=settings.VECTOR_DIMENSION)
        
        t0 = time.time()
        scored = embed_and_score_articles(query, articles, vector_store)
        reranked = rerank_and_fuse(scored, alpha=0.6)
        return (time.time() - t0) * 1000

    tasks = [single_worker(i) for i in range(concurrency_count)]
    t_start = time.time()
    latencies = await asyncio.gather(*tasks)
    total_batch_time = (time.time() - t_start) * 1000

    avg_lat = sum(latencies) / len(latencies)
    sorted_lats = sorted(latencies)
    p95_lat = sorted_lats[int(len(sorted_lats) * 0.95)]

    print(f"Total Concurrent Requests: {concurrency_count}")
    print(f"Batch Wall Clock Time:     {total_batch_time:.2f} ms")
    print(f"Average Request Latency:   {avg_lat:.2f} ms")
    print(f"P95 Request Latency:       {p95_lat:.2f} ms")
    print(f"Throughput:                {round((concurrency_count / (total_batch_time / 1000)), 1)} req/sec")
    print("================================================================================\n")

if __name__ == "__main__":
    benchmark_pool_scaling()
    asyncio.run(benchmark_concurrency())
