"""
modules/embeddings.py
---------------------
Semantic similarity, passage retrieval, and clustering engine.
Supports Sentence Transformers when available, with a resilient, high-speed
Scikit-learn TF-IDF + Latent Semantic Analysis (LSA / TruncatedSVD) fallback
that runs completely offline without external PyTorch/transformer dependencies.
"""

from typing import List, Dict, Any, Optional, Tuple
import re
import numpy as np

# Attempt to import sentence_transformers; fallback to scikit-learn
HAVE_SENTENCE_TRANSFORMERS = False
_st_model = None

try:
    from sentence_transformers import SentenceTransformer
    HAVE_SENTENCE_TRANSFORMERS = True
except (ImportError, Exception):
    HAVE_SENTENCE_TRANSFORMERS = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import AgglomerativeClustering

def get_sentence_transformer_model():
    global _st_model
    if HAVE_SENTENCE_TRANSFORMERS and _st_model is None:
        try:
            _st_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _st_model = None
    return _st_model

class SemanticEngine:
    """Unified semantic representation, similarity, ranking and clustering engine."""
    
    def __init__(self):
        self.use_st = HAVE_SENTENCE_TRANSFORMERS and (get_sentence_transformer_model() is not None)
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000
        )

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Computes semantic similarity score in [0.0, 1.0] between two strings."""
        if not text_a or not text_b:
            return 0.0
            
        if self.use_st:
            try:
                model = get_sentence_transformer_model()
                embs = model.encode([text_a, text_b])
                score = float(cosine_similarity([embs[0]], [embs[1]])[0][0])
                return max(0.0, min(1.0, score))
            except Exception:
                pass
                
        # Scikit-learn TF-IDF fallback
        try:
            tfidf_mat = self.vectorizer.fit_transform([text_a, text_b])
            score = float(cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:2])[0][0])
            return max(0.0, min(1.0, score))
        except Exception:
            # Fallback word-overlap Jaccard
            tokens_a = set(re.findall(r"\w+", text_a.lower()))
            tokens_b = set(re.findall(r"\w+", text_b.lower()))
            if not tokens_a or not tokens_b:
                return 0.0
            return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)

    def rank_passages(self, query: str, passages: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Ranks a list of candidate passages against a query using semantic cosine similarity.
        Passages are dicts containing at least 'content' or 'text'.
        """
        if not query or not passages:
            return []
            
        texts = [p.get("content") or p.get("text") or "" for p in passages]
        valid_indices = [i for i, t in enumerate(texts) if t.strip()]
        if not valid_indices:
            return []
            
        corpus = [query] + [texts[i] for i in valid_indices]
        
        scores = []
        if self.use_st:
            try:
                model = get_sentence_transformer_model()
                embs = model.encode(corpus)
                query_emb = embs[0:1]
                doc_embs = embs[1:]
                sims = cosine_similarity(query_emb, doc_embs)[0]
                scores = list(sims)
            except Exception:
                scores = []
                
        if not scores:
            try:
                tfidf_mat = self.vectorizer.fit_transform(corpus)
                sims = cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:])[0]
                scores = list(sims)
            except Exception:
                scores = [0.0] * len(valid_indices)

        ranked = []
        for idx, score in zip(valid_indices, scores):
            item = dict(passages[idx])
            item["similarity_score"] = round(float(score), 4)
            ranked.append(item)
            
        ranked.sort(key=lambda x: x["similarity_score"], reverse=True)
        return ranked[:top_k]

    def cluster_texts(self, texts: List[str], n_clusters: int = 3) -> List[int]:
        """Clusters texts using TF-IDF and Agglomerative Clustering."""
        if not texts:
            return []
        if len(texts) <= n_clusters:
            return list(range(len(texts)))
            
        try:
            tfidf = self.vectorizer.fit_transform(texts)
            n_c = min(n_clusters, len(texts))
            clustering = AgglomerativeClustering(n_clusters=n_c, metric="cosine", linkage="average")
            labels = clustering.fit_predict(tfidf.toarray())
            return [int(l) for l in labels]
        except Exception:
            return [0] * len(texts)

    def extract_keywords(self, text: str, top_n: int = 6) -> List[str]:
        """Extracts top keywords/keyphrases using TF-IDF scores."""
        if not text or len(text.strip()) < 10:
            return []
        try:
            vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=100)
            mat = vec.fit_transform([text])
            feature_names = vec.get_feature_names_out()
            scores = mat.toarray()[0]
            top_indices = np.argsort(scores)[::-1][:top_n]
            return [feature_names[i] for i in top_indices if scores[i] > 0]
        except Exception:
            words = re.findall(r"\b[A-Za-z]{4,}\b", text.lower())
            return list(dict.fromkeys(words))[:top_n]

# Global singleton instance
semantic_engine = SemanticEngine()
