"""Tests for loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quant_qual_bridge.loaders import load_segments, load_themes

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_segments_from_fixture():
    segments = load_segments(FIXTURES / "segments.json")
    assert len(segments) == 4
    assert segments[0].segment_id == "S1"
    assert segments[0].name == "High-engagement power users"
    assert "advanced" in segments[0].tags
    assert "P1" in segments[0].member_ids


def test_load_themes_from_fixture():
    themes = load_themes(FIXTURES / "themes.json")
    assert len(themes) == 5
    assert themes[0].theme_id == "T1"
    assert any("power user" in q.lower() for q in themes[0].quotes)


def test_load_segments_accepts_segments_key(tmp_path):
    p = tmp_path / "wrapped.json"
    p.write_text(json.dumps({"segments": [{"segment_id": "X", "name": "X"}]}))
    segments = load_segments(p)
    assert segments[0].segment_id == "X"


def test_load_themes_accepts_themes_key(tmp_path):
    p = tmp_path / "wrapped.json"
    p.write_text(json.dumps({"themes": [{"theme_id": "T", "name": "T"}]}))
    themes = load_themes(p)
    assert themes[0].theme_id == "T"


def test_load_rejects_non_list(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"not_segments": []}))
    with pytest.raises(ValueError):
        load_segments(p)


def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_segments("/tmp/nonexistent_qqb_file.json")
