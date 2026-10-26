"""
database.py
-----------
SQLite persistence layer for papers, sections, claims, summaries,
evidence-based research gaps, contradictions, verification records, and generated proposals.
Includes automatic schema migrations to preserve existing data.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_column(cursor: sqlite3.Cursor, table: str, column: str, col_type: str, default: str = ""):
    """Helper to add a column to an existing table if it doesn't already exist."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        default_clause = f" DEFAULT {default}" if default else ""
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}")

def init_db():
    """Initialize database tables with appropriate indices and run safe schema migrations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Papers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                abstract TEXT,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE,
                num_pages INTEGER DEFAULT 1,
                raw_text TEXT,
                is_scanned INTEGER DEFAULT 0,
                ocr_required INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Paper sections table with page number and character offsets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER NOT NULL,
                section_name TEXT NOT NULL,
                content TEXT NOT NULL,
                page_num INTEGER DEFAULT 1,
                char_start INTEGER DEFAULT 0,
                char_end INTEGER DEFAULT 0,
                FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
            )
        """)
        
        # Paper summaries & structured metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_summaries (
                paper_id INTEGER PRIMARY KEY,
                research_problem TEXT,
                objective TEXT,
                methodology TEXT,
                dataset TEXT,
                experimental_setup TEXT,
                evaluation_metrics TEXT,
                key_findings TEXT,
                limitations TEXT,
                future_work TEXT,
                metrics_json TEXT,
                references_json TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
            )
        """)
        
        # Research gaps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gap_code TEXT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                classification TEXT DEFAULT 'B. Synthesized from limitations across multiple papers',
                priority_score REAL DEFAULT 0.0,
                priority_level TEXT DEFAULT 'Medium',
                evidence_strength REAL DEFAULT 0.0,
                feasibility REAL DEFAULT 0.0,
                impact REAL DEFAULT 0.0,
                unaddressed_score REAL DEFAULT 0.0,
                recency REAL DEFAULT 0.0,
                source_paper_ids_json TEXT,
                evidence_passages_json TEXT,
                related_limitations_json TEXT,
                future_work_statements_json TEXT,
                collective_support_explanation TEXT,
                alternative_interpretations TEXT,
                uncertainties TEXT,
                suggested_research_question TEXT,
                verification_status TEXT DEFAULT 'Requires human verification',
                external_evidence_json TEXT,
                human_verification_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Contradictions / Conflicting findings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contradictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                paper1_id INTEGER,
                paper1_title TEXT,
                paper1_claim TEXT NOT NULL,
                paper1_page INTEGER DEFAULT 1,
                paper1_dataset TEXT,
                paper1_method TEXT,
                paper1_metrics TEXT,
                paper2_id INTEGER,
                paper2_title TEXT,
                paper2_claim TEXT NOT NULL,
                paper2_page INTEGER DEFAULT 1,
                paper2_dataset TEXT,
                paper2_method TEXT,
                paper2_metrics TEXT,
                divergence_type TEXT,
                explanation TEXT,
                required_info_for_fair_comparison TEXT,
                is_genuine_contradiction INTEGER DEFAULT 1,
                confidence REAL DEFAULT 0.85,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Verification history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gap_id INTEGER,
                search_query TEXT,
                provider TEXT,
                results_json TEXT,
                verification_status TEXT,
                synthesis_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gap_id) REFERENCES research_gaps (id) ON DELETE CASCADE
            )
        """)
        
        # Generated research proposals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gap_id INTEGER,
                gap_title TEXT,
                title TEXT NOT NULL,
                background TEXT,
                problem_statement TEXT NOT NULL,
                motivating_evidence TEXT NOT NULL,
                proposed_methodology TEXT NOT NULL,
                research_questions_json TEXT,
                hypotheses_json TEXT,
                objectives_json TEXT,
                supporting_literature_json TEXT,
                dataset_requirements TEXT,
                evaluation_metrics TEXT,
                baseline_methods TEXT,
                experimental_design_json TEXT,
                challenges_mitigations_json TEXT,
                feasibility_assessment TEXT,
                limitations TEXT,
                future_work TEXT,
                expected_impact TEXT,
                human_verification_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gap_id) REFERENCES research_gaps (id) ON DELETE SET NULL
            )
        """)
        
        # Safe schema migrations for existing tables
        _ensure_column(cursor, "papers", "is_scanned", "INTEGER", "0")
        _ensure_column(cursor, "papers", "ocr_required", "INTEGER", "0")
        _ensure_column(cursor, "papers", "project_id", "INTEGER", "1")
        
        _ensure_column(cursor, "paper_summaries", "research_problem", "TEXT", "''")
        _ensure_column(cursor, "paper_summaries", "dataset", "TEXT", "''")
        _ensure_column(cursor, "paper_summaries", "experimental_setup", "TEXT", "''")
        _ensure_column(cursor, "paper_summaries", "evaluation_metrics", "TEXT", "''")
        _ensure_column(cursor, "paper_summaries", "references_json", "TEXT", "'[]'")
        
        _ensure_column(cursor, "research_gaps", "gap_code", "TEXT", "''")
        _ensure_column(cursor, "research_gaps", "classification", "TEXT", "'B. Synthesized from limitations across multiple papers'")
        _ensure_column(cursor, "research_gaps", "related_limitations_json", "TEXT", "'[]'")
        _ensure_column(cursor, "research_gaps", "future_work_statements_json", "TEXT", "'[]'")
        _ensure_column(cursor, "research_gaps", "collective_support_explanation", "TEXT", "''")
        _ensure_column(cursor, "research_gaps", "alternative_interpretations", "TEXT", "''")
        _ensure_column(cursor, "research_gaps", "uncertainties", "TEXT", "''")
        _ensure_column(cursor, "research_gaps", "suggested_research_question", "TEXT", "''")
        _ensure_column(cursor, "research_gaps", "verification_status", "TEXT", "'Requires human verification'")
        _ensure_column(cursor, "research_gaps", "external_evidence_json", "TEXT", "'[]'")
        _ensure_column(cursor, "research_gaps", "project_id", "INTEGER", "1")
        
        _ensure_column(cursor, "contradictions", "paper1_dataset", "TEXT", "''")
        _ensure_column(cursor, "contradictions", "paper1_method", "TEXT", "''")
        _ensure_column(cursor, "contradictions", "paper1_metrics", "TEXT", "''")
        _ensure_column(cursor, "contradictions", "paper2_dataset", "TEXT", "''")
        _ensure_column(cursor, "contradictions", "paper2_method", "TEXT", "''")
        _ensure_column(cursor, "contradictions", "paper2_metrics", "TEXT", "''")
        _ensure_column(cursor, "contradictions", "required_info_for_fair_comparison", "TEXT", "''")
        _ensure_column(cursor, "contradictions", "is_genuine_contradiction", "INTEGER", "1")
        _ensure_column(cursor, "contradictions", "project_id", "INTEGER", "1")
        
        _ensure_column(cursor, "proposals", "background", "TEXT", "''")
        _ensure_column(cursor, "proposals", "objectives_json", "TEXT", "'[]'")
        _ensure_column(cursor, "proposals", "supporting_literature_json", "TEXT", "'[]'")
        _ensure_column(cursor, "proposals", "dataset_requirements", "TEXT", "''")
        _ensure_column(cursor, "proposals", "evaluation_metrics", "TEXT", "''")
        _ensure_column(cursor, "proposals", "baseline_methods", "TEXT", "''")
        _ensure_column(cursor, "proposals", "feasibility_assessment", "TEXT", "''")
        _ensure_column(cursor, "proposals", "limitations", "TEXT", "''")
        _ensure_column(cursor, "proposals", "future_work", "TEXT", "''")
        _ensure_column(cursor, "proposals", "project_id", "INTEGER", "1")

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                domain TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("SELECT COUNT(*) FROM projects")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO projects (id, name, description, domain, is_active)
                VALUES (1, 'Industrial Predictive Maintenance & Edge AI',
                        'Literature synthesis on vibration analysis, acoustic emission, vision transformers, and federated learning on edge microcontrollers.',
                        'Industrial Cyber-Physical Systems', 1)
            """)
        
        # Create helpful indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sections_paper ON paper_sections(paper_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gaps_score ON research_gaps(priority_score DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_verification_gap ON verification_records(gap_id)")
        
        conn.commit()

