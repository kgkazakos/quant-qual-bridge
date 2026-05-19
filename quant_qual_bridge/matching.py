"""Matching engine: surfaces possible correspondences between quant segments and qual themes.

DESIGN PRINCIPLE: This module never returns a unified score. It returns
*evidence items*, each of which is its own kind (lexical, tag, participant).
The researcher inspects evidence; the tool does not weigh it.
"""

from __future__ import annotations

import re
from typing import Iterable

from .models import Correspondence, EvidenceItem, QualTheme, QuantSegment

# A short, deliberately small stopword list. We bias toward keeping content terms.
_STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are aren as at
    be because been before being below between both but by can cannot could
    did do does doing down during each few for from further had has have
    having he her here hers herself him himself his how i if in into is it
    its itself just like me more most my myself no nor not now of off on
    once only or other ought our ours ourselves out over own same she should
    so some such than that the their theirs them themselves then there these
    they this those through to too under until up very was we were what when
    where which while who whom why will with would you your yours yourself
    yourselves users user use using one two three really lot lots much many
    things thing make made got get gets getting also even though although
    however still really kind sort feel feels felt
    """.split()
)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def _keywords(text: str, min_len: int = 4) -> set[str]:
    return {
        t for t in _tokens(text)
        if t not in _STOPWORDS and len(t) >= min_len
    }


def _segment_keywords(seg: QuantSegment) -> set[str]:
    text = " ".join([seg.name, seg.description, " ".join(seg.tags)])
    kw = _keywords(text)
    # Tags are intentionally included as keywords too — they survive even short
    kw.update({t.lower() for t in seg.tags if t})
    return kw


def _theme_keywords(theme: QualTheme, include_quotes: bool = True) -> set[str]:
    parts = [theme.name, theme.description, " ".join(theme.tags)]
    if include_quotes:
        parts.extend(theme.quotes)
    kw = _keywords(" ".join(parts))
    kw.update({t.lower() for t in theme.tags if t})
    return kw


def lexical_overlap(seg: QuantSegment, theme: QualTheme, min_terms: int = 1) -> EvidenceItem | None:
    shared = sorted(_segment_keywords(seg) & _theme_keywords(theme))
    if len(shared) < min_terms:
        return None
    n = len(shared)
    return EvidenceItem(
        kind="lexical_overlap",
        detail=f"{n} shared content term{'s' if n != 1 else ''}",
        items=shared,
    )


def tag_match(seg: QuantSegment, theme: QualTheme) -> EvidenceItem | None:
    s_tags = {t.lower() for t in seg.tags}
    t_tags = {t.lower() for t in theme.tags}
    shared = sorted(s_tags & t_tags)
    if not shared:
        return None
    n = len(shared)
    return EvidenceItem(
        kind="tag_match",
        detail=f"{n} shared tag{'s' if n != 1 else ''}",
        items=shared,
    )


def shared_participants(seg: QuantSegment, theme: QualTheme) -> EvidenceItem | None:
    s_p = set(seg.member_ids)
    t_p = set(theme.participant_ids)
    shared = sorted(s_p & t_p)
    if not shared:
        return None
    n = len(shared)
    return EvidenceItem(
        kind="shared_participants",
        detail=f"{n} participant{'s' if n != 1 else ''} appear in both",
        items=shared,
    )


def find_correspondences(
    segments: Iterable[QuantSegment],
    themes: Iterable[QualTheme],
    *,
    min_lexical_terms: int = 2,
) -> list[Correspondence]:
    """Return all (segment, theme) pairs that show at least one evidence kind.

    Note: the result is *not* sorted by any unified score. Sorting and
    weighting is left to the researcher and the UI layer.
    """
    out: list[Correspondence] = []
    seg_list = list(segments)
    theme_list = list(themes)

    for seg in seg_list:
        for theme in theme_list:
            evidence: list[EvidenceItem] = []
            lex = lexical_overlap(seg, theme, min_terms=min_lexical_terms)
            if lex is not None:
                evidence.append(lex)
            tag = tag_match(seg, theme)
            if tag is not None:
                evidence.append(tag)
            ppl = shared_participants(seg, theme)
            if ppl is not None:
                evidence.append(ppl)
            if evidence:
                out.append(
                    Correspondence(
                        segment_id=seg.segment_id,
                        theme_id=theme.theme_id,
                        evidence=evidence,
                    )
                )
    return out
