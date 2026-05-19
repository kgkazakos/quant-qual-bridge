"""Rendering: markdown summary and JSON export.

The output formats are designed to make the discovery framing visible — the
markdown report opens with a "What this is / What it is not" preamble, and
the JSON export contains a top-level disclaimer field.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .models import BridgeReport, Correspondence

PREAMBLE = (
    "Quant-Qual Bridge surfaces *possible* correspondences between "
    "quantitative segments and qualitative themes. Each correspondence is "
    "a candidate for the researcher to inspect, not a verified linkage. "
    "No unified score is produced; evidence kinds are kept separate by design."
)


def render_markdown(report: BridgeReport) -> str:
    md: list[str] = []
    md.append("# Quant–Qual Bridge — Discovery Report")
    md.append("")
    md.append("> " + PREAMBLE)
    md.append("")

    md.append("## What this is / what it is not")
    md.append("")
    md.append("**What it is**: A discovery surface. Each row below is a possible "
              "correspondence the researcher should review.")
    md.append("")
    md.append("**What it is not**: A triangulation engine. There is no fused "
              "confidence score. Edge counts are descriptive, not predictive.")
    md.append("")

    md.append("## Inputs")
    md.append("")
    md.append(f"- Segments: **{len(report.segments)}**")
    md.append(f"- Themes: **{len(report.themes)}**")
    md.append(f"- Correspondences surfaced: **{len(report.correspondences)}**")
    md.append("")

    if not report.correspondences:
        md.append("_No correspondences surfaced. Try lowering `min_lexical_terms`, "
                  "verifying tag conventions across both sides, or adding "
                  "participant IDs that link the two corpora._")
        md.append("")
        return "\n".join(md)

    md.append("## Correspondences to inspect")
    md.append("")
    seg_idx = {s.segment_id: s for s in report.segments}
    theme_idx = {t.theme_id: t for t in report.themes}

    # Stable display order: by segment_id, then theme_id
    ordered = sorted(
        report.correspondences, key=lambda c: (c.segment_id, c.theme_id)
    )

    for corr in ordered:
        seg = seg_idx.get(corr.segment_id)
        theme = theme_idx.get(corr.theme_id)
        seg_name = seg.name if seg else corr.segment_id
        theme_name = theme.name if theme else corr.theme_id
        md.append(f"### {corr.segment_id} ⇄ {corr.theme_id}")
        md.append("")
        md.append(f"**Segment**: {seg_name}  ")
        md.append(f"**Theme**: {theme_name}")
        md.append("")
        md.append("Evidence:")
        for e in corr.evidence:
            preview = ", ".join(f"`{x}`" for x in e.items[:8])
            if len(e.items) > 8:
                preview += f", +{len(e.items) - 8} more"
            md.append(f"- _{e.kind}_ — {e.detail}: {preview}")
        md.append("")

        enr = report.get_enrichment(corr.segment_id, corr.theme_id)
        if enr and enr.backend != "none":
            md.append(f"**Inspection notes** (via `{enr.backend}`):")
            md.append("")
            if enr.rationale:
                md.append(f"_Hypothesis_: {enr.rationale}")
                md.append("")
            if enr.inspection_questions:
                md.append("_Questions to answer_:")
                for q in enr.inspection_questions:
                    md.append(f"- {q}")
                md.append("")
            if enr.counter_evidence_prompts:
                md.append("_What would falsify this_:")
                for c in enr.counter_evidence_prompts:
                    md.append(f"- {c}")
                md.append("")
        md.append("---")
        md.append("")

    return "\n".join(md)


def render_json(report: BridgeReport) -> str:
    payload: dict[str, Any] = {
        "_disclaimer": PREAMBLE,
        "metadata": report.metadata,
        "segments": [asdict(s) for s in report.segments],
        "themes": [asdict(t) for t in report.themes],
        "correspondences": [_correspondence_to_dict(c) for c in report.correspondences],
        "enrichments": [
            {
                "segment_id": k[0],
                "theme_id": k[1],
                **asdict(v),
            }
            for k, v in report.enrichments.items()
        ],
    }
    return json.dumps(payload, indent=2)


def _correspondence_to_dict(c: Correspondence) -> dict[str, Any]:
    return {
        "segment_id": c.segment_id,
        "theme_id": c.theme_id,
        "evidence": [asdict(e) for e in c.evidence],
        "evidence_kinds": c.evidence_kinds,
        # Note: deliberately no "score" field.
    }
