"""
app.py
------
ResearchFlow AI — Research Literature Synthesis & Research-Gap Discovery Platform.
Premium SaaS Streamlit interface over the existing evidence-based analysis engines.
"""

import html
from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import (
    PAGE_CONFIG,
    GAP_CATEGORIES,
    PAPERS_DIR,
)
import database
from modules.pdf_processor import extract_pdf_data, calculate_file_hash, PDFProcessingError
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

st.set_page_config(**PAGE_CONFIG)

NAV_DASHBOARD = "Dashboard"
NAV_LITERATURE = "Literature Analysis"
NAV_GAPS = "Gap Discovery"
NAV_CONTRA = "Contradiction Analysis"
NAV_EVIDENCE = "Evidence Explorer"
NAV_PRIO = "Gap Prioritization"
NAV_PROPOSAL = "Research Proposal"
NAV_SAVED = "Saved Projects"
NAV_SETTINGS = "Settings"
NAV_HELP = "Help & Support"

PRIMARY_NAV = [
    (NAV_DASHBOARD, "⌂"),
    (NAV_LITERATURE, "▣"),
    (NAV_GAPS, "⌕"),
    (NAV_CONTRA, "⚡"),
    (NAV_EVIDENCE, "◎"),
    (NAV_PRIO, "☰"),
    (NAV_PROPOSAL, "✎"),
]
SECONDARY_NAV = [
    (NAV_SAVED, "▢"),
    (NAV_SETTINGS, "⚙"),
    (NAV_HELP, "?"),
]

CHART_COLORS = ["#3478F6", "#4F46E5", "#7C4DFF", "#10B981", "#38BDF8", "#F59E0B", "#6366F1", "#14B8A6"]
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, sans-serif", color="#14213D", size=12),
    margin=dict(l=8, r=8, t=28, b=8),
)
PLOTLY_LEGEND = dict(orientation="h", y=-0.18, font=dict(size=11, color="#71809B"))

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, p, span, label, div {
    font-family: Inter, "Segoe UI", Helvetica, Arial, sans-serif;
}

