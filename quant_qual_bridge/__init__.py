"""quant-qual-bridge: a discovery and visualisation tool for mixed methods.

Surfaces correspondences between quantitative segments and qualitative themes.
*Not* a triangulation engine — no fused confidence score is produced.
"""

from .bridge import build_bridge
from .loaders import load_segments, load_themes
from .matching import (
    find_correspondences,
    lexical_overlap,
    shared_participants,
    tag_match,
)
from .models import (
    BridgeReport,
    Correspondence,
    CorrespondenceEnrichment,
    EvidenceItem,
    QualTheme,
    QuantSegment,
)
from .render import render_json, render_markdown

__version__ = "0.1.0"

__all__ = [
    "BridgeReport",
    "Correspondence",
    "CorrespondenceEnrichment",
    "EvidenceItem",
    "QualTheme",
    "QuantSegment",
    "build_bridge",
    "find_correspondences",
    "lexical_overlap",
    "load_segments",
    "load_themes",
    "render_json",
    "render_markdown",
    "shared_participants",
    "tag_match",
]
