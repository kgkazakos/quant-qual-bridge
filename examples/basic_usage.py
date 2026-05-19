"""Basic usage example for quant-qual-bridge.

Run from the repo root:

    python examples/basic_usage.py
"""

from __future__ import annotations

from pathlib import Path

from quant_qual_bridge.bridge import build_bridge
from quant_qual_bridge.loaders import load_segments, load_themes
from quant_qual_bridge.render import render_markdown

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def main() -> None:
    segments = load_segments(FIXTURES / "segments.json")
    themes = load_themes(FIXTURES / "themes.json")

    # By default, LLM enrichment is ON. With no API key set it degrades silently
    # to rule-based output. Pass enrich=False to skip the LLM layer entirely.
    report = build_bridge(segments, themes, min_lexical_terms=1, enrich=False)

    print(f"Surfaced {len(report.correspondences)} correspondences for inspection.\n")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