.stApp { background: #F5F8FD; }
.block-container {
    padding-top: 1.15rem;
    padding-bottom: 2.4rem;
    padding-left: 1.6rem;
    padding-right: 1.6rem;
    max-width: 1440px;
}

#MainMenu, footer, .stDeployButton, div[data-testid="stToolbar"] { visibility: hidden; height: 0; }
header[data-testid="stHeader"] { background: transparent; }

section[data-testid="stSidebar"] {
    background: #07152B !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] > div { background: #07152B; }
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background: #07152B;
    padding: 18px 14px 20px 14px;
}
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {
    color: #9BB3D3;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08);
    margin: 10px 0 12px 0;
}
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #8AA4CC !important;
    border: none !important;
    border-radius: 10px !important;
    justify-content: flex-start !important;
    text-align: left !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
    padding: 0.58rem 0.85rem !important;
    box-shadow: none !important;
    letter-spacing: 0.01em;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(52,120,246,0.16) !important;
    color: #F4F8FF !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"],
section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(90deg, #3478F6 0%, #4F46E5 100%) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    box-shadow: 0 6px 16px rgba(52,120,246,0.28) !important;
}

.brand-lockup { display: flex; gap: 12px; align-items: center; margin: 2px 4px 18px 4px; }
.brand-mark {
    width: 38px; height: 38px; border-radius: 12px;
    background: linear-gradient(135deg, #3478F6, #7C4DFF);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 8px 18px rgba(76, 86, 255, 0.35);
    flex-shrink: 0;
}
.brand-title { color: #FFFFFF !important; font-size: 16.5px; font-weight: 800; letter-spacing: -0.03em; line-height: 1.15; }
.brand-sub { color: #8AA4CC !important; font-size: 11px; line-height: 1.35; margin-top: 2px; }
.nav-label { color: #5D7396 !important; font-size: 10.5px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin: 4px 8px 6px 8px; }
.sidebar-promo {
    margin-top: 18px; padding: 16px 14px; border-radius: 14px;
    background: linear-gradient(180deg, rgba(52,120,246,0.28), rgba(15,28,58,0.9));
    border: 1px solid rgba(124,77,255,0.28);
}
.sidebar-promo h4 { color: #FFFFFF !important; font-size: 13.5px; margin: 0 0 6px 0; font-weight: 700; }
.sidebar-promo p { color: #B7C7E4 !important; font-size: 11.5px; margin: 0; line-height: 1.45; }

.top-header {
    background: #FFFFFF; border: 1px solid #E3EAF5; border-radius: 16px;
    padding: 10px 16px; margin-bottom: 16px;
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
    box-shadow: 0 1px 2px rgba(20,33,61,0.04);
}
.profile-chip {
    display: flex; align-items: center; gap: 10px; justify-content: flex-end;
}
.avatar {
    width: 36px; height: 36px; border-radius: 50%;
    background: linear-gradient(135deg, #3478F6, #7C4DFF);
    color: #fff; font-weight: 700; font-size: 12px;
    display: flex; align-items: center; justify-content: center;
}
.profile-name { color: #14213D; font-weight: 700; font-size: 13px; line-height: 1.1; }
.profile-role { color: #71809B; font-size: 11px; }
.notice-pill {
    background: #F5F8FD; border: 1px solid #E3EAF5; border-radius: 999px;
    padding: 7px 12px; color: #3478F6; font-size: 12px; font-weight: 600;
    white-space: nowrap;
}

.hero {
    background:
        radial-gradient(circle at 88% 18%, rgba(124,77,255,0.35), transparent 28%),
        radial-gradient(circle at 70% 80%, rgba(52,120,246,0.25), transparent 32%),
        linear-gradient(115deg, #07152B 0%, #13244A 48%, #312E81 100%);
    color: #fff; border-radius: 22px; padding: 26px 30px 24px 30px;
    margin-bottom: 18px; position: relative; overflow: hidden; min-height: 164px;
    box-shadow: 0 16px 40px rgba(7,21,43,0.18);
}
.hero h1 { color: #FFFFFF; font-size: 28px; font-weight: 800; margin: 0 0 8px 0; letter-spacing: -0.04em; }
.hero p { color: #C9D7F0; font-size: 14.5px; margin: 0 0 16px 0; }
.hero-flow { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.hero-chip {
    background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.14);
    color: #E8EEFA; font-size: 12px; font-weight: 600;
    padding: 6px 10px; border-radius: 999px;
}
.hero-arrow { color: #8FB0FF; font-size: 12px; }
.hero-orb {
    position: absolute; right: 36px; top: 18px; width: 180px; height: 130px; opacity: 0.9;
    pointer-events: none;
}

.metric-card {
    background: #FFFFFF; border: 1px solid #E3EAF5; border-radius: 16px;
    padding: 16px 16px 14px 16px; min-height: 118px;
    box-shadow: 0 1px 2px rgba(20,33,61,0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(20,33,61,0.08); }
.metric-top { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.metric-icon {
    width: 34px; height: 34px; border-radius: 11px;
    display: flex; align-items: center; justify-content: center; font-size: 15px;
}
.metric-label { color: #71809B; font-size: 12px; font-weight: 600; }
.metric-value { color: #14213D; font-size: 28px; font-weight: 800; letter-spacing: -0.04em; line-height: 1; }
.metric-sub { color: #71809B; font-size: 11.5px; margin-top: 6px; }

.panel {
    background: #FFFFFF; border: 1px solid #E3EAF5; border-radius: 18px;
    padding: 16px 16px 12px 16px; margin-bottom: 14px;
    box-shadow: 0 1px 2px rgba(20,33,61,0.04);
    min-height: 100%;
}
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px; }
.panel-title { color: #14213D; font-size: 15px; font-weight: 700; margin: 0; }
.panel-link { color: #3478F6; font-size: 12px; font-weight: 600; }

.page-kicker { color: #71809B; font-size: 12px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 4px; }
.page-title { color: #14213D; font-size: 24px; font-weight: 800; letter-spacing: -0.03em; margin: 0 0 4px 0; }
.page-sub { color: #71809B; font-size: 13.5px; margin: 0 0 16px 0; }

.rf-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.rf-table th { color: #71809B; font-weight: 600; text-align: left; padding: 8px 6px; border-bottom: 1px solid #E3EAF5; font-size: 11px; }
.rf-table td { color: #14213D; padding: 10px 6px; border-bottom: 1px solid #EEF3FA; vertical-align: middle; }
.badge { display: inline-block; border-radius: 999px; padding: 2px 8px; font-size: 11px; font-weight: 700; }
.badge-high { background: #FEE2E2; color: #B91C1C; }
.badge-medium { background: #FEF3C7; color: #B45309; }
.badge-low { background: #DCFCE7; color: #047857; }
.badge-muted { background: #EEF2FF; color: #4338CA; }
.badge-warn { background: #FEF3C7; color: #B45309; }
.badge-ok { background: #DBEAFE; color: #1D4ED8; }

.contra-item { border: 1px solid #E3EAF5; border-radius: 12px; padding: 10px 12px; margin-bottom: 10px; background: #FBFCFE; }
.contra-topic { font-weight: 700; color: #14213D; font-size: 13px; margin-bottom: 6px; }
.contra-claim { font-size: 12px; color: #334155; line-height: 1.4; margin: 0 0 4px 0; }
.activity-item { display: flex; gap: 10px; padding: 8px 0; border-bottom: 1px solid #EEF3FA; }
.activity-dot { width: 9px; height: 9px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }
.activity-title { font-size: 12.5px; font-weight: 650; color: #14213D; }
.activity-sub { font-size: 11.5px; color: #71809B; }

.empty-state {
    background: #F8FAFF; border: 1px dashed #D5DEF0; border-radius: 12px;
    padding: 18px 16px; color: #71809B; font-size: 13px; text-align: center;
}
.gap-card {
    background: #FFFFFF; border: 1px solid #E3EAF5; border-radius: 14px;
    padding: 16px 18px; margin-bottom: 12px; border-left: 5px solid #3478F6;
}
.gap-card.high { border-left-color: #EF4444; }
.gap-card.medium { border-left-color: #F59E0B; }
.gap-card.low { border-left-color: #10B981; }
.comparability-warning, .ocr-warning, .integrity-box {
    border-radius: 12px; padding: 12px 14px; margin-bottom: 14px; font-size: 13px;
}
.comparability-warning { background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E; }
.ocr-warning { background: #FEF2F2; border: 1px solid #FECACA; color: #B91C1C; }
.integrity-box { background: #EEF2FF; border: 1px solid #C7D2FE; color: #312E81; }
.next-step {
    background: linear-gradient(180deg, #F4F1FF, #FFFFFF);
    border: 1px solid #E4D9FF; border-radius: 14px; padding: 12px 14px; margin-top: 8px;
}
.next-step h4 { margin: 0 0 6px 0; color: #4F46E5; font-size: 13px; }
.next-step p { margin: 0; color: #71809B; font-size: 12px; }

div[data-testid="stExpander"] {
    background: #FFFFFF; border: 1px solid #E3EAF5; border-radius: 12px;
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def category_label(key: str) -> str:
    raw = GAP_CATEGORIES.get(key, key or "General")
    return raw.split(" (")[0]


def goto(page: str):
    st.session_state.nav = page
    st.rerun()


def init_state():
    if "nav" not in st.session_state:
        st.session_state.nav = NAV_DASHBOARD
    if "search_q" not in st.session_state:
        st.session_state.search_q = ""


def get_projects():
    with database.get_connection() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def ensure_sample_data_loaded():
    existing = database.get_papers()
    if existing:
        return
    sample_files = list(PAPERS_DIR.glob("*.pdf"))
    if not sample_files:
        return
    for pdf_path in sample_files:
        try:
            extracted = extract_pdf_data(pdf_path)
            pid = database.save_paper(extracted)
            database.save_sections(pid, extracted.get("sections", []))
            database.save_summary(pid, extracted.get("summary", {}))
        except Exception:
            pass
    gap_detector.discover_gaps(force_refresh=True)
    contradiction_detector.detect_contradictions(force_refresh=True)


def page_header(title: str, subtitle: str, kicker: str = "ResearchFlow AI"):
    st.markdown(
        f'<div class="page-kicker">{esc(kicker)}</div>'
        f'<h1 class="page-title">{esc(title)}</h1>'
        f'<p class="page-sub">{esc(subtitle)}</p>',
        unsafe_allow_html=True,
    )


def priority_badge(level: str) -> str:
    lvl = (level or "Medium").title()
    cls = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(lvl, "badge-muted")
    return f'<span class="badge {cls}">{esc(lvl)}</span>'


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-lockup">
                <div class="brand-mark">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                        <path d="M12 3c-2.8 2.2-4 4.4-4 7.2 0 2.4 1.2 4.3 3 5.5v2.8h2v-2.8c1.8-1.2 3-3.1 3-5.5C16 7.4 14.8 5.2 12 3Z" fill="white"/>
                        <circle cx="9.2" cy="10.2" r="1" fill="#C4B5FD"/>
                        <circle cx="14.8" cy="10.2" r="1" fill="#C4B5FD"/>
                        <path d="M8 20h8v1.4c0 .3-.3.6-.6.6H8.6c-.3 0-.6-.3-.6-.6V20Z" fill="white"/>
                    </svg>
                </div>
                <div>
                    <div class="brand-title">ResearchFlow AI</div>
                    <div class="brand-sub">Literature Synthesis &amp; Research-Gap Discovery Agent</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
        for label, icon in PRIMARY_NAV:
            active = st.session_state.nav == label
            if st.button(f"{icon}    {label}", key=f"nav_{label}", use_container_width=True, type="primary" if active else "secondary"):
                if st.session_state.nav != label:
                    goto(label)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="nav-label">Library</div>', unsafe_allow_html=True)
        for label, icon in SECONDARY_NAV:
            active = st.session_state.nav == label
            if st.button(f"{icon}    {label}", key=f"nav_{label}", use_container_width=True, type="primary" if active else "secondary"):
                if st.session_state.nav != label:
                    goto(label)

        st.markdown(
            """
            <div class="sidebar-promo">
                <h4>Better Research. Greater Impact.</h4>
                <p>Turn research papers into meaningful insights.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_top_header(metrics: dict):
    left, mid, right = st.columns([6.2, 1.4, 2.0])
    with left:
        query = st.text_input(
            "Search",
            value=st.session_state.search_q,
            placeholder="Search papers, topics, authors, or keywords...",
            label_visibility="collapsed",
            key="global_search",
        )
        st.session_state.search_q = query or ""
    with mid:
        high = metrics.get("num_high_gaps", 0)
        st.markdown(
            f'<div class="notice-pill">High-priority gaps · {high}</div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div class="profile-chip">
                <div>
                    <div class="profile-name">Researcher</div>
                    <div class="profile-role">Workspace session</div>
                </div>
                <div class="avatar">RF</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_search_results(query: str):
    q = query.strip().lower()
    if len(q) < 2:
        return
    papers = database.get_papers()
    gaps = database.get_gaps()
    hits = []
    for p in papers:
        blob = " ".join([p.get("title") or "", p.get("authors") or "", p.get("abstract") or "", p.get("filename") or ""]).lower()
        if q in blob:
            hits.append(("Paper", p.get("title"), NAV_SAVED))
    for g in gaps:
        blob = " ".join([g.get("title") or "", g.get("description") or "", g.get("category") or ""]).lower()
        if q in blob:
            hits.append(("Gap", f"[{g.get('gap_code')}] {g.get('title')}", NAV_GAPS))
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f"**Search results for** `{query}`")
    if not hits:
        st.markdown('<div class="empty-state">No matching papers or gaps in the loaded collection.</div>', unsafe_allow_html=True)
    else:
        for kind, title, dest in hits[:12]:
            cols = st.columns([5, 1])
            cols[0].markdown(f"**{kind}** — {title}")
            if cols[1].button("Open", key=f"sr_{kind}_{title[:24]}"):
                goto(dest)
    st.markdown("</div>", unsafe_allow_html=True)


def plotly_cleanup(fig, legend=None):
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(legend=legend or PLOTLY_LEGEND)
    fig.update_xaxes(showgrid=True, gridcolor="#E3EAF5", zeroline=False, color="#71809B")
    fig.update_yaxes(showgrid=True, gridcolor="#E3EAF5", zeroline=False, color="#71809B")
    return fig


def literature_overview_figure(papers, summaries):
    if not papers:
        return None
    years = [p.get("year") for p in papers if p.get("year")]
    unique_years = sorted(set(years))
    if len(unique_years) >= 2:
        counts = Counter(years)
        df = pd.DataFrame({"Year": list(counts.keys()), "Papers": list(counts.values())}).sort_values("Year")
        df["Year"] = df["Year"].astype(str)
        fig = px.bar(df, x="Year", y="Papers", color="Papers", color_continuous_scale=["#C7D2FE", "#3478F6", "#4F46E5"])
        fig.update_layout(title="Research papers by publication year", coloraxis_showscale=False, height=280)
        fig.update_xaxes(type="category")
        return plotly_cleanup(fig)

    rows = []
    for p in papers:
        s = summaries.get(p["id"], {})
        domain = (s.get("methodology") or s.get("research_problem") or "Unspecified").split(".")[0][:28]
        rows.append({"Paper": (p.get("title") or "Untitled")[:22], "Sections": 0, "Focus": domain, "id": p["id"]})
    section_counts = Counter(sec["paper_id"] for sec in database.get_all_sections())
    for row in rows:
        row["Sections"] = section_counts.get(row["id"], 0)
    df = pd.DataFrame(rows)
    fig = px.bar(
        df, x="Paper", y="Sections", color="Focus",
        color_discrete_sequence=CHART_COLORS, height=280,
        title="Extracted evidence coverage by paper",
    )
    fig.update_layout(bargap=0.35)
    return plotly_cleanup(fig)


def gap_distribution_figure(gaps):
    if not gaps:
        return None
    counts = Counter(category_label(g.get("category")) for g in gaps)
    df = pd.DataFrame({"Category": list(counts.keys()), "Count": list(counts.values())})
    fig = go.Figure(data=[go.Pie(
        labels=df["Category"],
        values=df["Count"],
        hole=0.62,
        marker=dict(colors=CHART_COLORS[: len(df)], line=dict(color="#FFFFFF", width=2)),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>%{value} gaps (%{percent})<extra></extra>",
    )])
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(
        height=280,
        annotations=[dict(
            text=f"<b style='font-size:22px;color:#14213D'>{len(gaps)}</b><br><span style='color:#71809B'>Gaps</span>",
            x=0.5, y=0.5, showarrow=False,
        )],
        showlegend=True,
        legend=dict(orientation="v", y=0.5, x=1.02, font=dict(size=11, color="#71809B")),
        margin=dict(l=10, r=110, t=10, b=10),
    )
    return fig


def derive_recent_activity(papers, gaps, contradictions, proposals):
    events = []
    for p in papers:
        events.append({
            "ts": p.get("created_at") or "",
            "title": "New papers added",
            "detail": p.get("title") or p.get("filename") or "Paper ingested",
            "color": "#3478F6",
        })
    if gaps:
        stamp = gaps[0].get("created_at") or ""
        events.append({
            "ts": stamp,
            "title": "Research gaps discovered",
            "detail": f"{len(gaps)} candidate gaps identified from the collection",
            "color": "#7C4DFF",
        })
    if contradictions:
        stamp = contradictions[0].get("created_at") or ""
        events.append({
            "ts": stamp,
            "title": "Contradiction analysis finished",
            "detail": f"{len(contradictions)} conflicting findings compared",
            "color": "#F59E0B",
        })
    for prop in proposals:
        events.append({
            "ts": prop.get("created_at") or "",
            "title": "Proposal generated",
            "detail": prop.get("title") or "Research proposal",
            "color": "#10B981",
        })
    events = [e for e in events if e["ts"] or e["title"]]
    events.sort(key=lambda e: e["ts"] or "", reverse=True)
    return events[:6]


def render_dashboard():
    metrics = database.get_metrics_summary()
    papers = database.get_papers()
    summaries = database.get_summaries()
    gaps = database.get_gaps()
    contradictions = database.get_contradictions()
    proposals = database.get_proposals()

    topics = {category_label(g.get("category")) for g in gaps if g.get("category")}
    if not topics:
        for s in summaries.values():
            method = (s.get("methodology") or "").split(".")[0].strip()
            if method:
                topics.add(method[:48])
    num_topics = len(topics)

    st.markdown(
        """
        <div class="hero">
            <svg class="hero-orb" viewBox="0 0 220 140" fill="none">
                <circle cx="150" cy="58" r="46" stroke="rgba(255,255,255,0.18)" stroke-width="1.4"/>
                <circle cx="150" cy="58" r="22" fill="rgba(124,77,255,0.35)"/>
                <circle cx="118" cy="34" r="5" fill="#7C4DFF"/>
                <circle cx="186" cy="40" r="4" fill="#3478F6"/>
                <circle cx="178" cy="88" r="4.5" fill="#C4B5FD"/>
                <path d="M118 34 L150 58 L186 40 M150 58 L178 88" stroke="rgba(255,255,255,0.35)" stroke-width="1.2"/>
                <rect x="28" y="46" width="52" height="64" rx="6" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.22)"/>
                <rect x="40" y="36" width="52" height="64" rx="6" fill="rgba(255,255,255,0.16)" stroke="rgba(255,255,255,0.28)"/>
                <rect x="52" y="26" width="52" height="64" rx="6" fill="rgba(255,255,255,0.22)" stroke="rgba(255,255,255,0.32)"/>
            </svg>
            <h1>Welcome back, Researcher!</h1>
            <p>Discover research gaps. Analyze evidence. Build better research proposals.</p>
            <div class="hero-flow">
                <span class="hero-chip">Upload Papers</span><span class="hero-arrow">→</span>
                <span class="hero-chip">Analyze</span><span class="hero-arrow">→</span>
                <span class="hero-chip">Discover Gaps</span><span class="hero-arrow">→</span>
                <span class="hero-chip">Generate Proposals</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_specs = [
        ("Total Papers Analyzed", metrics["num_papers"], "Loaded in the research library" if metrics["num_papers"] else "Upload literature to begin", "#E8F0FE", "📄"),
        ("Research Topics Identified", num_topics, "From gap categories and paper analysis" if num_topics else "Topics appear after synthesis", "#EEE9FE", "🔎"),
        ("Research Gaps Found", metrics["num_gaps"], "Unique and actionable gaps" if metrics["num_gaps"] else "Run gap discovery after ingest", "#E7F8F0", "💡"),
        ("Contradictions Detected", metrics["num_contradictions"], "Conflicting findings across papers" if metrics["num_contradictions"] else "Need at least two papers", "#FEF4E6", "⚠"),
        ("Proposals Generated", metrics["num_proposals"], "Based on identified gaps" if metrics["num_proposals"] else "Generate from a selected gap", "#F3E8FF", "📝"),
    ]
    cols = st.columns(5)
    for col, (label, value, sub, bg, icon) in zip(cols, metric_specs):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-top">
                        <div class="metric-icon" style="background:{bg}">{icon}</div>
                        <div class="metric-label">{label}</div>
                    </div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-sub">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.35, 1.05, 0.9])
    with c1:
        st.markdown('<div class="panel"><div class="panel-head"><p class="panel-title">Literature Analysis Overview</p></div>', unsafe_allow_html=True)
        fig = literature_overview_figure(papers, summaries)
        if fig is None:
            st.markdown('<div class="empty-state">No papers loaded yet. Upload PDFs or load the benchmark corpus.</div>', unsafe_allow_html=True)
        else:
            st.plotly_chart(fig, use_container_width=True)
        if st.button("View details", key="dash_lit_details"):
            goto(NAV_LITERATURE)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="panel"><div class="panel-head"><p class="panel-title">Research Gap Distribution</p></div>', unsafe_allow_html=True)
        fig_gap = gap_distribution_figure(gaps)
        if fig_gap is None:
            st.markdown('<div class="empty-state">No gaps synthesized yet. Discover gaps from the loaded papers.</div>', unsafe_allow_html=True)
        else:
            st.plotly_chart(fig_gap, use_container_width=True)
            cats = sorted({category_label(g.get("category")) for g in gaps})
            chosen = st.selectbox("Inspect category", ["All categories"] + cats, key="dash_gap_cat")
            preview = gaps if chosen == "All categories" else [g for g in gaps if category_label(g.get("category")) == chosen]
            for g in preview[:3]:
                st.caption(f"• [{g.get('gap_code')}] {g.get('title')}")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="panel"><div class="panel-head"><p class="panel-title">Quick Actions</p></div>', unsafe_allow_html=True)
        actions = [
            ("Upload Research Papers", "PDF files from your corpus", NAV_SAVED, False),
            ("Run Literature Analysis", "Compare and summarize studies", NAV_LITERATURE, False),
            ("Discover Research Gaps", "Evidence-based gap detection", NAV_GAPS, True),
            ("Generate Research Proposal", "Based on identified gaps", NAV_PROPOSAL, False),
        ]
        for title, sub, dest, refresh_gaps in actions:
            st.caption(sub)
            if st.button(f"{title}  →", key=f"qa_{title}", use_container_width=True):
                if refresh_gaps:
                    gap_detector.discover_gaps(force_refresh=True)
                goto(dest)
        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1.35, 1.05, 0.9])
    with b1:
        head_l, head_r = st.columns([3, 1])
        with head_l:
            st.markdown('<div class="panel-title">Top Research Gaps</div>', unsafe_allow_html=True)
        with head_r:
            if st.button("View All", key="view_all_gaps"):
                goto(NAV_GAPS)
        top = gaps[:5]
        if not top:
            st.markdown('<div class="empty-state">No candidate gaps yet. Ingest papers and run discovery.</div>', unsafe_allow_html=True)
        else:
            rows_html = [
                "<table class='rf-table'><thead><tr><th>#</th><th>Research Gap</th><th>Domain</th><th>Priority</th><th>Evidence</th></tr></thead><tbody>"
            ]
            for i, g in enumerate(top, start=1):
                evidence_n = len(g.get("source_paper_ids") or [])
                rows_html.append(
                    "<tr>"
                    f"<td>{i}</td>"
                    f"<td>{esc(g.get('gap_code'))}: {esc((g.get('title') or '')[:72])}</td>"
                    f"<td>{esc(category_label(g.get('category')))}</td>"
                    f"<td>{priority_badge(g.get('priority_level'))}</td>"
                    f"<td>{evidence_n} papers</td>"
                    "</tr>"
                )
            rows_html.append("</tbody></table>")
            st.markdown("".join(rows_html), unsafe_allow_html=True)
            for g in top:
                with st.expander(f"Evidence for [{g.get('gap_code')}] {g.get('title')}"):
                    st.write(g.get("description"))
                    st.markdown(f"**Research question:** *{g.get('suggested_research_question') or 'N/A'}*")
                    st.caption(g.get("collective_support_explanation") or "")
                    for ep in g.get("evidence_passages") or []:
                        st.markdown(f"- **{ep.get('paper_title')} (p. {ep.get('page')})**")
                        st.caption(f"\"{ep.get('passage')}\"")
        st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        head_l, head_r = st.columns([3, 1])
        with head_l:
            st.markdown('<div class="panel-title">Contradiction Analysis</div>', unsafe_allow_html=True)
        with head_r:
            if st.button("View All", key="view_all_contra"):
                goto(NAV_CONTRA)
        if not contradictions:
            st.markdown('<div class="empty-state">No contradictions detected in the current collection.</div>', unsafe_allow_html=True)
        else:
            for c in contradictions[:3]:
                genuine = "Potential empirical conflict" if c.get("is_genuine_contradiction") else "Contextual / environmental divergence"
                badge = "badge-high" if c.get("is_genuine_contradiction") else "badge-warn"
                st.markdown(
                    f"""
                    <div class="contra-item">
                        <div class="contra-topic">{esc(c.get('topic'))} <span class="badge {badge}">{esc(genuine)}</span></div>
                        <p class="contra-claim"><b>Study A:</b> {esc((c.get('paper1_claim') or '')[:180])}</p>
                        <p class="contra-claim"><b>Study B:</b> {esc((c.get('paper2_claim') or '')[:180])}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if gaps:
                st.markdown(
                    """
                    <div class="next-step">
                        <h4>Next Step</h4>
                        <p>Turn a high-priority gap into a structured research proposal.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Generate Proposal →", key="dash_gen_prop"):
                    goto(NAV_PROPOSAL)

    with b3:
        st.markdown('<div class="panel-title">Recent Activity</div>', unsafe_allow_html=True)
        events = derive_recent_activity(papers, gaps, contradictions, proposals)
        if not events:
            st.markdown('<div class="empty-state">No timestamped activity is stored yet.</div>', unsafe_allow_html=True)
        else:
            for ev in events:
                ts = esc(ev["ts"]) if ev["ts"] else "Timestamp unavailable"
                st.markdown(
                    f"""
                    <div class="activity-item">
                        <div class="activity-dot" style="background:{ev['color']}"></div>
                        <div>
                            <div class="activity-title">{esc(ev['title'])}</div>
                            <div class="activity-sub">{esc(ev['detail'])}<br>{ts}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(
        """
        <div class="integrity-box">
            <b>Scientific integrity.</b> Factual claims stay tied to extracted passages and page numbers.
            Cross-paper metrics are not ranked when testbeds differ. The platform does not claim global novelty
            without external bibliographic verification.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_saved_projects():
    page_header("Saved Projects", "Upload and manage academic publications. PyMuPDF extracts metadata, structured sections, character offsets, and limitations.")
    projects = get_projects()
    if projects:
        st.markdown("#### Workspace collections")
        for proj in projects:
            st.markdown(
                f"<div class='panel'><b>{esc(proj.get('name'))}</b>"
                f"<div class='activity-sub'>{esc(proj.get('domain') or '')} · {esc(proj.get('description') or '')}</div></div>",
                unsafe_allow_html=True,
            )

    uploaded_files = st.file_uploader(
        "Upload Academic Papers (PDF format)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Supports single or batch PDF ingestion. Automatically extracts sections, checks for encryption, and detects scanned documents.",
    )

    if uploaded_files:
        for uf in uploaded_files:
            file_bytes = uf.read()
            fhash = calculate_file_hash(file_bytes)
            existing = database.get_paper_by_hash(fhash)
            if existing:
                st.warning(f"Document '{uf.name}' already ingested (Matched SHA-256 hash {fhash[:8]}...). Skipping duplicate.")
            else:
                try:
                    with st.spinner(f"Extracting structured sections from '{uf.name}'..."):
                        extracted = extract_pdf_data(file_bytes, filename=uf.name)
                        pid = database.save_paper(extracted)
                        database.save_sections(pid, extracted.get("sections", []))
                        database.save_summary(pid, extracted.get("summary", {}))
                        st.success(f"Successfully ingested '{extracted['title']}' ({extracted['num_pages']} pages, {len(extracted['sections'])} sections)")
                        if extracted.get("is_scanned"):
                            st.warning(extracted.get("ocr_message"))
                except PDFProcessingError as e:
                    st.error(f"Failed to process '{uf.name}': {str(e)}")
        gap_detector.discover_gaps(force_refresh=True)
        contradiction_detector.detect_contradictions(force_refresh=True)
        st.rerun()

    papers = database.get_papers()
    summaries = database.get_summaries()

    if not papers:
        st.markdown('<div class="empty-state">No papers currently loaded. Upload PDF files or load the industrial benchmark papers.</div>', unsafe_allow_html=True)
        if st.button("Load 5 Industrial Benchmark Papers"):
            ensure_sample_data_loaded()
            st.rerun()
        return

    st.write(f"**Loaded Papers ({len(papers)} Total):**")
    for p in papers:
        pid = p["id"]
        s = summaries.get(pid, {})
        with st.expander(f"[{p['year']}] {p['title']} — {p['authors']}"):
            col_meta1, col_meta2 = st.columns([3, 1])
            with col_meta1:
                st.write(f"**File:** `{p['filename']}` | **Pages:** {p['num_pages']} | **SHA-256:** `{p.get('file_hash', '')[:12]}...`")
            with col_meta2:
                if st.button(f"Delete Paper {pid}", key=f"del_{pid}"):
                    database.delete_paper(pid)
                    gap_detector.discover_gaps(force_refresh=True)
                    contradiction_detector.detect_contradictions(force_refresh=True)
                    st.rerun()

            if p.get("is_scanned"):
                st.markdown(
                    f'<div class="ocr-warning"><b>Scanned Document Warning:</b> This document contains low machine-readable text density. OCR is required to extract full content.</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("**Abstract:**")
            st.write(p.get("abstract") or "No abstract extracted.")
            st.markdown("**Extracted Structural Summary:**")
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                st.write(f"**Research Problem:** {s.get('research_problem', 'N/A')}")
                st.write(f"**Objective:** {s.get('objective', 'N/A')}")
                st.write(f"**Methodology:** {s.get('methodology', 'N/A')}")
            with c_s2:
                st.write(f"**Dataset / Testbed:** {s.get('dataset', 'N/A')}")
                st.write(f"**Key Findings:** {s.get('key_findings', 'N/A')}")
                st.write(f"**Reported Limitations (Page {s.get('limitations_page', 2)}):** {s.get('limitations', 'N/A')}")

            sections = database.get_sections_by_paper(pid)
            if sections:
                with st.expander(f"View {len(sections)} Structured Sections & Page References"):
                    for sec in sections:
                        st.markdown(f"**{sec['section_name']}** (Page {sec['page_num']}, characters {sec['char_start']}–{sec['char_end']})")
                        st.caption(sec["content"][:300] + ("..." if len(sec["content"]) > 300 else ""))


def render_literature():
    page_header("Literature Analysis", "Systematic multi-paper comparison matrix, common approaches, methodological divergences, and comparability constraints.")
    st.markdown(
        """
        <div class="comparability-warning">
            <b>Methodological Comparability Notice:</b> Numerical performance results (such as F1-scores, accuracy, or inference latencies)
            cannot be directly ranked against each other across distinct studies when physical testbeds, sensor modalities, or power envelopes differ.
            Consult the 'Comparability Constraints' column below for specific contextual boundaries.
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_comp = synthesis_engine.build_comparative_matrix()
    if df_comp.empty:
        st.markdown('<div class="empty-state">Please load papers in Saved Projects to view the comparative synthesis matrix.</div>', unsafe_allow_html=True)
        return

    st.dataframe(df_comp, use_container_width=True, height=350)
    col_exp1, col_exp2 = st.columns([1, 4])
    with col_exp1:
        csv_data = df_comp.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV Matrix", csv_data, "literature_synthesis_matrix.csv", "text/csv")
    with col_exp2:
        json_data = df_comp.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button("Download JSON Matrix", json_data, "literature_synthesis_matrix.json", "application/json")

    st.divider()
    themes = synthesis_engine.extract_synthesis_themes()
    c_th1, c_th2 = st.columns(2)
    with c_th1:
        st.markdown("#### Recurring Limitations Across Studies")
        for rl in themes.get("recurring_limitations", []):
            st.markdown(f"**• {rl['theme']}** ({rl['frequency']})")
            st.write(rl["description"])
            st.caption(f"Affected studies: {', '.join(rl.get('affected_papers', []))}")
            st.write("")
        st.markdown("#### Common Methodological Approaches")
        for ca in themes.get("common_approaches", []):
            st.markdown(f"• {ca}")
    with c_th2:
        st.markdown("#### Methodological Divergences")
        for md in themes.get("methodological_divergences", []):
            st.markdown(f"**• {md['dimension']}**")
            st.write(f"*{md['divergence']}*")
            st.caption(f"Operational Implication: {md['implication']}")
            st.write("")
        st.markdown("#### Underexplored Research Directions")
        for ut in themes.get("underexplored_topics", []):
            st.markdown(f"• {ut}")


def render_gap_discovery():
    page_header("Gap Discovery", "Traceable candidate research gaps synthesized from cross-study limitations, future-work statements, and empirical trade-offs.")
    col_btn, col_filter1, col_filter2 = st.columns([1.5, 2, 2])
    with col_btn:
        if st.button("Re-synthesize Gaps"):
            gap_detector.discover_gaps(force_refresh=True)
            st.success("Research gaps re-synthesized.")
            st.rerun()

    gaps = database.get_gaps()
    with col_filter1:
        cat_options = ["All Categories"] + list(GAP_CATEGORIES.keys())
        selected_cat = st.selectbox("Filter by Category", cat_options)
    with col_filter2:
        typ_options = ["All Typologies", "Class A (Explicit)", "Class B (Synthesized)", "Class C (Inferred)"]
        selected_typ = st.selectbox("Filter by Typology", typ_options)

    filtered_gaps = gaps
    if selected_cat != "All Categories":
        filtered_gaps = [g for g in filtered_gaps if g.get("category") == selected_cat]
    if selected_typ == "Class A (Explicit)":
        filtered_gaps = [g for g in filtered_gaps if "Explicitly" in g.get("classification", "")]
    elif selected_typ == "Class B (Synthesized)":
        filtered_gaps = [g for g in filtered_gaps if "Synthesized" in g.get("classification", "")]
    elif selected_typ == "Class C (Inferred)":
        filtered_gaps = [g for g in filtered_gaps if "Inferred" in g.get("classification", "")]

    if not filtered_gaps:
        st.markdown('<div class="empty-state">No research gaps match the active filter criteria.</div>', unsafe_allow_html=True)
        return

    st.write(f"Displaying **{len(filtered_gaps)} candidate research gaps**:")
    for g in filtered_gaps:
        plevel = (g.get("priority_level") or "Medium").lower()
        clf = g.get("classification", "")
        badge_class = "badge-low" if "Explicitly" in clf else ("badge-ok" if "Synthesized" in clf else "badge-warn")
        st.markdown(
            f"""
            <div class="gap-card {esc(plevel)}">
                <div style="display:flex;justify-content:space-between;gap:12px;margin-bottom:8px;">
                    <span style="font-size:16px;font-weight:700;color:#14213D;">[{esc(g.get('gap_code', 'GAP'))}] {esc(g.get('title'))}</span>
                    <span style="font-weight:700;color:#3478F6;">Priority Score: {esc(g.get('priority_score'))}/100 ({esc(g.get('priority_level'))})</span>
                </div>
                <div style="margin-bottom:10px;">
                    <span class="badge {badge_class}">{esc(clf)}</span>
                    <span class="badge badge-muted">{esc((g.get('category') or '').upper())}</span>
                    <span class="badge badge-ok">{esc(g.get('verification_status'))}</span>
                </div>
                <p style="color:#334155;font-size:13.5px;line-height:1.5;">{esc(g.get('description'))}</p>
                <div style="background:#F5F8FD;border:1px solid #E3EAF5;border-radius:8px;padding:10px 14px;">
                    <b>Suggested Research Question:</b><br>
                    <i style="color:#3478F6;">"{esc(g.get('suggested_research_question'))}"</i>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"Inspect Traceable Evidence & Source Passages for [{g.get('gap_code')}]"):
            st.markdown("**Collective Support Explanation:**")
            st.write(g.get("collective_support_explanation") or "N/A")
            st.markdown("**Exact Supporting Passages:**")
            for ep in g.get("evidence_passages", []):
                st.markdown(f"• **{ep.get('paper_title')} (Page {ep.get('page')}, {ep.get('type')}):**")
                st.caption(f"\"{ep.get('passage')}\"")
            st.markdown("**Alternative Interpretations:**")
            st.write(g.get("alternative_interpretations") or "None documented.")
            st.markdown("**Uncertainties & Risk Factors:**")
            st.write(g.get("uncertainties") or "None documented.")
            if st.button(f"Generate Research Proposal for {g.get('gap_code')}", key=f"btn_prop_{g['id']}"):
                proposal = proposal_generator.generate_proposal(g)
                st.success(f"Proposal '{proposal['title']}' created! Open Research Proposal to view and edit.")


def render_contradictions():
    page_header("Contradiction Analysis", "Identifies conflicting empirical claims across papers, explains contextual causes, and formulates fair comparison requirements.")
    st.markdown(
        """
        <div class="comparability-warning">
            <b>Scientific Neutrality Rule:</b> The platform never declares one study correct solely because its reported score is higher.
            Divergences are analyzed contextually based on physical testbeds, sensor bandwidths, and mechanical enclosures.
        </div>
        """,
        unsafe_allow_html=True,
    )
    conflicts = database.get_contradictions()
    if not conflicts:
        st.markdown('<div class="empty-state">No contradictions detected. Re-run analysis or ingest additional papers.</div>', unsafe_allow_html=True)
        if st.button("Run Contradiction Detector"):
            contradiction_detector.detect_contradictions(force_refresh=True)
            st.rerun()
        return

    st.write(f"Detected **{len(conflicts)} empirical controversies** across loaded studies:")
    for i, c in enumerate(conflicts, start=1):
        genuine = "Yes" if c.get("is_genuine_contradiction") else "Contextual / Environmental Divergence"
        with st.expander(f"Discrepancy #{i}: {c.get('topic')}", expanded=True):
            st.markdown(
                f"**Divergence Typology:** `{c.get('divergence_type')}` | **Detection Confidence:** `{c.get('confidence', 0.85):.0%}` | **Genuine Empirical Conflict:** `{genuine}`"
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"#### Claim A: {c.get('paper1_title')}")
                st.markdown(f"**Source Page:** Page {c.get('paper1_page', 1)}")
                st.markdown(f"**Extracted Claim:**\n> \"{c.get('paper1_claim')}\"")
                st.caption(f"**Methodology:** {c.get('paper1_method')}")
                st.caption(f"**Testbed / Modality:** {c.get('paper1_dataset')}")
                st.caption(f"**Reported Metrics:** {c.get('paper1_metrics')}")
            with c2:
                st.markdown(f"#### Claim B: {c.get('paper2_title')}")
                st.markdown(f"**Source Page:** Page {c.get('paper2_page', 1)}")
                st.markdown(f"**Extracted Claim:**\n> \"{c.get('paper2_claim')}\"")
                st.caption(f"**Methodology:** {c.get('paper2_method')}")
                st.caption(f"**Testbed / Modality:** {c.get('paper2_dataset')}")
                st.caption(f"**Reported Metrics:** {c.get('paper2_metrics')}")
            st.divider()
            st.markdown("#### Contextual Explanation for Disagreement:")
            st.write(c.get("explanation"))
            st.markdown("#### Requirements for Fair Empirical Comparison:")
            st.info(c.get("required_info_for_fair_comparison"))


def render_prioritization():
    page_header("Gap Prioritization", "Multi-criteria scoring model with configurable criteria weights, deterministic formula breakdown, and uncertainty disclosures.")
    st.markdown(
        r"""
        <div class="integrity-box">
            <b>Deterministic Scoring Formulation:</b><br>
            $$\text{Score} = 100 \times \frac{w_{\text{ev}} \cdot s_{\text{ev}} + w_{\text{imp}} \cdot s_{\text{imp}} + w_{\text{fea}} \cdot s_{\text{fea}} + w_{\text{unadd}} \cdot s_{\text{unadd}} + w_{\text{rec}} \cdot s_{\text{rec}}}{\sum w_i}$$
            <span style="font-size:12px;color:#71809B;">Prioritization scores are portfolio heuristics and must not be represented as scientifically validated global novelty.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("##### Adjust Criteria Weights")
    col_w1, col_w2, col_w3, col_w4, col_w5 = st.columns(5)
    with col_w1:
        w_ev = st.slider("Evidence Strength", 0.0, 1.0, 0.30, 0.05)
    with col_w2:
        w_imp = st.slider("Research Impact", 0.0, 1.0, 0.25, 0.05)
    with col_w3:
        w_fea = st.slider("Feasibility", 0.0, 1.0, 0.20, 0.05)
    with col_w4:
        w_unadd = st.slider("Unaddressed Score", 0.0, 1.0, 0.15, 0.05)
    with col_w5:
        w_rec = st.slider("Recency / Urgency", 0.0, 1.0, 0.10, 0.05)

    custom_weights = {
        "evidence_strength": w_ev,
        "impact": w_imp,
        "feasibility": w_fea,
        "unaddressed_score": w_unadd,
        "recency": w_rec,
    }
    ranked_gaps = prioritization_engine.reorder_gaps(custom_weights)
    if not ranked_gaps:
        st.markdown('<div class="empty-state">No gaps to prioritize. Discover gaps first.</div>', unsafe_allow_html=True)
        return

    chart_rows = []
    for g in ranked_gaps:
        sc = g.get("scoring_details", {})
        for crit, val in sc.get("contributions", {}).items():
            chart_rows.append({
                "Gap": f"{g.get('gap_code')}: {str(g.get('title') or '')[:24]}...",
                "Criterion": crit,
                "Score Contribution": val,
            })
    df_chart = pd.DataFrame(chart_rows)
    fig_bar = px.bar(
        df_chart, x="Score Contribution", y="Gap", color="Criterion",
        title="Criteria Contribution Breakdown to Priority Score",
        orientation="h",
        color_discrete_sequence=CHART_COLORS,
        height=320,
    )
    st.plotly_chart(plotly_cleanup(fig_bar), use_container_width=True)

    st.markdown("##### Ranked Research Gaps with Uncertainty Disclosures")
    for rank, g in enumerate(ranked_gaps, start=1):
        sc = g.get("scoring_details", {})
        with st.expander(f"Rank #{rank} | [{g.get('gap_code')}] {g.get('title')} — Score: {g['priority_score']}/100"):
            st.markdown(priority_badge(g.get("priority_level")), unsafe_allow_html=True)
            st.write(f"**Description:** {g.get('description')}")
            st.write(f"**Research Question:** *{g.get('suggested_research_question')}*")
            st.markdown("**Criteria Contribution Breakdown:**")
            contrib_cols = st.columns(5)
            for i, (crit_name, val) in enumerate(sc.get("contributions", {}).items()):
                with contrib_cols[i]:
                    st.metric(crit_name, f"+{val:.1f}")
            st.markdown("**Missing Information & Uncertainty Disclosures:**")
            missing = sc.get("missing_info", [])
            if missing:
                for m in missing:
                    st.warning(m)
            else:
                st.success("Corroborating multi-study evidence available.")


def render_evidence_explorer():
    page_header("Evidence Explorer", "Interactive provenance network and external literature verification against scholarly registries.")
    tab_graph, tab_verify = st.tabs(["Evidence Graph", "External Literature Verification"])

    with tab_graph:
        G = evidence_graph_engine.build_network()
        col_g1, col_g2 = st.columns([3, 1])
        with col_g2:
            st.markdown("**Graph Entity Filters**")
            st.write(f"Total Nodes: **{len(G.nodes)}**")
            st.write(f"Total Edges: **{len(G.edges)}**")
            st.markdown(
                """
                **Legend:**
                - Papers
                - Methods & Findings
                - Datasets
                - Reported Limitations
                - Candidate Research Gaps
                - Project Proposals
                """
            )
        with col_g1:
            fig_graph = evidence_graph_engine.generate_plotly_figure(G)
            fig_graph.update_layout(paper_bgcolor="white", plot_bgcolor="white", font=dict(family="Inter, sans-serif", color="#14213D"))
            st.plotly_chart(fig_graph, use_container_width=True)

        st.markdown("#### Interactive Node Inspection")
        node_names = list(G.nodes)
        if node_names:
            selected_node = st.selectbox(
                "Inspect Details for Node",
                node_names,
                format_func=lambda x: f"{G.nodes[x].get('label', x)} ({G.nodes[x].get('type', 'entity')})",
            )
            node_info = G.nodes[selected_node]
            st.markdown(f"**Type:** `{node_info.get('type')}` | **Label:** `{node_info.get('label')}`")
            st.info(node_info.get("details", "No additional details."))
            in_edges = list(G.in_edges(selected_node, data=True))
            out_edges = list(G.out_edges(selected_node, data=True))
            c_in, c_out = st.columns(2)
            with c_in:
                st.markdown(f"**Inbound Connections ({len(in_edges)}):**")
                for u, v, d in in_edges:
                    st.caption(f"← {G.nodes[u].get('label', u)} via `{d.get('relationship')}`")
            with c_out:
                st.markdown(f"**Outbound Connections ({len(out_edges)}):**")
                for u, v, d in out_edges:
                    st.caption(f"→ {G.nodes[v].get('label', v)} via `{d.get('relationship')}`")

    with tab_verify:
        gaps = database.get_gaps()
        if not gaps:
            st.markdown('<div class="empty-state">No research gaps synthesized yet.</div>', unsafe_allow_html=True)
        else:
            gap_options = {f"[{g.get('gap_code')}] {g.get('title')}": g for g in gaps}
            selected_label = st.selectbox("Select Candidate Gap to Verify", list(gap_options.keys()))
            target_gap = gap_options[selected_label]
            col_prov, col_btn = st.columns([3, 1])
            with col_prov:
                provider = st.selectbox(
                    "Scholarly Search Provider",
                    ["crossref", "openalex", "local_benchmark"],
                    format_func=lambda x: {
                        "crossref": "Crossref REST API (Public Registry)",
                        "openalex": "OpenAlex REST API (Global Open Index)",
                        "local_benchmark": "Verified Authentic Benchmark Corpus (Offline Mode)",
                    }.get(x, x),
                )
            with col_btn:
                st.write("")
                run_verification = st.button("Run Verification", type="primary")

            suggested_queries = verification_engine.generate_search_queries(target_gap)
            st.markdown("**Generated Targeted Search Queries:**")
            for q in suggested_queries:
                st.caption(f"• `{q}`")

            if run_verification:
                with st.spinner("Querying scholarly database and comparing external literature..."):
                    res = verification_engine.verify_gap(target_gap, provider=provider)
                    if res.get("is_offline"):
                        st.warning(res.get("error_message"))
                    else:
                        st.success(f"Verification complete via {res['provider'].upper()}.")

            curr_status = target_gap.get("verification_status", "Requires human verification")
            st.markdown(f"#### Current Verification Status: `{curr_status}`")
            records = database.get_verification_records(target_gap["id"])
            if records:
                st.markdown(f"**Verification Audit History ({len(records)} runs):**")
                for rec in records:
                    with st.expander(f"Run #{rec['id']} | Status: {rec['verification_status']} | Provider: {rec['provider']}"):
                        st.write(f"**Query Executed:** `{rec['search_query']}`")
                        st.write(f"**Synthesis Notes:** {rec['synthesis_notes']}")
                        st.markdown("**Retrieved Academic Literature:**")
                        for paper in rec.get("results", []):
                            st.markdown(f"• **[{paper.get('year')}] {paper.get('title')}**")
                            st.caption(f"Authors: {paper.get('authors')} | Venue: {paper.get('venue')} | DOI: {paper.get('doi')}")
                            if paper.get("url"):
                                st.caption(f"Link: {paper.get('url')}")
                            st.caption(f"Abstract: {paper.get('abstract', '')[:250]}...")
                            st.info(f"Relation to Candidate Gap: {paper.get('relation_type')} — {paper.get('relevance_notes')}")


def render_proposals():
    page_header("Research Proposal", "Transforms an evidence-grounded research gap into an academic grant or industrial R&D project proposal.")
    gaps = database.get_gaps()
    proposals = database.get_proposals()
    tab_create, tab_view = st.tabs(["Draft New Proposal from Gap", f"Saved Proposals ({len(proposals)})"])

    with tab_create:
        if not gaps:
            st.markdown('<div class="empty-state">No candidate gaps available.</div>', unsafe_allow_html=True)
        else:
            gap_choices = {f"[{g.get('gap_code')}] {g.get('title')}": g for g in gaps}
            sel_gap_label = st.selectbox("Select Research Gap to Formulate Proposal", list(gap_choices.keys()))
            chosen_gap = gap_choices[sel_gap_label]
            if st.button("Formulate Complete Research Proposal", type="primary"):
                with st.spinner("Synthesizing research questions, methodologies, baseline methods, and feasibility assessments..."):
                    new_prop = proposal_generator.generate_proposal(chosen_gap)
                    st.success(f"Proposal '{new_prop['title']}' generated and saved!")
                    st.rerun()

    with tab_view:
        if not proposals:
            st.markdown('<div class="empty-state">No proposals generated yet. Use the tab above to formulate one.</div>', unsafe_allow_html=True)
            return
        for prop in proposals:
            with st.expander(f"Proposal: {prop.get('title')}", expanded=True):
                st.markdown(f"**Target Gap:** `{prop.get('gap_title')}` | **Created:** `{prop.get('created_at')}`")
                st.markdown("#### 1. Problem Statement & Background")
                st.write(prop.get("problem_statement"))
                st.caption(prop.get("background"))
                st.markdown("#### 2. Research Questions & Hypotheses")
                for rq in prop.get("research_questions", []):
                    st.markdown(f"• **{rq}**")
                for h in prop.get("hypotheses", []):
                    st.markdown(f"• *{h}*")
                st.markdown("#### 3. Proposed Methodology (3-Phase Formulation)")
                st.text_area("Proposed Methodology (Editable)", prop.get("proposed_methodology"), height=180, key=f"meth_{prop['id']}")
                st.markdown("#### 4. Dataset Requirements & Evaluation Metrics")
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    st.write(f"**Sensory & Data Specifications:**\n{prop.get('dataset_requirements')}")
                with c_d2:
                    st.write(f"**Target Evaluation Metrics:**\n{prop.get('evaluation_metrics')}")
                st.markdown("#### 5. Baseline Methods for Empirical Benchmarking")
                st.text(prop.get("baseline_methods"))
                st.markdown("#### 6. Expected Challenges & Risk Mitigations")
                for cm in prop.get("challenges_mitigations", []):
                    st.markdown(f"• **Risk:** {cm.get('challenge')}")
                    st.caption(f"  *Mitigation Strategy:* {cm.get('mitigation')}")
                st.markdown("#### 7. Feasibility Assessment & Known Limitations")
                st.write(f"**Feasibility:** {prop.get('feasibility_assessment')}")
                st.caption(f"**Limitations:** {prop.get('limitations')}")
                st.warning(prop.get("human_verification_note"))
                if st.button(f"Delete Proposal #{prop['id']}", key=f"del_prop_{prop['id']}"):
                    database.delete_proposal(prop["id"])
                    st.rerun()


def render_settings():
    page_header("Settings", "Downloadable PDF / DOCX academic synthesis reports, LLM provider status, and database operations.")
    tab_rep, tab_set = st.tabs(["Downloadable Reports", "System & LLM Settings"])
    with tab_rep:
        st.markdown("#### Download Academic Synthesis Reports")
        st.caption("Full report containing Executive Overview, Individual Paper Summaries, Comparative Matrix, Contradictions, Traceable Gaps, and Project Proposals.")
        proposals = database.get_proposals()
        prop_id_choice = None
        if proposals:
            prop_choice_map = {f"Proposal #{p['id']}: {p['title']}": p["id"] for p in proposals}
            sel_p = st.selectbox("Select Proposal to include in Report", list(prop_choice_map.keys()))
            prop_id_choice = prop_choice_map[sel_p]

        c_pdf, c_docx = st.columns(2)
        with c_pdf:
            if st.button("Generate PDF Synthesis Report (ReportLab)", type="primary"):
                with st.spinner("Rendering academic PDF document with ReportLab..."):
                    pdf_path = report_generator.generate_pdf_report(proposal_id=prop_id_choice)
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(label="Download Generated PDF", data=pdf_bytes, file_name=pdf_path.name, mime="application/pdf")
                    st.success(f"PDF Report generated: {pdf_path.name}")
        with c_docx:
            if st.button("Generate DOCX Synthesis Report (python-docx)"):
                with st.spinner("Generating formatted Microsoft Word report..."):
                    docx_path = report_generator.generate_docx_report(proposal_id=prop_id_choice)
                    with open(docx_path, "rb") as f:
                        docx_bytes = f.read()
                    st.download_button(
                        label="Download Generated DOCX",
                        data=docx_bytes,
                        file_name=docx_path.name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                    st.success(f"DOCX Report generated: {docx_path.name}")

    with tab_set:
        st.markdown("#### Configuration & Database Persistence")
        st.write(f"**Database Location:** `{database.DB_PATH}`")
        st.markdown("##### LLM Configuration")
        st.caption("Configurable through environment variables or `.env` file.")
        st.text_input("Current LLM Provider", value=llm_client.provider.upper(), disabled=True)
        st.caption("To enable OpenAI, Gemini, or Groq, edit your `.env` file and set `LLM_PROVIDER=openai` (or `gemini`/`groq`).")
        st.divider()
        st.markdown("##### Database Operations")
        if st.button("Reset All Application Data"):
            database.clear_all_data()
            st.warning("All papers, sections, gaps, and proposals cleared from SQLite database.")
            st.rerun()


def render_help():
    page_header("Help & Support", "Grounded evidence Q&A across uploaded papers, plus platform usage notes.")
    st.markdown(
        """
        <div class="integrity-box">
            Ask questions about methodologies, datasets, results, limitations, or future work. Answers cite
            paper titles, sections, page numbers, and similarity scores. Out-of-scope questions return an insufficient-evidence statement.
        </div>
        """,
        unsafe_allow_html=True,
    )
    sample_questions = [
        "What is the inference latency and power consumption of INT8 quantization on STM32 microcontrollers?",
        "What is the reported accuracy drop when transferring models across different motor horsepower ratings?",
        "Under what factory noise levels does cavitation detection accuracy collapse?",
        "What are the communication bottlenecks reported for federated learning in distributed factories?",
    ]
    chosen_sample = st.selectbox("Select a benchmark question or type below:", ["-- Custom Query --"] + sample_questions)
    default_q = "" if chosen_sample == "-- Custom Query --" else chosen_sample
    user_query = st.text_input("Research Question:", value=default_q, placeholder="e.g. What are the reported limitations of acoustic emission?")
    if st.button("Retrieve Evidence & Answer", key="btn_qa"):
        if user_query:
            with st.spinner("Retrieving relevant passages and evaluating textual evidence..."):
                res = qa_engine.answer_query(user_query)
                if not res["sufficient_evidence"]:
                    st.warning(res["answer"])
                else:
                    st.markdown(res["answer"])
                    st.markdown("##### Retrieved Provenance Passages:")
                    for src in res.get("sources", []):
                        st.markdown(f"**Source {src['source_id']}: {src['paper_title']}** (Page {src['page']}, {src['section']})")
                        st.caption(f"\"{src['passage_snippet']}\"")
                        st.caption(f"Similarity Score: {src['similarity_score']:.4f}")

    st.divider()
    st.markdown("#### How to use ResearchFlow AI")
    st.markdown(
        """
        1. **Saved Projects** — ingest PDFs (or load the five industrial benchmark papers).
        2. **Literature Analysis** — review the comparative matrix and export CSV/JSON.
        3. **Gap Discovery / Contradiction Analysis / Gap Prioritization** — inspect evidence-linked findings.
        4. **Evidence Explorer** — inspect the provenance graph and run Crossref/OpenAlex verification.
        5. **Research Proposal** — draft a proposal from a selected gap.
        6. **Settings** — export PDF/DOCX reports or reset the local database.
        """
    )


def main():
    init_state()
    ensure_sample_data_loaded()
    metrics = database.get_metrics_summary()
    render_sidebar()
    render_top_header(metrics)

    query = st.session_state.get("search_q") or ""
    if query.strip() and st.session_state.nav == NAV_DASHBOARD:
        render_search_results(query)

    page = st.session_state.nav
    if page == NAV_DASHBOARD:
        render_dashboard()
    elif page == NAV_LITERATURE:
        render_literature()
    elif page == NAV_GAPS:
        render_gap_discovery()
    elif page == NAV_CONTRA:
        render_contradictions()
    elif page == NAV_EVIDENCE:
        render_evidence_explorer()
    elif page == NAV_PRIO:
        render_prioritization()
    elif page == NAV_PROPOSAL:
        render_proposals()
    elif page == NAV_SAVED:
        render_saved_projects()
    elif page == NAV_SETTINGS:
        render_settings()
    elif page == NAV_HELP:
        render_help()
    else:
        render_dashboard()


main()
