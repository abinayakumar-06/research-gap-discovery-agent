"""
config.py
---------
Configuration parameters, directory paths, and default settings
for the Research Literature Synthesis & Research-Gap Discovery Platform.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load optional .env file
load_dotenv()

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sample_data"
PAPERS_DIR = DATA_DIR / "papers"
EXPORTS_DIR = BASE_DIR / "exports"
DB_PATH = BASE_DIR / "research_gap_platform.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
PAPERS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Application Metadata
APP_TITLE = "Research Literature Synthesis & Research-Gap Discovery Platform"
APP_SUBTITLE = "Evidence-Based Literature Analysis, Gap Discovery & Proposal Generation"
AUTHOR_INFO = "Academic & Industrial Research Analysis Engine"
VERSION = "2.2.0"

# Academic Gap Typologies (Standardized from academic literature review frameworks)
GAP_CATEGORIES = {
    "knowledge": "Knowledge Gap (Unaddressed questions or theoretical limits)",
    "methodological": "Methodological Gap (Flaws, limitations or bias in current methods)",
    "contextual": "Contextual Gap (Untested real-world environments or domains)",
    "population": "Population / Dataset Gap (Distribution shift, benchmark bias, small samples)",
    "geographical": "Geographical / Environmental Gap (Region or condition-specific limitations)",
    "temporal": "Temporal Gap (Outdated baselines, latency drift, dynamic drift)",
    "contradictory": "Contradictory Findings Gap (Direct conflicts or opposing empirical results)",
    "data_modality": "Data / Modality Gap (Missing multimodal streams, sensory limitations)",
    "application": "Application / Deployment Gap (Resource constraints, edge execution, latency)"
}

# Gap Classifications (Distinguishing facts from AI interpretations)
GAP_CLASSIFICATIONS = {
    "CLASS_A": "A. Explicitly stated by the authors",
    "CLASS_B": "B. Synthesized from limitations across multiple papers",
    "CLASS_C": "C. Inferred by the AI and requiring verification"
}

# Verification Statuses
VERIFICATION_STATUSES = [
    "Supported within uploaded collection",
    "Additional related literature found",
    "Potentially addressed by existing work",
    "Conflicting evidence found",
    "Insufficient evidence",
    "Requires human verification"
]

# Prioritization Scoring Weights (Deterministic Model)
DEFAULT_PRIORITY_WEIGHTS = {
    "evidence_strength": 0.30,
    "impact": 0.25,
    "feasibility": 0.20,
    "unaddressed_score": 0.15,
    "recency": 0.10
}
PRIORITY_WEIGHTS = DEFAULT_PRIORITY_WEIGHTS.copy()

# Priority Levels
PRIORITY_LEVELS = {
    "High": {"min_score": 75, "color": "#E53E3E", "badge": "HIGH PRIORITY"},
    "Medium": {"min_score": 50, "color": "#DD6B20", "badge": "MEDIUM PRIORITY"},
    "Low": {"min_score": 0, "color": "#3182CE", "badge": "EXPLORATORY"}
}

# Document & Processing Constraints
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
OCR_TEXT_DENSITY_THRESHOLD = int(os.getenv("OCR_TEXT_DENSITY_THRESHOLD", 60))  # min avg chars per page

# LLM Configuration (Optional, purely local fallback by default)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local").lower()  # local, openai, groq, gemini
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# External Literature Verification Configuration
SCHOLAR_SEARCH_PROVIDER = os.getenv("SCHOLAR_SEARCH_PROVIDER", "crossref").lower()
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

# Streamlit Page Configuration
PAGE_CONFIG = {
    "page_title": "ResearchFlow AI",
    "page_icon": "🔬",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}
