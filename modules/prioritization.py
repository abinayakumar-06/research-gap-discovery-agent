"""
modules/prioritization.py
-------------------------
Transparent, Deterministic Multi-Criteria Gap Prioritization Engine.
Calculates priority scores based on adjustable criteria weights using a documented,
reproducible mathematical formula:
  Score = 100 * sum(w_i * s_i) / sum(w_i)
Exposes the exact contribution of each criterion, clearly distinguishes evidence strength
from novelty, highlights missing information and uncertainty, and categorizes gaps into
High Priority, Medium Priority, and Exploratory tiers.
"""

from typing import List, Dict, Any, Optional, Tuple
from config import DEFAULT_PRIORITY_WEIGHTS, PRIORITY_LEVELS
from database import get_gaps, update_gap

class PrioritizationEngine:
    """Deterministic, transparent scoring engine for candidate research directions."""

    def __init__(self):
        pass

    @staticmethod
    def calculate_priority(
        gap: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculates deterministic priority score, criterion contributions,
        and uncertainty notes for a research gap.
        
        Formula:
          Score = 100 * [
            w_ev * evidence_strength +
            w_imp * impact +
            w_fea * feasibility +
            w_unadd * unaddressed_score +
            w_rec * recency
          ] / sum(weights)
        """
        w = weights or DEFAULT_PRIORITY_WEIGHTS.copy()
        
        # Raw normalized scores in [0.0, 1.0]
        s_ev = float(gap.get("evidence_strength", 0.5))
        s_imp = float(gap.get("impact", 0.5))
        s_fea = float(gap.get("feasibility", 0.5))
        s_unadd = float(gap.get("unaddressed_score", 0.5))
        s_rec = float(gap.get("recency", 0.5))

        w_ev = float(w.get("evidence_strength", 0.30))
        w_imp = float(w.get("impact", 0.25))
        w_fea = float(w.get("feasibility", 0.20))
        w_unadd = float(w.get("unaddressed_score", 0.15))
        w_rec = float(w.get("recency", 0.10))

        total_weight = w_ev + w_imp + w_fea + w_unadd + w_rec
        if total_weight <= 0:
            total_weight = 1.0

        # Weighted contributions out of 100
        contrib_ev = round((w_ev * s_ev / total_weight) * 100, 2)
        contrib_imp = round((w_imp * s_imp / total_weight) * 100, 2)
        contrib_fea = round((w_fea * s_fea / total_weight) * 100, 2)
        contrib_unadd = round((w_unadd * s_unadd / total_weight) * 100, 2)
        contrib_rec = round((w_rec * s_rec / total_weight) * 100, 2)

        final_score = round(contrib_ev + contrib_imp + contrib_fea + contrib_unadd + contrib_rec, 2)

        # Determine level
        if final_score >= PRIORITY_LEVELS["High"]["min_score"]:
            level = "High"
        elif final_score >= PRIORITY_LEVELS["Medium"]["min_score"]:
            level = "Medium"
        else:
            level = "Low"

        # Missing information and uncertainty analysis
        uncertainties = gap.get("uncertainties") or "None documented."
        missing_info = []
        if len(gap.get("source_paper_ids", [])) < 2:
            missing_info.append("Single-paper support: Needs corroborating evidence from external literature.")
        if s_fea < 0.70:
            missing_info.append("Feasibility risk: Hardware constraints or memory budgets may restrict real-time deployment.")
        if gap.get("category") == "contradictory":
            missing_info.append("Empirical divergence: Direct side-by-side benchmark required before commercial prototyping.")

        return {
            "priority_score": final_score,
            "priority_level": level,
            "contributions": {
                "Evidence Strength": contrib_ev,
                "Research Impact": contrib_imp,
                "Feasibility": contrib_fea,
                "Unaddressed Score": contrib_unadd,
                "Recency & Timeliness": contrib_rec
            },
            "raw_scores": {
                "evidence_strength": s_ev,
                "impact": s_imp,
                "feasibility": s_fea,
                "unaddressed_score": s_unadd,
                "recency": s_rec
            },
            "weights_used": w,
            "missing_info": missing_info,
            "uncertainty_summary": uncertainties,
            "methodology_disclaimer": (
                "NOTE: This score is a deterministic multi-criteria heuristic for portfolio prioritization. "
                "Evidence strength reflects internal citation density within the analyzed collection and "
                "must NOT be conflated with validated global novelty or academic peer consensus."
            )
        }

    def reorder_gaps(self, weights: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        Recalculates scores for all gaps in the database and updates their records.
        Returns the sorted list by priority_score descending.
        """
        gaps = get_gaps()
        scored_gaps = []

        for g in gaps:
            res = self.calculate_priority(g, weights)
            updates = {
                "priority_score": res["priority_score"],
                "priority_level": res["priority_level"]
            }
            if g.get("id"):
                update_gap(g["id"], updates)
                g.update(updates)
            g["scoring_details"] = res
            scored_gaps.append(g)

        scored_gaps.sort(key=lambda x: x["priority_score"], reverse=True)
        return scored_gaps

prioritization_engine = PrioritizationEngine()
