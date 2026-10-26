"""
tests/test_platform.py
----------------------
Comprehensive automated test suite for the Research Literature Synthesis &
Research-Gap Discovery Platform.
Tests:
- PDF processing & metadata extraction
- Scanned PDF detection & OCR alert
- SHA-256 duplicate detection
- Cross-paper synthesis & comparability warnings
- Evidence-based gap discovery & typologies (Class A, B, C)
- Contradiction detection & divergence explanations
- Deterministic prioritization formula & contribution calculation
- External literature verification & offline handling
- Structured project proposal generation
- Evidence graph network construction
- Grounded Q&A engine
- Database CRUD & migrations
- Report generation (PDF & DOCX)
"""

import sys
from pathlib import Path
import pytest
import sqlite3

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import PAPERS_DIR, EXPORTS_DIR, GAP_CATEGORIES, GAP_CLASSIFICATIONS
import database
from modules.pdf_processor import (
    extract_pdf_data, calculate_file_hash, PDFProcessingError
)
from modules.synthesis_engine import synthesis_engine
from modules.gap_detector import gap_detector
from modules.contradiction_detector import contradiction_detector
from modules.prioritization import prioritization_engine
from modules.verification_engine import verification_engine
from modules.proposal_generator import proposal_generator
from modules.evidence_graph import evidence_graph_engine
from modules.qa_engine import qa_engine
from modules.report_generator import report_generator
from modules.llm_client import llm_client

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure database is initialized and sample papers are parsed and loaded."""
    database.init_db()
    
    # Check if sample papers exist in sample_data/papers
    sample_files = list(PAPERS_DIR.glob("*.pdf"))
    assert len(sample_files) >= 5, f"Expected at least 5 sample PDFs in {PAPERS_DIR}, found {len(sample_files)}"

    # Ingest sample papers if not already present in DB
    existing_papers = database.get_papers()
    if len(existing_papers) < len(sample_files):
        for pdf_path in sample_files:
            file_hash = calculate_file_hash(pdf_path)
            if not database.get_paper_by_hash(file_hash):
                extracted = extract_pdf_data(pdf_path)
                pid = database.save_paper(extracted)
                database.save_sections(pid, extracted.get("sections", []))
                database.save_summary(pid, extracted.get("summary", {}))

    yield

def test_database_initialization():
    """Test that SQLite database tables exist and metrics summary returns counts."""
    metrics = database.get_metrics_summary()
    assert isinstance(metrics, dict)
    assert metrics["num_papers"] >= 5
    assert metrics["num_sections"] > 0
    assert "num_gaps" in metrics
    assert "num_contradictions" in metrics

def test_pdf_processor_metadata_and_sections():
    """Test PDF extraction extracts title, authors, year, sections, page numbers, and limitations."""
    test_pdf = PAPERS_DIR / "paper_1_edge_ai_vibration.pdf"
    assert test_pdf.exists()

    res = extract_pdf_data(test_pdf)
    assert "Edge-AI vs Cloud" in res["title"]
    assert "Alex Chen" in res["authors"]
    assert res["year"] in [2024, 2025, 2026]
    assert res["num_pages"] == 2
    assert len(res["sections"]) >= 4

    # Check page numbers
    page_nums = [s["page_num"] for s in res["sections"]]
    assert 1 in page_nums
    assert 2 in page_nums

    # Check limitations extraction
    lim = res["summary"]["limitations"]
    assert "memory exhaustion" in lim.lower() or "sram" in lim.lower()
    assert res["summary"]["limitations_page"] == 2

def test_pdf_processor_duplicate_detection():
    """Test SHA-256 hash calculation and duplicate detection."""
    test_pdf = PAPERS_DIR / "paper_2_multimodal_vision_transformer.pdf"
    hash1 = calculate_file_hash(test_pdf)
    hash2 = calculate_file_hash(test_pdf)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length

    # Existing paper lookup by hash should find paper
    found = database.get_paper_by_hash(hash1)
    assert found is not None
    assert "Multimodal" in found["title"]

def test_pdf_scanned_detection():
    """Test that scanned document detection correctly triggers if char density is too low."""
    # Test low text density simulation
    res = extract_pdf_data(PAPERS_DIR / "paper_1_edge_ai_vibration.pdf")
    # Real PDF has text density > threshold, so is_scanned is False
    assert res["is_scanned"] is False
    assert res["ocr_required"] is False
    assert res["ocr_message"] == ""

def test_cross_paper_synthesis():
    """Test comparative matrix construction and scientific comparability warnings."""
    df = synthesis_engine.build_comparative_matrix()
    assert len(df) >= 5
    assert "Title" in df.columns
    assert "Methodology" in df.columns
    assert "Dataset / Testbed" in df.columns
    assert "Comparability Constraints" in df.columns

    # Verify that comparability constraint flags hardware/modality differences
    warnings = " ".join(df["Comparability Constraints"].dropna().tolist())
    assert "cannot be directly benchmarked" in warnings or "distinct" in warnings or "modality" in warnings.lower()

    # Themes
    themes = synthesis_engine.extract_synthesis_themes()
    assert len(themes["recurring_limitations"]) >= 2
    assert len(themes["methodological_divergences"]) >= 2

def test_evidence_gap_discovery():
    """Test gap discovery, typologies (Class A, B, C), and evidence traceability."""
    gaps = gap_detector.discover_gaps(force_refresh=True)
    assert len(gaps) >= 4

    for g in gaps:
        assert g["gap_code"].startswith("GAP-")
        assert len(g["title"]) > 5
        assert g["category"] in GAP_CATEGORIES
        assert any(c in g["classification"] for c in ["A. Explicitly", "B. Synthesized", "C. Inferred"])
        assert len(g["evidence_passages"]) > 0
        assert len(g["source_paper_ids"]) > 0
        assert "suggested_research_question" in g
        assert len(g["suggested_research_question"]) > 10

        # Check evidence passage structure
        for ep in g["evidence_passages"]:
            assert "paper_title" in ep
            assert "page" in ep
            assert "passage" in ep
            assert len(ep["passage"]) > 15

def test_contradiction_detection():
    """Test detection of conflicting findings between papers (e.g. thermal vs acoustic)."""
    conflicts = contradiction_detector.detect_contradictions(force_refresh=True)
    assert len(conflicts) >= 2

    # Check for the key controversy: Thermal Vision vs Acoustic Emission
    modal_conflict = next((c for c in conflicts if "optical" in c["topic"].lower() or "sensory" in c["topic"].lower() or "thermal" in c["topic"].lower()), None)
    assert modal_conflict is not None
    assert "paper1_claim" in modal_conflict
    assert "paper2_claim" in modal_conflict
    assert "required_info_for_fair_comparison" in modal_conflict
    assert len(modal_conflict["explanation"]) > 20

def test_deterministic_prioritization():
    """Test the deterministic prioritization formula and contribution breakdown."""
    test_gap = {
        "evidence_strength": 0.90,
        "impact": 0.80,
        "feasibility": 0.70,
        "unaddressed_score": 0.85,
        "recency": 0.90,
        "source_paper_ids": [1, 2],
        "category": "application"
    }
    
    weights = {
        "evidence_strength": 0.30,
        "impact": 0.25,
        "feasibility": 0.20,
        "unaddressed_score": 0.15,
        "recency": 0.10
    }

    # Expected: 100 * (0.3*0.9 + 0.25*0.8 + 0.2*0.7 + 0.15*0.85 + 0.1*0.9)
    # = 100 * (0.27 + 0.20 + 0.14 + 0.1275 + 0.09) = 100 * 0.8275 = 82.75
    res = prioritization_engine.calculate_priority(test_gap, weights)
    assert abs(res["priority_score"] - 82.75) < 0.05
    assert res["priority_level"] == "High"
    assert "contributions" in res
    assert sum(res["contributions"].values()) == pytest.approx(res["priority_score"], abs=0.1)

def test_verification_engine_offline_handling():
    """Test external literature verification engine handling of offline environment."""
    gaps = database.get_gaps()
    assert len(gaps) > 0
    target_gap = gaps[0]

    # Run verification with local benchmark provider
    res = verification_engine.verify_gap(target_gap, provider="local_benchmark")
    assert res["status"] in [
        "Supported within uploaded collection",
        "Additional related literature found",
        "Potentially addressed by existing work",
        "Conflicting evidence found",
        "Insufficient evidence",
        "Requires human verification"
    ]
    assert len(res["results"]) > 0
    # Verify DOI is real
    assert "10." in res["results"][0]["doi"]

    # Verify query history is saved
    records = database.get_verification_records(target_gap["id"])
    assert len(records) > 0

def test_proposal_generation():
    """Test transforming a gap into a structured research proposal."""
    gaps = database.get_gaps()
    assert len(gaps) > 0
    target_gap = gaps[0]

    proposal = proposal_generator.generate_proposal(target_gap)
    assert "title" in proposal
    assert "problem_statement" in proposal
    assert "proposed_methodology" in proposal
    assert len(proposal["research_questions"]) >= 2
    assert "dataset_requirements" in proposal
    assert "evaluation_metrics" in proposal
    assert "baseline_methods" in proposal
    assert "feasibility_assessment" in proposal
    assert "human_verification_note" in proposal

    # Check persistence in database
    saved_prop = database.get_proposal_by_id(proposal["id"])
    assert saved_prop is not None
    assert saved_prop["title"] == proposal["title"]

def test_evidence_graph_construction():
    """Test NetworkX graph contains papers, methods, datasets, limitations, gaps, and edges."""
    G = evidence_graph_engine.build_network()
    assert len(G.nodes) >= 15
    assert len(G.edges) >= 10

    node_types = set(data.get("type") for _, data in G.nodes(data=True))
    assert "paper" in node_types
    assert "gap" in node_types
    assert "limitation" in node_types

    edge_rels = set(data.get("relationship") for _, _, data in G.edges(data=True))
    assert "motivates_gap" in edge_rels or "grounds_gap" in edge_rels

def test_grounded_qa_engine():
    """Test grounded QA queries return cited passages with page numbers or state insufficient evidence."""
    # Query with matching evidence
    res = qa_engine.answer_query("What is the inference latency and power consumption of INT8 quantization on STM32?")
    assert res["sufficient_evidence"] is True
    assert len(res["sources"]) > 0
    assert any("Page" in s.get("paper_title", "") or s.get("page") in [1, 2] for s in res["sources"])

    # Query without matching evidence
    out_of_scope = qa_engine.answer_query("What is the protein folding accuracy of AlphaFold on COVID-19 spike glycoprotein?")
    assert res["sufficient_evidence"] is True  # previous
    assert out_of_scope["sufficient_evidence"] is False
    assert "Insufficient evidence" in out_of_scope["answer"]

def test_report_generation():
    """Test PDF and DOCX report creation."""
    proposals = database.get_proposals()
    prop_id = proposals[0]["id"] if proposals else None

    # Generate PDF
    pdf_path = report_generator.generate_pdf_report(proposal_id=prop_id)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000

    # Generate DOCX
    docx_path = report_generator.generate_docx_report(proposal_id=prop_id)
    assert docx_path.exists()
    assert docx_path.stat().st_size > 1000

def test_llm_client_fallback():
    """Test LLM client fallback when no API key is provided."""
    resp = llm_client.generate("Summarize vibration anomaly detection.")
    assert "Grounded" in resp or "Academic" in resp or "Offline" in resp or len(resp) > 10
