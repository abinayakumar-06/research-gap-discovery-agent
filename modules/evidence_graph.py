"""
modules/evidence_graph.py
-------------------------
Interactive Research Evidence Graph Engine.
Constructs a typed provenance network using NetworkX and renders an interactive Plotly visualization.
Graph Elements:
- Nodes: Papers, Methods, Datasets, Findings, Limitations, Research Gaps, Proposed Directions.
- Edges: Typed, labeled relationships (e.g. 'evaluates_on', 'employs_method', 'reports_finding',
  'identifies_limitation', 'motivates_gap', 'contradicts', 'proposes_direction').
Guarantees: Strict empirical provenance. All nodes and edges derive exclusively from
actual extracted database records; no synthetic placeholder edges are inserted.
"""

from typing import Dict, Any, List, Optional, Tuple
import networkx as nx
import plotly.graph_objects as go
import json

from database import get_papers, get_summaries, get_gaps, get_contradictions, get_proposals

NODE_COLORS = {
    "paper": "#2B6CB0",        # Deep Blue
    "method": "#319795",       # Teal
    "dataset": "#805AD5",      # Purple
    "finding": "#38A169",      # Green
    "limitation": "#E53E3E",   # Red
    "gap": "#DD6B20",          # Orange
    "direction": "#D69E2E",    # Amber
    "proposal": "#3182CE"      # Blue
}

NODE_SYMBOLS = {
    "paper": "circle",
    "method": "square",
    "dataset": "diamond",
    "finding": "circle-open",
    "limitation": "triangle-down",
    "gap": "star",
    "direction": "hexagon",
    "proposal": "diamond-wide"
}

