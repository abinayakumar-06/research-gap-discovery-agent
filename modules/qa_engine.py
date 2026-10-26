"""
modules/qa_engine.py
--------------------
Evidence-Grounded Semantic Search & Academic Q&A Engine.
Retrieves relevant passages across uploaded research papers using semantic similarity,
extracts source provenance (paper title, section name, exact page number), and generates
synthesized answers strictly grounded in the retrieved text.
Integrity Rules:
- If retrieved evidence is insufficient, explicitly states:
  'Insufficient evidence found in the uploaded collection to substantiate this claim.'
- Restricts analysis to the project collection unless external literature search is explicitly toggled.
"""

from typing import List, Dict, Any, Optional
import re
from database import get_papers, get_all_sections
from modules.embeddings import semantic_engine

class GroundedQAEngine:
    """Answers research questions strictly grounded in uploaded document sections."""

    def __init__(self):
        pass

    def search_evidence(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieves top-k evidence passages matching query with page references."""
        sections = get_all_sections()
        if not sections or not query:
            return []

        ranked = semantic_engine.rank_passages(query, sections, top_k=top_k)
        return ranked

    def answer_query(self, query: str, top_k: int = 4) -> Dict[str, Any]:
        """
        Retrieves passages and generates a grounded response with source citations.
        """
        if not query or len(query.strip()) < 3:
            return {
                "query": query,
                "answer": "Please provide a specific research query regarding methodologies, datasets, metrics, limitations, or future directions.",
                "sources": [],
                "confidence": 0.0,
                "sufficient_evidence": False
            }

        passages = self.search_evidence(query, top_k=top_k)

        # Check evidence threshold
        if not passages or passages[0].get("similarity_score", 0.0) < 0.12:
            return {
                "query": query,
                "answer": (
                    "Insufficient evidence in the uploaded collection to substantiate an answer to this query. "
                    "The documents do not contain passages with sufficient semantic correspondence to this specific question. "
                    "To verify this claim, consider uploading additional literature in the Paper Library."
                ),
                "sources": passages[:2] if passages else [],
                "confidence": 0.1,
                "sufficient_evidence": False
            }

        # Formulate grounded synthesis
        sources = []
        evidence_bullets = []
        for i, p in enumerate(passages, start=1):
            title = p.get("paper_title", "Research Paper")
            page = p.get("page_num", 1)
            sec = p.get("section_name", "General")
            score = p.get("similarity_score", 0.0)
            content = p.get("content", "").strip()
            
            # Extract key snippet
            first_sent = content.split(". ")[0] + "."
            snippet = content[:280] + ("..." if len(content) > 280 else "")

            sources.append({
                "source_id": i,
                "paper_title": title,
                "section": sec,
                "page": page,
                "similarity_score": score,
                "passage_snippet": snippet
            })

            evidence_bullets.append(f"[{i}] {title} (Page {page}, {sec}):\n\"{snippet}\"")

        grounded_answer = (
            f"Based strictly on evidence retrieved from the uploaded literature collection, here are the documented findings regarding '{query}':\n\n"
            + "\n\n".join(evidence_bullets)
            + "\n\nSynthesis Summary: The cited passages above constitute the direct textual evidence extracted from the collection. "
            "Passages are provided verbatim with page numbers for independent peer verification."
        )

        return {
            "query": query,
            "answer": grounded_answer,
            "sources": sources,
            "confidence": passages[0].get("similarity_score", 0.5),
            "sufficient_evidence": True
        }

qa_engine = GroundedQAEngine()
