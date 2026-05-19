"""Tests for the matching engine."""

from __future__ import annotations

from pathlib import Path

from quant_qual_bridge.loaders import load_segments, load_themes
from quant_qual_bridge.matching import (
    find_correspondences,
    lexical_overlap,
    shared_participants,
    tag_match,
)
from quant_qual_bridge.models import QualTheme, QuantSegment

FIXTURES = Path(__file__).parent / "fixtures"


def test_lexical_overlap_finds_shared_terms():
    seg = QuantSegment(
        segment_id="S1",
        name="Power users",
        description="Users who use advanced customisation features.",
        tags=["advanced"],
    )
    theme = QualTheme(
        theme_id="T1",
        name="Mastery-seeking",
        description="Participants want to use advanced features and master customisation.",
        tags=["advanced"],
    )
    ev = lexical_overlap(seg, theme, min_terms=1)
    assert ev is not None
    assert ev.kind == "lexical_overlap"
    assert "advanced" in ev.items


def test_lexical_overlap_below_threshold_returns_none():
    seg = QuantSegment(segment_id="S1", name="Apple", description="Apple sauce recipe details.")
    theme = QualTheme(theme_id="T1", name="Banana", description="Banana smoothie texture concerns.")
    assert lexical_overlap(seg, theme, min_terms=2) is None


def test_tag_match_intersects_tags():
    seg = QuantSegment(segment_id="S1", name="A", tags=["admin", "billing"])
    theme = QualTheme(theme_id="T1", name="B", tags=["billing", "permissions"])
    ev = tag_match(seg, theme)
    assert ev is not None
    assert ev.items == ["billing"]


def test_tag_match_empty_returns_none():
    seg = QuantSegment(segment_id="S1", name="A", tags=["x"])
    theme = QualTheme(theme_id="T1", name="B", tags=["y"])
    assert tag_match(seg, theme) is None


def test_shared_participants():
    seg = QuantSegment(segment_id="S1", name="A", member_ids=["P1", "P2", "P3"])
    theme = QualTheme(theme_id="T1", name="B", participant_ids=["P2", "P4"])
    ev = shared_participants(seg, theme)
    assert ev is not None
    assert ev.items == ["P2"]


def test_shared_participants_none():
    seg = QuantSegment(segment_id="S1", name="A", member_ids=["P1"])
    theme = QualTheme(theme_id="T1", name="B", participant_ids=["P2"])
    assert shared_participants(seg, theme) is None


def test_find_correspondences_on_fixtures():
    segments = load_segments(FIXTURES / "segments.json")
    themes = load_themes(FIXTURES / "themes.json")
    correspondences = find_correspondences(segments, themes, min_lexical_terms=1)

    # We expect at least the strong mappings:
    pairs = {(c.segment_id, c.theme_id) for c in correspondences}
    assert ("S1", "T1") in pairs  # power users <-> mastery
    assert ("S2", "T2") in pairs  # onboarding stallers <-> setup friction
    assert ("S4", "T3") in pairs  # admins <-> permissions anxiety
    assert ("S3", "T4") in pairs  # weekenders <-> time-of-week identity


def test_correspondence_has_no_score_field():
    """Critical design check: Correspondence intentionally exposes no score."""
    seg = QuantSegment(
        segment_id="S1", name="Alpha", description="advanced customisation power",
    )
    theme = QualTheme(
        theme_id="T1", name="Beta", description="advanced customisation power workflow",
    )
    [c] = find_correspondences([seg], [theme], min_lexical_terms=1)
    # The Correspondence dataclass must not have a 'score' or 'confidence' attribute.
    assert not hasattr(c, "score"), "Correspondence must not expose a unified score."
    assert not hasattr(c, "confidence"), "Correspondence must not expose a confidence value."


def test_evidence_kinds_are_distinct():
    seg = QuantSegment(
        segment_id="S1", name="Alpha", description="advanced customisation workflow",
        tags=["shared-tag"], member_ids=["P1", "P2"],
    )
    theme = QualTheme(
        theme_id="T1", name="Beta", description="advanced customisation patterns",
        tags=["shared-tag"], participant_ids=["P1"],
    )
    [c] = find_correspondences([seg], [theme], min_lexical_terms=1)
    kinds = set(c.evidence_kinds)
    assert kinds == {"lexical_overlap", "tag_match", "shared_participants"}
