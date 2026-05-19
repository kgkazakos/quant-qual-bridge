# quant-qual-bridge

> **A discovery and visualisation tool. Not a triangulation engine.**

`quant-qual-bridge` surfaces *possible* correspondences between quantitative segments (clusters, persona groups, behavioural segments) and qualitative themes (interview synthesis, JTBD statements, journey-map phases) — and hands them to the researcher to inspect.

It does **not** produce a fused confidence score. It does **not** declare that a quant segment and a qual theme have been triangulated. It surfaces evidence of three distinct kinds and keeps them separate so the researcher can weigh them.

---

## The problem

Most mixed-methods analysis lives in a researcher's head. You finish a segmentation study, then finish a qualitative round, and somewhere on the whiteboard you start drawing lines: "*these power users from the cluster analysis sound a lot like the mastery-seekers from the interviews.*"

That linking is real work. It's also the moment where bias most easily creeps in: the segment that *feels* like the theme gets the connection; the segment that doesn't get a label gets forgotten. A tool that surfaces correspondences systematically is useful — *if* it stays honest about what it can and cannot do.

`quant-qual-bridge` is that tool. It is built around a single, deliberate constraint: **it never produces a unified score**. Every correspondence comes with its evidence broken out by kind, and the researcher decides what holds.

---

## What it does

**Surfaces correspondences across three independent evidence kinds:**
- **Lexical overlap** — shared content terms between segment descriptions and theme descriptions / quotes
- **Tag match** — shared tags from the researcher's own taxonomy
- **Shared participants** — when participant IDs link both corpora directly

**Visualises them** as a bipartite Sankey diagram where edge width is *discrete* — 1, 2, or 3 — reflecting how many evidence kinds support the link. Not a continuous score. Not a probability.

**Adds LLM inspection notes** (optional, on by default) — for each correspondence, the LLM produces:
- A short hypothesis stating why the link *might* hold
- Inspection questions for the researcher to answer
- Counter-evidence prompts that could falsify the link

**Lets the researcher annotate** — every correspondence gets a status: *unreviewed*, *follow-up*, *likely spurious*, *verified via additional data* — with a free-text reasoning note.

---

## What it deliberately is not

This tool can drift into **Multimodal Say-Do Triangulation** territory if you let it. To prevent that:

- The `Correspondence` dataclass has no `score`, `confidence`, or `strength` field. Tests assert this.
- The JSON export carries a top-level `_disclaimer` framing it as a discovery surface.
- The LLM prompt instructs the model to **never produce a numeric confidence**, and to frame the rationale as a hypothesis to test.
- The UI banner reads "What this is / what it is not" — visible on every screen.

If you want validated triangulation, you need additional research design (longitudinal data, behavioural confirmation, separate corroboration). This tool gives you the candidates worth doing that work for. It does not do that work itself.

---

## Install

```bash
pip install quant-qual-bridge
# with the Streamlit UI:
pip install "quant-qual-bridge[ui]"
# with LLM enrichment:
pip install "quant-qual-bridge[llm]"
# everything:
pip install "quant-qual-bridge[all]"
```

---

## Usage

### CLI

```bash
qqb bridge --segments segments.json --themes themes.json --out report.md
```

Optional flags:

| Flag | Default | Notes |
|---|---|---|
| `--min-lexical-terms` | `2` | Lower for more candidates, higher for tighter results |
| `--no-llm` | off | Disable LLM enrichment entirely |
| `--llm-backend` | `anthropic/claude-opus-4-7` | Or `gemini/gemini-3.1-pro`, `openai/gpt-5.5` |
| `--max-enrichments` | `30` | Cap on enrichment calls (cost guardrail) |
| `--json-output` | off | Emit JSON to stdout for downstream pipelines |

### Python

```python
from quant_qual_bridge import load_segments, load_themes, build_bridge, render_markdown

segments = load_segments("segments.json")
themes = load_themes("themes.json")
report = build_bridge(segments, themes, enrich=True)
print(render_markdown(report))
```

### UI

```bash
qqb ui
```

Then open `http://localhost:8501`.

---

## Input format

**Segments** (JSON list, or `{"segments": [...]}`):

```json
[
  {
    "segment_id": "S1",
    "name": "High-engagement power users",
    "description": "Users who log in 5+ days per week and use advanced features.",
    "size": 412,
    "tags": ["advanced", "engaged"],
    "member_ids": ["P1", "P2", "P7"]
  }
]
```

**Themes** (JSON list, or `{"themes": [...]}`):

```json
[
  {
    "theme_id": "T1",
    "name": "Mastery-seeking behaviour",
    "description": "Participants describe wanting to feel expert and capable.",
    "quotes": ["I want to know I'm using this thing properly."],
    "tags": ["expertise", "advanced"],
    "participant_ids": ["P1", "P7", "P19"]
  }
]
```

`member_ids` and `participant_ids` are optional but enable the strongest evidence kind — direct participant overlap. If you can carry IDs through both studies, do.

---

## LLM backends

Three supported, opt-out (LLM enrichment is on by default):

| Backend | Env var |
|---|---|
| `anthropic/claude-opus-4-7` (default) | `ANTHROPIC_API_KEY` |
| `gemini/gemini-3.1-pro` | `GEMINI_API_KEY` |
| `openai/gpt-5.5` | `OPENAI_API_KEY` |

If no API key is present, the pipeline degrades silently: each enrichment records `backend: "none"` and the rule-based output stands on its own.

---

## Part of the CPR Ecosystem

`quant-qual-bridge` is the 29th tool in the **CPR Orbital Series** — 40 open-source tools shipping at an almost daily cadence through December 2026, all sitting under the broader **Computational Product Research** discipline.

Closest relatives in the series:

- [`max-diff-analyzer`](https://github.com/kgkazakos/max-diff-analyzer) — preference scoring for surveys, the kind of quant output that feeds this bridge
- [`segment-finder`](https://github.com/kgkazakos/segment-finder) — behavioural segmentation that produces segments
- [`saturation-meter`](https://github.com/kgkazakos/saturation-meter) — qualitative saturation, the kind of qual synthesis that produces themes
- [`evidence-chain`](https://github.com/kgkazakos/evidence-chain) — tracking claim-to-evidence provenance through layered reports

This tool stays a *bridge*, not a triangulator, because triangulation is a separate concern handled by **CausalTrack** — a research-grade Multimodal Say-Do Gap detection system that lives outside the orbital series.

---

## License

MIT
