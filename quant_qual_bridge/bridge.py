"""High-level orchestrator for quant-qual-bridge."""

from __future__ import annotations

from typing import Iterable

from .matching import find_correspondences
from .models import (
    BridgeReport,
    Correspondence,
    QualTheme,
    QuantSegment,
)


def build_bridge(
    segments: Iterable[QuantSegment],
    themes: Iterable[QualTheme],
    *,
    min_lexical_terms: int = 2,
    enrich: bool = True,
    backend: str | None = None,
    max_enrichments: int = 30,
) -> BridgeReport:
    """Run the full pipeline: surface correspondences, optionally enrich.

    Parameters
    ----------
    segments, themes
        Iterables of QuantSegment and QualTheme.
    min_lexical_terms
        Minimum number of shared content terms for lexical_overlap to register.
    enrich
        Whether to invoke the LLM enrichment layer. Default True (on by default).
    backend
        LiteLLM-format backend string. None means use the default from llm.py.
    max_enrichments
        Cap on number of enrichments to request — protects against runaway costs.
        Correspondences beyond the cap are still returned, just without rationale.
    """
    seg_list = list(segments)
    theme_list = list(themes)
    correspondences: list[Correspondence] = find_correspondences(
        seg_list, theme_list, min_lexical_terms=min_lexical_terms
    )

    report = BridgeReport(
        segments=seg_list,
        themes=theme_list,
        correspondences=correspondences,
        metadata={
            "min_lexical_terms": min_lexical_terms,
            "enrichment_requested": bool(enrich),
            "backend_requested": backend,
            "n_segments": len(seg_list),
            "n_themes": len(theme_list),
            "n_correspondences": len(correspondences),
        },
    )

    if not enrich or not correspondences:
        return report

    from .llm import DEFAULT_BACKEND, enrich_correspondence  # late import

    chosen = backend or DEFAULT_BACKEND
    seg_index = {s.segment_id: s for s in seg_list}
    theme_index = {t.theme_id: t for t in theme_list}

    # Order correspondences by number of evidence kinds so the most multi-faceted
    # ones get enriched first within the cap. This is a *prioritisation* signal,
    # not a quality score.
    ordered = sorted(
        correspondences,
        key=lambda c: (-len(c.evidence_kinds), -sum(len(e.items) for e in c.evidence)),
    )

    for corr in ordered[:max_enrichments]:
        seg = seg_index.get(corr.segment_id)
        theme = theme_index.get(corr.theme_id)
        if seg is None or theme is None:
            continue
        enrichment = enrich_correspondence(seg, theme, corr, backend=chosen)
        report.enrichments[(corr.segment_id, corr.theme_id)] = enrichment

    report.metadata["backend_used"] = chosen
    return report
