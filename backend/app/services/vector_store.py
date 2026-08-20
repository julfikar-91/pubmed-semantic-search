import numpy as np
from typing import List, Tuple, Dict, Any, Optional

try:
    # pyrefly: ignore [missing-import]
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

class VectorStore:
    """FAISS-backed vector store with automatic numpy fallback."""
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.doc_ids: List[str] = []
        self.vectors: List[np.ndarray] = []
        self.index = None

        if HAS_FAISS:
            self.index = faiss.IndexFlatIP(dimension)

    def add_vectors(self, ids: List[str], embeddings: np.ndarray) -> None:
        """Add normalized embeddings to index."""
        if len(ids) == 0 or len(embeddings) == 0:
            return

        embeddings = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = embeddings / norms

        self.doc_ids.extend(ids)
        self.vectors.extend(normalized)

        if HAS_FAISS and self.index is not None:
            self.index.add(normalized)

    def search(self, query_vector: np.ndarray, top_k: int = 20) -> List[Tuple[str, float]]:
        """Search top_k nearest documents to query_vector."""
        if len(self.doc_ids) == 0:
            return []

        query_vec = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec = query_vec / norm

        top_k = min(top_k, len(self.doc_ids))

        if HAS_FAISS and self.index is not None and self.index.ntotal > 0:
            scores, indices = self.index.search(query_vec, top_k)
            results = []
            for idx, score in zip(indices[0], scores[0]):
                if 0 <= idx < len(self.doc_ids):
                    sim = float(np.clip(score, 0.0, 1.0))
                    results.append((self.doc_ids[idx], sim))
            return results
        else:
            matrix = np.array(self.vectors, dtype=np.float32)
            sims = np.dot(matrix, query_vec.T).squeeze()
            if matrix.shape[0] == 1:
                sims = np.array([sims])
            
            top_indices = np.argsort(sims)[::-1][:top_k]
            results = []
            for idx in top_indices:
                sim = float(np.clip(sims[idx], 0.0, 1.0))
                results.append((self.doc_ids[idx], sim))
            return results

    def clear(self) -> None:
        self.doc_ids = []
        self.vectors = []
        if HAS_FAISS:
            self.index = faiss.IndexFlatIP(self.dimension)

def create_vector_store(dimension: int = 384) -> VectorStore:
    return VectorStore(dimension=dimension)
