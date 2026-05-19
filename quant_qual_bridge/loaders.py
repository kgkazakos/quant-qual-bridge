"""Loaders for quant segments and qual themes.

Supports JSON input. Both inputs are intentionally loose-schema — researchers
often hand-curate these files and we want to be forgiving.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import QualTheme, QuantSegment


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def load_segments(path: str | Path) -> list[QuantSegment]:
    """Load quantitative segments from a JSON file.

    Expected shape (top-level list or object with "segments" key):

        [
          {
            "segment_id": "S1",
            "name": "Power users",
            "description": "...",
            "size": 412,
            "attributes": {...},
            "tags": ["advanced", "engaged"],
            "member_ids": ["P1", "P2", ...]
          },
          ...
        ]
    """
    raw = _read_json(path)
    items = raw["segments"] if isinstance(raw, dict) and "segments" in raw else raw
    if not isinstance(items, list):
        raise ValueError("Segment file must contain a list or a 'segments' key with a list.")

    segments: list[QuantSegment] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Segment entry #{i} is not an object.")
        segments.append(
            QuantSegment(
                segment_id=str(item.get("segment_id") or item.get("id") or f"S{i + 1}"),
                name=str(item.get("name") or item.get("segment_id") or f"Segment {i + 1}"),
                description=str(item.get("description", "")),
                size=item.get("size"),
                attributes=item.get("attributes") or {},
                tags=_coerce_list(item.get("tags")),
                member_ids=_coerce_list(item.get("member_ids") or item.get("members")),
            )
        )
    return segments


def load_themes(path: str | Path) -> list[QualTheme]:
    """Load qualitative themes from a JSON file.

    Expected shape (top-level list or object with "themes" key):

        [
          {
            "theme_id": "T1",
            "name": "Mastery-seeking behaviour",
            "description": "...",
            "quotes": ["...", "..."],
            "tags": ["expertise"],
            "participant_ids": ["P1", "P7"]
          },
          ...
        ]
    """
    raw = _read_json(path)
    items = raw["themes"] if isinstance(raw, dict) and "themes" in raw else raw
    if not isinstance(items, list):
        raise ValueError("Theme file must contain a list or a 'themes' key with a list.")

    themes: list[QualTheme] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Theme entry #{i} is not an object.")
        themes.append(
            QualTheme(
                theme_id=str(item.get("theme_id") or item.get("id") or f"T{i + 1}"),
                name=str(item.get("name") or item.get("theme_id") or f"Theme {i + 1}"),
                description=str(item.get("description", "")),
                quotes=_coerce_list(item.get("quotes")),
                tags=_coerce_list(item.get("tags")),
                participant_ids=_coerce_list(item.get("participant_ids") or item.get("participants")),
            )
        )
    return themes


def _read_json(path: str | Path) -> Any:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)
