"""Core data models for quant-qual-bridge.

DESIGN PRINCIPLE: This module deliberately avoids a unified
"correspondence score" or "triangulation confidence" field.

A Correspondence holds a list of EvidenceItem objects of *distinct kinds*
(lexical overlap, tag match, shared participants). It is the researcher's
job to weigh that evidence — not the tool's. This is the boundary that
keeps quant-qual-bridge a discovery surface rather than an automated
triangulation engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Tuple


@dataclass
class QuantSegment:
    """A segment derived from quantitative analysis (cluster, persona group, etc.)."""

    segment_id: str
    name: str
    description: str = ""
    size: int | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    member_ids: list[str] = field(default_factory=list)


@dataclass
class QualTheme:
    """A theme derived from qualitative synthesis (interview themes, JTBD, etc.)."""

    theme_id: str
    name: str
    description: str = ""
    quotes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    participant_ids: list[str] = field(default_factory=list)


@dataclass
class EvidenceItem:
    """A single piece of evidence that could support a correspondence.

    Each EvidenceItem is its own *kind*; the researcher sees evidence types
    separately rather than as a single fused score.
    """

    kind: str  # "lexical_overlap" | "tag_match" | "shared_participants"
    detail: str
    items: list[str] = field(default_factory=list)


@dataclass
class Correspondence:
    """A surfaced possible link between a quant segment and a qual theme.

    Notably absent: a unified `score` or `confidence` field. A Correspondence
    is a *candidate for inspection*, not a verified linkage.
    """

    segment_id: str
    theme_id: str
    evidence: list[EvidenceItem] = field(default_factory=list)

    @property
    def evidence_kinds(self) -> list[str]:
        """Kinds of evidence present, in stable order — used for filtering, not weighting."""
        order = ["lexical_overlap", "tag_match", "shared_participants"]
        present = {e.kind for e in self.evidence}
        return [k for k in order if k in present]


@dataclass
class CorrespondenceEnrichment:
    """LLM-generated narrative for a single correspondence.

    Explicitly does not include a score. Only:
      - a short rationale describing why the correspondence might hold
      - inspection questions the researcher should answer
      - counter-evidence prompts that could falsify it
    """

    rationale: str = ""
    inspection_questions: list[str] = field(default_factory=list)
    counter_evidence_prompts: list[str] = field(default_factory=list)
    backend: str = "none"


@dataclass
class BridgeReport:
    """A full quant-qual-bridge output."""

    segments: list[QuantSegment] = field(default_factory=list)
    themes: list[QualTheme] = field(default_factory=list)
    correspondences: list[Correspondence] = field(default_factory=list)
    enrichments: dict[Tuple[str, str], CorrespondenceEnrichment] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_correspondence(self, segment_id: str, theme_id: str) -> Correspondence | None:
        for c in self.correspondences:
            if c.segment_id == segment_id and c.theme_id == theme_id:
                return c
        return None

    def get_enrichment(self, segment_id: str, theme_id: str) -> CorrespondenceEnrichment | None:
        return self.enrichments.get((segment_id, theme_id))
