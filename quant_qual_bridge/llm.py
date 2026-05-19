"""Optional LLM enrichment for quant-qual-bridge.

DESIGN PRINCIPLE: The LLM is asked for *narrative* — a short rationale plus
inspection and counter-evidence prompts. The schema deliberately excludes
any numeric confidence, likelihood, or "match strength" field.

If the model attempts to inject one (e.g. saying "0.85 confidence" in the
rationale), it is the researcher's responsibility to disregard it; downstream
consumers of this tool's JSON never see a fused score.

This module is excluded from CI (no API keys in CI environment).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Any

from .models import (
    Correspondence,
    CorrespondenceEnrichment,
    QualTheme,
    QuantSegment,
)

# LLM is on by default. These three backends are supported.
DEFAULT_BACKEND = "anthropic/claude-opus-4-7"
SUPPORTED_BACKENDS = (
    "anthropic/claude-opus-4-7",
    "gemini/gemini-3.1-pro",
    "openai/gpt-5.5",
)


SYSTEM_PROMPT = """\
You are a methodological co-pilot for a UX researcher inspecting a possible
correspondence between a quantitative segment and a qualitative theme.

Your job is to help the researcher *inspect* this possible correspondence —
NOT to certify it, score it, or declare it valid.

Rules you MUST follow:
- Never produce a confidence score, probability, percentage, or any numeric
  judgement of how strongly the segment and theme correspond.
- Never claim the correspondence is "verified", "triangulated", "confirmed",
  or "true". The researcher decides that.
- Frame the rationale as a hypothesis the researcher should test.
- Always supply counter-evidence prompts that could falsify the hypothesis.

Output a single JSON object with these fields:
{
  "rationale": "1-3 sentences. Why might this segment and theme relate? Be specific. Avoid certainty language.",
  "inspection_questions": ["3-5 short questions the researcher should answer to decide if this correspondence holds."],
  "counter_evidence_prompts": ["2-4 short prompts describing what would falsify or weaken this correspondence."]
}

No other fields. No scores. No preamble. Pure JSON.
"""


def _build_user_prompt(
    seg: QuantSegment, theme: QualTheme, corr: Correspondence
) -> str:
    evidence_lines = []
    for e in corr.evidence:
        items_preview = ", ".join(e.items[:8])
        if len(e.items) > 8:
            items_preview += f", ... (+{len(e.items) - 8} more)"
        evidence_lines.append(f"- {e.kind}: {e.detail} — [{items_preview}]")
    evidence_block = "\n".join(evidence_lines) if evidence_lines else "(none)"

    quotes_preview = "\n".join(f"  • {q}" for q in theme.quotes[:3]) if theme.quotes else "  (no quotes provided)"

    return f"""\
QUANTITATIVE SEGMENT
  ID: {seg.segment_id}
  Name: {seg.name}
  Size: {seg.size if seg.size is not None else "unknown"}
  Description: {seg.description}
  Tags: {", ".join(seg.tags) if seg.tags else "(none)"}

QUALITATIVE THEME
  ID: {theme.theme_id}
  Name: {theme.name}
  Description: {theme.description}
  Tags: {", ".join(theme.tags) if theme.tags else "(none)"}
  Sample quotes:
{quotes_preview}

EVIDENCE SURFACED BY THE TOOL
{evidence_block}

Now produce the JSON object as specified.
"""


def enrich_correspondence(
    seg: QuantSegment,
    theme: QualTheme,
    corr: Correspondence,
    backend: str = DEFAULT_BACKEND,
) -> CorrespondenceEnrichment:
    """Call the chosen LLM backend via LiteLLM and return an enrichment.

    On any error (missing API key, network, parse failure), returns an
    enrichment with empty fields and the backend recorded as "none" so the
    surrounding pipeline degrades gracefully.
    """
    try:
        import litellm  # noqa: WPS433
    except Exception:
        return CorrespondenceEnrichment(backend="none")

    if backend not in SUPPORTED_BACKENDS:
        return CorrespondenceEnrichment(backend="none")

    if not _has_api_key_for(backend):
        return CorrespondenceEnrichment(backend="none")

    user_prompt = _build_user_prompt(seg, theme, corr)

    try:
        resp = litellm.completion(
            model=backend,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=600,
        )
        raw = resp["choices"][0]["message"]["content"]
        data = _parse_json_payload(raw)
    except Exception:
        return CorrespondenceEnrichment(backend="none")

    return CorrespondenceEnrichment(
        rationale=str(data.get("rationale", "")).strip(),
        inspection_questions=[str(q) for q in (data.get("inspection_questions") or [])][:5],
        counter_evidence_prompts=[str(q) for q in (data.get("counter_evidence_prompts") or [])][:4],
        backend=backend,
    )


def _has_api_key_for(backend: str) -> bool:
    if backend.startswith("anthropic/"):
        return bool(os.getenv("ANTHROPIC_API_KEY"))
    if backend.startswith("openai/"):
        return bool(os.getenv("OPENAI_API_KEY"))
    if backend.startswith("gemini/"):
        return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    return False


def _parse_json_payload(raw: str) -> dict[str, Any]:
    """Tolerant parse — strips markdown fences if present."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # remove leading "json" language tag if present
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


def enrichment_to_dict(e: CorrespondenceEnrichment) -> dict[str, Any]:
    """Serialise enrichment for JSON export — note: no score field by design."""
    return asdict(e)
