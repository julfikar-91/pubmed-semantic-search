import time
import requests

queries = [
    "What are the effects of metformin on type 2 diabetes?",
    "effects of metformn on type 2 diabtes and renal functon",
    "checkpoint inhibitors in lung cancer",
    "cardiovascular effects of statins"
]

print("\n" + "="*70)
print("PUBMED SEMANTIC SEARCH LATENCY BENCHMARK (< 2.0s TARGET)")
print("="*70)

for idx, q in enumerate(queries, 1):
    t0 = time.time()
    try:
        resp = requests.post(
            "http://127.0.0.1:8000/api/search",
            json={
                "query": q,
                "use_spell_correction": True,
                "use_llm_expansion": True,
                "use_mesh_guardrail": True,
                "hybrid_alpha": 0.6
            },
            timeout=10
        )
        total_time_sec = time.time() - t0
        data = resp.json()
        exec_ms = data.get("execution_time_ms", 0)
        articles = len(data.get("results", []))
        cached = data.get("cached", False)

        status_text = "PASS (<2s)" if total_time_sec < 2.0 else "SLOW"

        print(f"[{idx}] {status_text}")
        print(f"    Query        : {q}")
        print(f"    Total Latency: {total_time_sec:.3f} seconds")
        print(f"    Server Time  : {exec_ms:.1f} ms")
        print(f"    Results      : {articles} articles (Cached: {cached})")
        print("-" * 70)
    except Exception as e:
        print(f"[{idx}] Request failed: {e}")

print("="*70 + "\n")