# --- Paper Operations ---

def save_paper(paper_data: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO papers (title, authors, year, abstract, filename, file_hash, num_pages, raw_text, is_scanned, ocr_required)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_data.get("title", "Untitled Document"),
            paper_data.get("authors", "Unknown"),
            paper_data.get("year", 2025),
            paper_data.get("abstract", ""),
            paper_data.get("filename", ""),
            paper_data.get("file_hash", ""),
            paper_data.get("num_pages", 1),
            paper_data.get("raw_text", ""),
            1 if paper_data.get("is_scanned") else 0,
            1 if paper_data.get("ocr_required") else 0
        ))
        paper_id = cursor.lastrowid
        conn.commit()
        return paper_id

def get_paper_by_hash(file_hash: str) -> Optional[Dict[str, Any]]:
    if not file_hash:
        return None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM papers WHERE file_hash = ?", (file_hash,))
        row = cursor.fetchone()
        return dict(row) if row else None

def save_sections(paper_id: int, sections: List[Dict[str, Any]]):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM paper_sections WHERE paper_id = ?", (paper_id,))
        for sec in sections:
            cursor.execute("""
                INSERT INTO paper_sections (paper_id, section_name, content, page_num, char_start, char_end)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                paper_id,
                sec.get("section_name", "General"),
                sec.get("content", ""),
                sec.get("page_num", 1),
                sec.get("char_start", 0),
                sec.get("char_end", 0)
            ))
        conn.commit()

def save_summary(paper_id: int, summary_data: Dict[str, Any]):
    with get_connection() as conn:
        cursor = conn.cursor()
        metrics_json = json.dumps(summary_data.get("metrics", {}))
        references_json = json.dumps(summary_data.get("references", []))
        cursor.execute("""
            INSERT OR REPLACE INTO paper_summaries (
                paper_id, research_problem, objective, methodology, dataset,
                experimental_setup, evaluation_metrics, key_findings,
                limitations, future_work, metrics_json, references_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_id,
            summary_data.get("research_problem", ""),
            summary_data.get("objective", ""),
            summary_data.get("methodology", ""),
            summary_data.get("dataset", ""),
            summary_data.get("experimental_setup", ""),
            summary_data.get("evaluation_metrics", ""),
            summary_data.get("key_findings", ""),
            summary_data.get("limitations", ""),
            summary_data.get("future_work", ""),
            metrics_json,
            references_json
        ))
        conn.commit()

