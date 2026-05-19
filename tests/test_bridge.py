"""Tests for orchestrator and rendering."""

from __future__ import annotations

import json
from pathlib import Path

from quant_qual_bridge.bridge import build_bridge
from quant_qual_bridge.loaders import load_segments, load_themes
from quant_qual_bridge.render import render_json, render_markdown

FIXTURES = Path(__file__).parent / "fixtures"


def test_build_bridge_without_llm():
    segments = load_segments(FIXTURES / "segments.json")
    themes = load_themes(FIXTURES / "themes.json")
    report = build_bridge(segments, themes, min_lexical_terms=1, enrich=False)
    assert len(report.correspondences) > 0
    assert len(report.enrichments) == 0
    assert report.metadata["enrichment_requested"] is False


def test_build_bridge_with_llm_no_key_returns_graceful_empty():
    """With LLM enabled but no API keys present, pipeline should not crash."""
    segments = load_segments(FIXTURES / "segments.json")
    themes = load_themes(FIXTURES / "themes.json")
    report = build_bridge(segments, themes, min_lexical_terms=1, enrich=True)
    # All enrichments should have backend "none" since CI has no API keys
    for k, v in report.enrichments.items():
        assert v.backend == "none"


def test_render_markdown_includes_discovery_framing():
    segments = load_segments(FIXTURES / "segments.json")
    themes = load_themes(FIXTURES / "themes.json")
    report = build_bridge(segments, themes, min_lexical_terms=1, enrich=False)
    md = render_markdown(report)
    assert "What this is / what it is not" in md
    assert "triangulation engine" in md
    assert "no fused" in md.lower()


def test_render_json_contains_disclaimer_and_no_score_field():
    segments = load_segments(FIXTURES / "segments.json")
    themes = load_themes(FIXTURES / "themes.json")
    report = build_bridge(segments, themes, min_lexical_terms=1, enrich=False)
    payload = json.loads(render_json(report))
    assert "_disclaimer" in payload
    # No correspondence should have a "score" or "confidence" field.
    for c in payload["correspondences"]:
        assert "score" not in c
        assert "confidence" not in c


def test_render_markdown_empty_corpus():
    report = build_bridge([], [], enrich=False)
    md = render_markdown(report)
    assert "Segments:" in md
    assert "0" in md


def test_metadata_includes_counts():
    segments = load_segments(FIXTURES / "segments.json")
    themes = load_themes(FIXTURES / "themes.json")
    report = build_bridge(segments, themes, min_lexical_terms=1, enrich=False)
    assert report.metadata["n_segments"] == 4
    assert report.metadata["n_themes"] == 5
    assert report.metadata["n_correspondences"] == len(report.correspondences)
