"""Streamlit UI for quant-qual-bridge.

Design choices that reflect the discovery framing:
  - The bridge view uses a *bipartite graph* with edge widths proportional to
    the number of evidence kinds (1, 2, or 3) — discrete, not continuous.
  - No edge is labelled "confidence" or "strength"; the legend says "evidence kinds".
  - Each selected correspondence opens an inspection panel where the researcher
    annotates: "Mark for follow-up", "Likely spurious", "Already verified separately".
  - The "What this is / what it is not" banner is fixed at the top.
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from .bridge import build_bridge
from .llm import DEFAULT_BACKEND, SUPPORTED_BACKENDS
from .loaders import load_segments, load_themes
from .models import BridgeReport

st.set_page_config(
    page_title="Quant–Qual Bridge",
    page_icon="🔗",
    layout="wide",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
    .stApp {
        background: #fafafa;
    }
    h1, h2, h3 {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }
    code, .mono {
        font-family: 'DM Mono', ui-monospace, SFMono-Regular, monospace !important;
    }
    .banner {
        background: #fffbea;
        border-left: 3px solid #f0b429;
        padding: 12px 16px;
        margin-bottom: 16px;
        font-size: 13px;
        color: #5c4a13;
        border-radius: 4px;
    }
    .evidence-pill {
        display: inline-block;
        padding: 2px 8px;
        margin: 2px 4px 2px 0;
        font-size: 11px;
        border-radius: 99px;
        font-family: 'DM Mono', ui-monospace, monospace;
    }
    .pill-lex { background: #e6f1fb; color: #185fa5; border: 0.5px solid #b5d4f4; }
    .pill-tag { background: #e1f5ee; color: #0f6e56; border: 0.5px solid #a8e0cb; }
    .pill-ppl { background: #faeeda; color: #854f0b; border: 0.5px solid #fac775; }
    .corr-card {
        background: #fff;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown("# Quant–Qual Bridge")
st.markdown(
    "Surface possible correspondences between quantitative segments and "
    "qualitative themes — for the researcher to inspect."
)

st.markdown(
    """
    <div class="banner">
    <b>What this is</b>: a discovery surface. Each correspondence below is a
    candidate worth your inspection.<br>
    <b>What it is not</b>: a triangulation engine. There is no fused
    confidence score. Evidence kinds are kept separate by design.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### Inputs")
    seg_file = st.file_uploader("Quantitative segments (JSON)", type=["json"], key="seg")
    theme_file = st.file_uploader("Qualitative themes (JSON)", type=["json"], key="theme")

    st.markdown("### Matching")
    min_lex = st.slider("Min shared content terms", 1, 6, 2,
                        help="Lower this to surface more candidates.")

    st.markdown("### LLM enrichment")
    use_llm = st.toggle("Enable inspection notes", value=True,
                       help="On by default. Adds a short rationale and inspection questions per correspondence.")
    backend = st.selectbox(
        "Backend",
        SUPPORTED_BACKENDS,
        index=SUPPORTED_BACKENDS.index(DEFAULT_BACKEND),
        disabled=not use_llm,
    )
    max_enr = st.number_input("Max enrichments", 1, 200, 30, disabled=not use_llm)


# ---------- Helpers ----------
def _load_uploaded(file, kind: str):
    if file is None:
        return None
    payload = json.loads(file.read())
    tmp_path = Path(f"/tmp/qqb_{kind}.json")
    tmp_path.write_text(json.dumps(payload), encoding="utf-8")
    if kind == "segments":
        return load_segments(tmp_path)
    return load_themes(tmp_path)


def _evidence_pills(corr) -> str:
    cls = {
        "lexical_overlap": "pill-lex",
        "tag_match": "pill-tag",
        "shared_participants": "pill-ppl",
    }
    label = {
        "lexical_overlap": "lexical",
        "tag_match": "tag",
        "shared_participants": "participants",
    }
    chunks = []
    for e in corr.evidence:
        chunks.append(
            f'<span class="evidence-pill {cls[e.kind]}">{label[e.kind]} · {len(e.items)}</span>'
        )
    return "".join(chunks)


def _bridge_diagram(report: BridgeReport):
    """Render a bipartite Sankey-like diagram using Plotly.

    Edge widths are *discrete* — 1, 2, or 3 — corresponding to the number of
    evidence kinds. We deliberately do NOT scale them by a fused score.
    """
    try:
        import plotly.graph_objects as go
    except Exception:
        st.info("Install plotly to see the bridge diagram (already in deps).")
        return

    seg_ids = [s.segment_id for s in report.segments]
    theme_ids = [t.theme_id for t in report.themes]

    labels = (
        [f"{s.segment_id} · {s.name}" for s in report.segments]
        + [f"{t.theme_id} · {t.name}" for t in report.themes]
    )
    seg_idx = {sid: i for i, sid in enumerate(seg_ids)}
    theme_idx = {tid: i + len(seg_ids) for i, tid in enumerate(theme_ids)}

    sources, targets, values, hovers = [], [], [], []
    for c in report.correspondences:
        if c.segment_id not in seg_idx or c.theme_id not in theme_idx:
            continue
        sources.append(seg_idx[c.segment_id])
        targets.append(theme_idx[c.theme_id])
        # Discrete edge weight: number of evidence kinds (1, 2, or 3)
        values.append(len(c.evidence_kinds))
        kinds_str = ", ".join(c.evidence_kinds)
        hovers.append(f"{c.segment_id} ⇄ {c.theme_id}<br>Evidence kinds: {kinds_str}")

    if not sources:
        st.info("No correspondences to draw. Try lowering the minimum shared content terms.")
        return

    fig = go.Figure(
        data=[go.Sankey(
            arrangement="snap",
            node=dict(
                pad=14,
                thickness=14,
                line=dict(color="#cbd5e1", width=0.5),
                label=labels,
                color=["#185FA5"] * len(seg_ids) + ["#7F77DD"] * len(theme_ids),
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                customdata=hovers,
                hovertemplate="%{customdata}<extra></extra>",
                color="rgba(120,120,140,0.25)",
            ),
        )]
    )
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=20, b=10),
        font=dict(family="DM Sans, sans-serif", size=12, color="#222"),
        paper_bgcolor="#fafafa",
        annotations=[
            dict(
                text="Edge width = number of evidence kinds (1, 2, or 3) — not a confidence score.",
                showarrow=False, x=0.5, y=-0.08, xref="paper", yref="paper",
                font=dict(size=11, color="#777"),
            )
        ],
    )
    st.plotly_chart(fig, use_container_width=True)