def get_papers() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM papers ORDER BY id ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_paper_by_id(paper_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_sections_by_paper(paper_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM paper_sections WHERE paper_id = ? ORDER BY page_num ASC, id ASC", (paper_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_all_sections() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, p.title as paper_title 
            FROM paper_sections s 
            JOIN papers p ON s.paper_id = p.id 
            ORDER BY s.paper_id ASC, s.page_num ASC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_summaries() -> Dict[int, Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM paper_summaries")
        rows = cursor.fetchall()
        summaries = {}
        for row in rows:
            d = dict(row)
            try:
                d["metrics"] = json.loads(d.get("metrics_json") or "{}")
            except Exception:
                d["metrics"] = {}
            try:
                d["references"] = json.loads(d.get("references_json") or "[]")
            except Exception:
                d["references"] = []
            summaries[d["paper_id"]] = d
        return summaries

def delete_paper(paper_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        cursor.execute("DELETE FROM paper_sections WHERE paper_id = ?", (paper_id,))
        cursor.execute("DELETE FROM paper_summaries WHERE paper_id = ?", (paper_id,))
        conn.commit()

def clear_all_data():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM proposals")
        cursor.execute("DELETE FROM verification_records")
        cursor.execute("DELETE FROM contradictions")
        cursor.execute("DELETE FROM research_gaps")
        cursor.execute("DELETE FROM paper_summaries")
        cursor.execute("DELETE FROM paper_sections")
        cursor.execute("DELETE FROM papers")
        conn.commit()

# --- Research Gap Operations ---

def save_gaps(gaps: List[Dict[str, Any]]):
    with get_connection() as conn:
        cursor = conn.cursor()
        for gap in gaps:
            cursor.execute("""
                INSERT INTO research_gaps (
                    gap_code, title, category, description, classification,
                    priority_score, priority_level, evidence_strength, feasibility,
                    impact, unaddressed_score, recency, source_paper_ids_json,
                    evidence_passages_json, related_limitations_json, future_work_statements_json,
                    collective_support_explanation, alternative_interpretations, uncertainties,
                    suggested_research_question, verification_status, external_evidence_json,
                    human_verification_note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gap.get("gap_code", f"GAP-{gap.get('id', 'NEW')}"),
                gap.get("title", "Untitled Gap"),
                gap.get("category", "knowledge"),
                gap.get("description", ""),
                gap.get("classification", "B. Synthesized from limitations across multiple papers"),
                gap.get("priority_score", 0.0),
                gap.get("priority_level", "Medium"),
                gap.get("evidence_strength", 0.0),
                gap.get("feasibility", 0.0),
                gap.get("impact", 0.0),
                gap.get("unaddressed_score", 0.0),
                gap.get("recency", 0.0),
                json.dumps(gap.get("source_paper_ids", [])),
                json.dumps(gap.get("evidence_passages", [])),
                json.dumps(gap.get("related_limitations", [])),
                json.dumps(gap.get("future_work_statements", [])),
                gap.get("collective_support_explanation", ""),
                gap.get("alternative_interpretations", ""),
                gap.get("uncertainties", ""),
                gap.get("suggested_research_question", ""),
                gap.get("verification_status", "Requires human verification"),
                json.dumps(gap.get("external_evidence", [])),
                gap.get("human_verification_note", "Requires external benchmark verification.")
            ))
        conn.commit()

def update_gap(gap_id: int, updates: Dict[str, Any]):
    with get_connection() as conn:
        cursor = conn.cursor()
        fields = []
        values = []
        for k, v in updates.items():
            if k in ["source_paper_ids", "evidence_passages", "related_limitations", "future_work_statements", "external_evidence"]:
                fields.append(f"{k}_json = ?")
                values.append(json.dumps(v))
            else:
                fields.append(f"{k} = ?")
                values.append(v)
        values.append(gap_id)
        cursor.execute(f"UPDATE research_gaps SET {', '.join(fields)} WHERE id = ?", tuple(values))
        conn.commit()

def clear_gaps():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM research_gaps")
        cursor.execute("DELETE FROM verification_records")
        conn.commit()

def get_gaps() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM research_gaps ORDER BY priority_score DESC, id ASC")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["source_paper_ids"] = json.loads(d.get("source_paper_ids_json") or "[]")
            except Exception:
                d["source_paper_ids"] = []
            try:
                d["evidence_passages"] = json.loads(d.get("evidence_passages_json") or "[]")
            except Exception:
                d["evidence_passages"] = []
            try:
                d["related_limitations"] = json.loads(d.get("related_limitations_json") or "[]")
            except Exception:
                d["related_limitations"] = []
            try:
                d["future_work_statements"] = json.loads(d.get("future_work_statements_json") or "[]")
            except Exception:
                d["future_work_statements"] = []
            try:
                d["external_evidence"] = json.loads(d.get("external_evidence_json") or "[]")
            except Exception:
                d["external_evidence"] = []
            result.append(d)
        return result

def get_gap_by_id(gap_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM research_gaps WHERE id = ?", (gap_id,))
        r = cursor.fetchone()
        if not r:
            return None
        d = dict(r)
        d["source_paper_ids"] = json.loads(d.get("source_paper_ids_json") or "[]")
        d["evidence_passages"] = json.loads(d.get("evidence_passages_json") or "[]")
        d["related_limitations"] = json.loads(d.get("related_limitations_json") or "[]")
        d["future_work_statements"] = json.loads(d.get("future_work_statements_json") or "[]")
        d["external_evidence"] = json.loads(d.get("external_evidence_json") or "[]")
        return d

# --- Contradiction Operations ---

def save_contradictions(contradictions: List[Dict[str, Any]]):
    with get_connection() as conn:
        cursor = conn.cursor()
        for c in contradictions:
            cursor.execute("""
                INSERT INTO contradictions (
                    topic, paper1_id, paper1_title, paper1_claim, paper1_page,
                    paper1_dataset, paper1_method, paper1_metrics,
                    paper2_id, paper2_title, paper2_claim, paper2_page,
                    paper2_dataset, paper2_method, paper2_metrics,
                    divergence_type, explanation, required_info_for_fair_comparison,
                    is_genuine_contradiction, confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c.get("topic", "General"),
                c.get("paper1_id"),
                c.get("paper1_title", "Paper 1"),
                c.get("paper1_claim", ""),
                c.get("paper1_page", 1),
                c.get("paper1_dataset", ""),
                c.get("paper1_method", ""),
                c.get("paper1_metrics", ""),
                c.get("paper2_id"),
                c.get("paper2_title", "Paper 2"),
                c.get("paper2_claim", ""),
                c.get("paper2_page", 1),
                c.get("paper2_dataset", ""),
                c.get("paper2_method", ""),
                c.get("paper2_metrics", ""),
                c.get("divergence_type", "Empirical Discrepancy"),
                c.get("explanation", ""),
                c.get("required_info_for_fair_comparison", ""),
                1 if c.get("is_genuine_contradiction", True) else 0,
                c.get("confidence", 0.85)
            ))
        conn.commit()

def clear_contradictions():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contradictions")
        conn.commit()

def get_contradictions() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contradictions ORDER BY confidence DESC, id ASC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

# --- Verification Records ---

def save_verification_record(record: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO verification_records (gap_id, search_query, provider, results_json, verification_status, synthesis_notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            record.get("gap_id"),
            record.get("search_query", ""),
            record.get("provider", "crossref"),
            json.dumps(record.get("results", [])),
            record.get("verification_status", "Requires human verification"),
            record.get("synthesis_notes", "")
        ))
        rec_id = cursor.lastrowid
        conn.commit()
        return rec_id

def get_verification_records(gap_id: Optional[int] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if gap_id is not None:
            cursor.execute("SELECT * FROM verification_records WHERE gap_id = ? ORDER BY id DESC", (gap_id,))
        else:
            cursor.execute("SELECT * FROM verification_records ORDER BY id DESC")
        rows = cursor.fetchall()
        res = []
        for r in rows:
            d = dict(r)
            try:
                d["results"] = json.loads(d.get("results_json") or "[]")
            except Exception:
                d["results"] = []
            res.append(d)
        return res

# --- Proposal Operations ---

def save_proposal(prop: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO proposals (
                gap_id, gap_title, title, background, problem_statement, motivating_evidence,
                proposed_methodology, research_questions_json, hypotheses_json, objectives_json,
                supporting_literature_json, dataset_requirements, evaluation_metrics, baseline_methods,
                experimental_design_json, challenges_mitigations_json, feasibility_assessment,
                limitations, future_work, expected_impact, human_verification_note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prop.get("gap_id"),
            prop.get("gap_title", ""),
            prop.get("title", "Research Proposal"),
            prop.get("background", ""),
            prop.get("problem_statement", ""),
            prop.get("motivating_evidence", ""),
            prop.get("proposed_methodology", ""),
            json.dumps(prop.get("research_questions", [])),
            json.dumps(prop.get("hypotheses", [])),
            json.dumps(prop.get("objectives", [])),
            json.dumps(prop.get("supporting_literature", [])),
            prop.get("dataset_requirements", ""),
            prop.get("evaluation_metrics", ""),
            prop.get("baseline_methods", ""),
            json.dumps(prop.get("experimental_design", {})),
            json.dumps(prop.get("challenges_mitigations", [])),
            prop.get("feasibility_assessment", ""),
            prop.get("limitations", ""),
            prop.get("future_work", ""),
            prop.get("expected_impact", ""),
            prop.get("human_verification_note", "Human expert review required before grant or production commitment.")
        ))
        pid = cursor.lastrowid
        conn.commit()
        return pid

def update_proposal(proposal_id: int, updates: Dict[str, Any]):
    with get_connection() as conn:
        cursor = conn.cursor()
        fields = []
        values = []
        for k, v in updates.items():
            if k in ["research_questions", "hypotheses", "objectives", "supporting_literature", "experimental_design", "challenges_mitigations"]:
                fields.append(f"{k}_json = ?")
                values.append(json.dumps(v))
            else:
                fields.append(f"{k} = ?")
                values.append(v)
        values.append(proposal_id)
        cursor.execute(f"UPDATE proposals SET {', '.join(fields)} WHERE id = ?", tuple(values))
        conn.commit()

def delete_proposal(proposal_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM proposals WHERE id = ?", (proposal_id,))
        conn.commit()

def get_proposals() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proposals ORDER BY id DESC")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["research_questions"] = json.loads(d.get("research_questions_json") or "[]")
                d["hypotheses"] = json.loads(d.get("hypotheses_json") or "[]")
                d["objectives"] = json.loads(d.get("objectives_json") or "[]")
                d["supporting_literature"] = json.loads(d.get("supporting_literature_json") or "[]")
                d["experimental_design"] = json.loads(d.get("experimental_design_json") or "{}")
                d["challenges_mitigations"] = json.loads(d.get("challenges_mitigations_json") or "[]")
            except Exception:
                d["research_questions"] = []
                d["hypotheses"] = []
                d["objectives"] = []
                d["supporting_literature"] = []
                d["experimental_design"] = {}
                d["challenges_mitigations"] = []
            result.append(d)
        return result

def get_proposal_by_id(proposal_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
        r = cursor.fetchone()
        if not r:
            return None
        d = dict(r)
        d["research_questions"] = json.loads(d.get("research_questions_json") or "[]")
        d["hypotheses"] = json.loads(d.get("hypotheses_json") or "[]")
        d["objectives"] = json.loads(d.get("objectives_json") or "[]")
        d["supporting_literature"] = json.loads(d.get("supporting_literature_json") or "[]")
        d["experimental_design"] = json.loads(d.get("experimental_design_json") or "{}")
        d["challenges_mitigations"] = json.loads(d.get("challenges_mitigations_json") or "[]")
        return d

# --- Aggregate Metrics ---

def get_metrics_summary() -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM papers")
        num_papers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM paper_sections")
        num_sections = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM research_gaps")
        num_gaps = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM research_gaps WHERE priority_level = 'High'")
        num_high_gaps = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contradictions")
        num_contradictions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM proposals")
        num_proposals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM verification_records")
        num_verifications = cursor.fetchone()[0]
        
        return {
            "num_papers": num_papers,
            "num_sections": num_sections,
            "num_gaps": num_gaps,
            "num_high_gaps": num_high_gaps,
            "num_contradictions": num_contradictions,
            "num_proposals": num_proposals,
            "num_verifications": num_verifications
        }

# Initialize and migrate tables on import
init_db()
