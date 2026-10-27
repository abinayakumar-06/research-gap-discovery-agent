# Research Literature Synthesis & Research-Gap Discovery Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58%2B-FF4B4B.svg)](https://streamlit.io)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-2.0-orange.svg)](https://pymupdf.readthedocs.io/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.9%2B-F7931E.svg)](https://scikit-learn.org)
[![Tests](https://img.shields.io/badge/Pytest-14%20Passing-brightgreen.svg)]()

A professional, competition-ready AI research platform that analyzes academic research literature, synthesizes findings across multiple studies, identifies potential research gaps, traces every gap to supporting evidence, detects conflicting findings, prioritizes research directions transparently, verifies literature against external registries, and generates structured grant/project proposals.

## 🚀 Live Demo

**Try ResearchFlow AI online:**

👉 **[Launch ResearchFlow AI — Streamlit App](https://research-gap-discovery-agent-5kn35pzqis3r6dy9oxakpr.streamlit.app/)**

Explore the interactive Evidence Explorer, literature synthesis, research-gap discovery, contradiction analysis, gap prioritization, and research proposal generation.

---

A professional, competition-ready AI research platform that analyzes academic research literature, synthesizes findings across multiple studies, identifies potential research gaps, traces every gap to supporting evidence, detects conflicting findings, prioritizes research directions transparently, verifies literature against external registries, and generates structured grant/project proposals.

Unlike superficial PDF summarizers, this platform strictly enforces **scientific provenance**:

- Distinguishes extracted facts from AI interpretations.
- Every factual claim links to source passages and page references.
- Warns against invalid cross-study numerical comparisons.
- Never claims global novelty without external verification.


## 🌟 Core Architecture & Platform Modules

```
research_gap_platform/
├── app.py                      # Multi-page academic Streamlit application (10 Views)
├── config.py                   # System configuration, gap categories, priority weights
├── database.py                 # SQLite persistence layer with automatic schema migrations
├── .env.example                # Template configuration for LLMs and scholarly search
├── modules/
│   ├── pdf_processor.py        # PyMuPDF parser: titles, authors, sections, char offsets, OCR alerts
│   ├── embeddings.py           # Unified semantic engine: Sentence Transformers + Sklearn TF-IDF fallback
│   ├── synthesis_engine.py     # Cross-paper comparative synthesis & comparability warning engine
│   ├── gap_detector.py         # Evidence-based research gap discovery (Class A, B, C typologies)
│   ├── contradiction_detector.py# Empirical contradiction detector & contextual divergence analyzer
│   ├── prioritization.py       # Deterministic, multi-criteria gap prioritization engine
│   ├── verification_engine.py  # Scholarly search (Crossref, OpenAlex, Local Benchmark Corpus)
│   ├── proposal_generator.py   # Publication-grade research project proposal synthesizer
│   ├── evidence_graph.py       # NetworkX + Plotly interactive research evidence network
│   ├── qa_engine.py            # Evidence-grounded semantic search & Q&A assistant
│   ├── report_generator.py     # Downloadable PDF (ReportLab) & DOCX (python-docx) report builder
│   └── llm_client.py           # Configurable LLM client (OpenAI, Gemini, Groq, Local Offline Fallback)
├── sample_data/
│   ├── generator.py            # ReportLab academic benchmark paper generator
│   └── papers/                 # 5 benchmark research PDFs (Predictive Maintenance in Smart Mfg)
├── exports/                    # Generated PDF and DOCX synthesis reports
└── tests/
    └── test_platform.py        # Comprehensive Pytest test suite (14 passing tests)
```

---

## 🚀 Key Functional Capabilities

### 1. Robust Academic PDF Ingestion (`modules/pdf_processor.py`)
- Extracts titles, authors, publication years, abstracts, and structured sections (Introduction, Methodology, Testbed, Results, Limitations, Future Work, References).
- Tracks exact **page numbers** and character offsets (`char_start`, `char_end`) for full traceability.
- **Scanned PDF Detection:** Automatically computes character density per page; flags documents below threshold with a prominent OCR requirement alert.
- **Integrity Guard:** Uses SHA-256 content hashing to eliminate duplicate uploads and handles encrypted/corrupted files gracefully.

### 2. Cross-Paper Literature Synthesis (`modules/synthesis_engine.py`)
- Compares papers across research problems, objectives, methodologies, datasets, hardware budgets, metrics, and limitations.
- **Scientific Comparability Constraints:** Flags when numerical performance results (accuracy, latency, F1) cannot be directly benchmarked against each other due to differing sensor modalities, hardware power envelopes, or mechanical testbeds.
- Identifies recurring limitations, common approaches, and methodological divergences.
- Exports to CSV and JSON formats.

### 3. Evidence-Based Research Gap Discovery (`modules/gap_detector.py`)
Synthesizes candidate research gaps categorized into academic typologies:
- **Class A:** Explicitly stated by the authors.
- **Class B:** Synthesized from limitations across multiple papers.
- **Class C:** Inferred by AI and requiring external human verification.
- Each gap includes: unique code (`GAP-01`), title, description, category, supporting papers, exact supporting passages with page numbers, related limitations, collective support explanation, alternative interpretations, uncertainties, and suggested research questions.

### 4. Contradictory Findings Detector (`modules/contradiction_detector.py`)
- Analyzes conflicting empirical claims between papers (e.g. radiometric thermal vision vs ultrasonic acoustic emission).
- Extracts opposing claims with page references, datasets, methodologies, and metrics.
- Reconciles divergences contextually (e.g., exposed vs enclosed liquid-lubricated machinery) and prescribes the exact controlled experiment required for a fair comparison.
- **Integrity Rule:** Never declares a study correct solely because its reported score is higher.

### 5. Transparent Prioritization Formula (`modules/prioritization.py`)
Prioritizes candidate gaps using a deterministic, multi-criteria formula:
$$\text{Score} = 100 \times \frac{w_{\text{ev}} \cdot s_{\text{ev}} + w_{\text{imp}} \cdot s_{\text{imp}} + w_{\text{fea}} \cdot s_{\text{fea}} + w_{\text{unadd}} \cdot s_{\text{unadd}} + w_{\text{rec}} \cdot s_{\text{rec}}}{\sum w_i}$$
- Allows users to adjust criteria weights interactively in the UI.
- Displays stacked bar chart breakdown of each criterion's contribution.
- Highlights missing information and uncertainty disclosures for each ranking.

### 6. External Literature Verification (`modules/verification_engine.py`)
- Formulates targeted bibliographic search queries.
- Connects to public scholarly APIs (**Crossref REST API**, **OpenAlex REST API**) or authentic local benchmark corpus when offline.
- Assigns standardized verification statuses:
  - *Supported within uploaded collection*
  - *Additional related literature found*
  - *Potentially addressed by existing work*
  - *Conflicting evidence found*
  - *Insufficient evidence*
  - *Requires human verification*
- Never hallucinates DOIs, citations, or paper metadata.

### 7. Research Proposal Generator (`modules/proposal_generator.py`)
- Converts any selected candidate research gap into a complete, publication-grade project proposal.
- Includes: Proposed Title, Background, Problem Statement, Primary/Secondary Research Questions, Hypotheses, Objectives, Traceable Supporting Literature, 3-Phase Methodology, Sensory & Data Specifications, Target Evaluation Metrics, Baseline Methods, Challenges & Risk Mitigations, Feasibility Assessment, Limitations, and Future Work.
- Explicitly separates proposed methods from demonstrated experimental results.

### 8. Interactive Evidence Provenance Graph (`modules/evidence_graph.py`)
- Renders an interactive NetworkX + Plotly network visualization.
- Nodes represent Papers, Methods, Datasets, Findings, Limitations, Research Gaps, and Proposals.
- Labeled directed edges represent typed relationships (`employs_method`, `evaluates_on`, `identifies_limitation`, `motivates_gap`, `contradicts`, `proposes_direction`).
- Interactive node inspection drawer reveals source details and page citations.

### 9. Grounded Evidence Q&A Assistant (`modules/qa_engine.py`)
- Answers natural language research questions using semantic retrieval across paper sections.
- Cites source paper titles, section names, exact page numbers, and similarity scores.
- Explicitly states: *"Insufficient evidence found in the uploaded collection"* when out of scope.

### 10. Publication-Ready Reports (`modules/report_generator.py`)
- Generates downloadable **PDF reports** formatted with ReportLab.
- Generates editable **Word (.docx) reports** formatted with `python-docx`.

---

## 🛠️ Quickstart Installation & Execution

### 1. Requirements
- Python 3.10+
- Dependencies: `streamlit`, `pymupdf`, `pandas`, `scikit-learn`, `plotly`, `networkx`, `reportlab`, `python-docx`, `pytest`

### 2. Configuration (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
By default, the platform runs in **100% Local Offline Mode** without requiring external API keys.
To optionally enable external LLM reasoning, configure:
```env
LLM_PROVIDER=openai # or gemini, groq, local
OPENAI_API_KEY=your_key_here
```

### 3. Launching the SaaS Dashboard
From the project root:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Running the Automated Test Suite
Execute the full test suite with Pytest:
```bash
python -m pytest tests/test_platform.py -v
```
All 14 tests run in under 30 seconds with 100% pass rate.

---

## 📄 License & Academic Attribution
Developed for competition and research literature discovery under the MIT License.
All generated sample benchmark research papers model authentic predictive maintenance literature in Industry 4.0 cyber-physical systems.