def _inspection_panel(report: BridgeReport):
    if not report.correspondences:
        st.warning("No correspondences surfaced yet.")
        return

    seg_idx = {s.segment_id: s for s in report.segments}
    theme_idx = {t.theme_id: t for t in report.themes}

    options = [(c.segment_id, c.theme_id) for c in report.correspondences]
    labels = [
        f"{seg_idx[s].name} ⇄ {theme_idx[t].name}"
        if s in seg_idx and t in theme_idx else f"{s} ⇄ {t}"
        for s, t in options
    ]
    sel = st.selectbox("Inspect a correspondence", range(len(options)),
                       format_func=lambda i: labels[i], key="sel_corr")
    s_id, t_id = options[sel]
    corr = report.get_correspondence(s_id, t_id)
    seg = seg_idx.get(s_id)
    theme = theme_idx.get(t_id)
    enr = report.get_enrichment(s_id, t_id)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### Segment: {seg.name if seg else s_id}")
        if seg:
            st.markdown(f"<span class='mono'>{seg.segment_id}</span> · size: "
                        f"{seg.size if seg.size is not None else '—'}", unsafe_allow_html=True)
            st.write(seg.description or "_no description_")
            if seg.tags:
                st.markdown("**Tags**: " + ", ".join(f"`{t}`" for t in seg.tags))
    with col2:
        st.markdown(f"#### Theme: {theme.name if theme else t_id}")
        if theme:
            st.markdown(f"<span class='mono'>{theme.theme_id}</span>", unsafe_allow_html=True)
            st.write(theme.description or "_no description_")
            if theme.quotes:
                with st.expander(f"Sample quotes ({len(theme.quotes)})"):
                    for q in theme.quotes[:6]:
                        st.markdown(f"> {q}")

    st.markdown("#### Evidence")
    for e in corr.evidence:
        st.markdown(
            f"<span class='evidence-pill pill-"
            f"{ {'lexical_overlap':'lex','tag_match':'tag','shared_participants':'ppl'}[e.kind] }"
            f"'>{e.kind}</span> &nbsp;{e.detail}",
            unsafe_allow_html=True,
        )
        preview = ", ".join(f"`{x}`" for x in e.items[:12])
        if len(e.items) > 12:
            preview += f", +{len(e.items) - 12} more"
        st.markdown(preview)

    if enr and enr.backend != "none":
        st.markdown(f"#### Inspection notes  <span class='mono' style='color:#888;font-size:11px;'>· {enr.backend}</span>", unsafe_allow_html=True)
        if enr.rationale:
            st.info(enr.rationale)
        if enr.inspection_questions:
            st.markdown("**Questions to answer**")
            for q in enr.inspection_questions:
                st.markdown(f"- {q}")
        if enr.counter_evidence_prompts:
            st.markdown("**What would falsify this**")
            for c in enr.counter_evidence_prompts:
                st.markdown(f"- {c}")

    st.markdown("#### Researcher annotation")
    key = f"annot_{s_id}_{t_id}"
    annotation = st.radio(
        "Mark this correspondence",
        ["Unreviewed", "Mark for follow-up", "Likely spurious", "Verified via additional data"],
        key=key,
        horizontal=True,
    )
    note_key = f"note_{s_id}_{t_id}"
    st.text_area("Inspection note (your reasoning)", key=note_key)
    if annotation != "Unreviewed":
        st.caption(f"Last action: {annotation}")


# ---------- Main flow ----------
segments = _load_uploaded(seg_file, "segments")
themes = _load_uploaded(theme_file, "themes")

if segments is None or themes is None:
    st.info("Upload both a segments JSON and a themes JSON to begin.")
    with st.expander("Example input format"):
        st.code(
            """[
  {
    "segment_id": "S1",
    "name": "Power users",
    "description": "...",
    "tags": ["advanced", "engaged"],
    "member_ids": ["P1", "P2", "P7"]
  }
]""",
            language="json",
        )
    st.stop()

report = build_bridge(
    segments, themes,
    min_lexical_terms=min_lex,
    enrich=use_llm,
    backend=backend if use_llm else None,
    max_enrichments=int(max_enr),
)

st.markdown("### Bridge view")
_bridge_diagram(report)

st.markdown("### Inspect a correspondence")
_inspection_panel(report)

st.markdown("### Export")
col_a, col_b = st.columns(2)
with col_a:
    from .render import render_markdown
    st.download_button(
        "Download markdown report",
        render_markdown(report),
        file_name="quant_qual_bridge_report.md",
        mime="text/markdown",
    )
with col_b:
    from .render import render_json
    st.download_button(
        "Download JSON",
        render_json(report),
        file_name="quant_qual_bridge_report.json",
        mime="application/json",
    )