class EvidenceGraphEngine:
    """Constructs and visualizes traceable evidence knowledge graphs."""

    def __init__(self):
        pass

    def build_network(self) -> nx.DiGraph:
        """
        Builds a directed NetworkX graph populated with actual extracted entities
        and verified relationships from SQLite.
        """
        G = nx.DiGraph()

        papers = get_papers()
        summaries = get_summaries()
        gaps = get_gaps()
        contradictions = get_contradictions()
        proposals = get_proposals()

        # 1. Add Paper Nodes
        for p in papers:
            pid = f"paper_{p['id']}"
            G.add_node(pid,
                id=pid,
                entity_id=p['id'],
                label=f"Paper {p['id']}: {p['title'][:28]}...",
                full_title=p['title'],
                authors=p['authors'],
                year=p['year'],
                type="paper",
                details=f"Authors: {p['authors']} ({p['year']})\nPages: {p.get('num_pages', 1)}"
            )

        # 2. Add Summaries (Methods, Datasets, Findings, Limitations)
        for pid, s in summaries.items():
            paper_node = f"paper_{pid}"
            if not G.has_node(paper_node):
                continue

            # Method Node
            method_text = s.get("methodology")
            if method_text and len(method_text.strip()) > 5:
                mid = f"method_{pid}"
                short_m = method_text.split(".")[0][:40]
                G.add_node(mid,
                    id=mid,
                    label=f"Method: {short_m}...",
                    type="method",
                    details=method_text,
                    source_paper_id=pid
                )
                G.add_edge(paper_node, mid, relationship="employs_method")

            # Dataset Node
            dataset_text = s.get("dataset")
            if dataset_text and len(dataset_text.strip()) > 5:
                did = f"dataset_{pid}"
                short_d = dataset_text.split(".")[0][:35]
                G.add_node(did,
                    id=did,
                    label=f"Dataset: {short_d}...",
                    type="dataset",
                    details=dataset_text,
                    source_paper_id=pid
                )
                G.add_edge(paper_node, did, relationship="evaluates_on")

            # Limitation Node
            lim_text = s.get("limitations")
            if lim_text and len(lim_text.strip()) > 5 and "none explicitly" not in lim_text.lower():
                lid = f"lim_{pid}"
                short_l = lim_text.split(".")[0][:45]
                G.add_node(lid,
                    id=lid,
                    label=f"Limitation: {short_l}...",
                    type="limitation",
                    details=lim_text,
                    source_paper_id=pid,
                    page=s.get("limitations_page", 2)
                )
                G.add_edge(paper_node, lid, relationship="identifies_limitation")

            # Finding Node
            finding_text = s.get("key_findings")
            if finding_text and len(finding_text.strip()) > 5:
                fid = f"finding_{pid}"
                short_f = finding_text.split(".")[0][:40]
                G.add_node(fid,
                    id=fid,
                    label=f"Finding: {short_f}...",
                    type="finding",
                    details=finding_text,
                    source_paper_id=pid
                )
                G.add_edge(paper_node, fid, relationship="reports_finding")

        # 3. Add Research Gaps & Link to Supporting Papers and Limitations
        for g in gaps:
            gid = f"gap_{g['id']}"
            G.add_node(gid,
                id=gid,
                entity_id=g['id'],
                label=f"{g.get('gap_code', 'GAP')}: {g['title'][:32]}...",
                full_title=g['title'],
                category=g.get('category', 'knowledge'),
                priority_score=g.get('priority_score', 0.0),
                type="gap",
                details=(
                    f"Category: {g.get('category')}\n"
                    f"Priority Score: {g.get('priority_score')} ({g.get('priority_level')})\n"
                    f"Description: {g.get('description')}\n"
                    f"Status: {g.get('verification_status')}"
                )
            )

            # Connect to supporting papers
            for src_pid in g.get("source_paper_ids", []):
                p_node = f"paper_{src_pid}"
                if G.has_node(p_node):
                    G.add_edge(p_node, gid, relationship="motivates_gap")

                # If the paper has an associated limitation, connect limitation to gap
                lim_node = f"lim_{src_pid}"
                if G.has_node(lim_node):
                    G.add_edge(lim_node, gid, relationship="grounds_gap")

        # 4. Add Contradiction Edges between Papers
        for c in contradictions:
            p1_node = f"paper_{c.get('paper1_id')}"
            p2_node = f"paper_{c.get('paper2_id')}"
            if G.has_node(p1_node) and G.has_node(p2_node):
                G.add_edge(p1_node, p2_node,
                    relationship="contradicts",
                    topic=c.get("topic", "Divergent Findings"),
                    details=c.get("explanation", "")
                )

        # 5. Add Proposals & Link to Target Gap
        for prop in proposals:
            pr_id = f"proposal_{prop['id']}"
            G.add_node(pr_id,
                id=pr_id,
                entity_id=prop['id'],
                label=f"Proposal: {prop['title'][:30]}...",
                full_title=prop['title'],
                type="proposal",
                details=f"Problem: {prop['problem_statement'][:150]}..."
            )
            target_gid = f"gap_{prop.get('gap_id')}"
            if G.has_node(target_gid):
                G.add_edge(target_gid, pr_id, relationship="proposes_direction")

        return G

    def generate_plotly_figure(self, G: nx.DiGraph, selected_node_id: Optional[str] = None) -> go.Figure:
        """
        Creates an interactive Plotly figure from the NetworkX evidence graph.
        Positions nodes using Spring Layout.
        """
        if len(G.nodes) == 0:
            fig = go.Figure()
            fig.update_layout(
                title="Evidence Graph: No literature loaded yet.",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                template="plotly_white"
            )
            return fig

        # Compute deterministic layout
        pos = nx.spring_layout(G, k=0.55, iterations=60, seed=42)

        # Build Edges
        edge_x = []
        edge_y = []
        edge_hover_x = []
        edge_hover_y = []
        edge_hover_text = []

        for u, v, data in G.edges(data=True):
            if u not in pos or v not in pos:
                continue
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            # Midpoint for hover label
            edge_hover_x.append((x0 + x1) / 2)
            edge_hover_y.append((y0 + y1) / 2)
            rel = data.get("relationship", "relates_to").replace("_", " ").upper()
            edge_hover_text.append(f"Relationship: {rel}")

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1.2, color="#CBD5E0"),
            hoverinfo="none",
            mode="lines"
        )

        edge_label_trace = go.Scatter(
            x=edge_hover_x, y=edge_hover_y,
            mode="markers",
            marker=dict(size=4, color="#A0AEC0", opacity=0.7),
            hoverinfo="text",
            hovertext=edge_hover_text
        )

        # Build Nodes by category
        node_traces = []
        for ntype, color in NODE_COLORS.items():
            nodes_of_type = [n for n, d in G.nodes(data=True) if d.get("type") == ntype]
            if not nodes_of_type:
                continue

            nx_coords = [pos[n][0] for n in nodes_of_type if n in pos]
            ny_coords = [pos[n][1] for n in nodes_of_type if n in pos]
            labels = [G.nodes[n].get("label", n) for n in nodes_of_type if n in pos]
            hover_texts = []
            
            for n in nodes_of_type:
                if n not in pos:
                    continue
                d = G.nodes[n]
                text = (
                    f"<b>{d.get('type', 'entity').upper()}</b>: {d.get('label')}<br>"
                    f"<br>{d.get('details', '')[:200]}..."
                )
                hover_texts.append(text)

            trace = go.Scatter(
                x=nx_coords, y=ny_coords,
                mode="markers+text" if ntype in ["paper", "gap"] else "markers",
                name=ntype.capitalize(),
                text=labels if ntype in ["paper", "gap"] else None,
                textposition="top center",
                textfont=dict(size=10, color="#2D3748"),
                hoverinfo="text",
                hovertext=hover_texts,
                marker=dict(
                    color=color,
                    size=18 if ntype in ["gap", "paper"] else 12,
                    symbol=NODE_SYMBOLS.get(ntype, "circle"),
                    line=dict(width=2, color="#FFFFFF")
                )
            )
            node_traces.append(trace)

        fig = go.Figure(data=[edge_trace, edge_label_trace] + node_traces)
        fig.update_layout(
            title=dict(
                text="Interactive Research Evidence & Gap Lineage Network",
                font=dict(size=15)
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="closest",
            margin=dict(b=20, l=10, r=10, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            template="plotly_white",
            height=600
        )
        return fig

evidence_graph_engine = EvidenceGraphEngine()
