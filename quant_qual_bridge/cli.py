"""Command-line interface for quant-qual-bridge."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .bridge import build_bridge
from .loaders import load_segments, load_themes
from .render import PREAMBLE, render_json, render_markdown

console = Console()

SUPPORTED_BACKENDS = (
    "anthropic/claude-opus-4-7",
    "gemini/gemini-3.1-pro",
    "openai/gpt-5.5",
)


@click.group()
@click.version_option()
def main() -> None:
    """Quant–Qual Bridge — surface correspondences between quant segments and qual themes.

    A discovery and visualisation tool. Not a triangulation engine.
    """


@main.command()
@click.option(
    "--segments", "segments_path", required=True, type=click.Path(exists=True, dir_okay=False),
    help="Path to JSON file containing quantitative segments.",
)
@click.option(
    "--themes", "themes_path", required=True, type=click.Path(exists=True, dir_okay=False),
    help="Path to JSON file containing qualitative themes.",
)
@click.option(
    "--out", "out_path", type=click.Path(dir_okay=False),
    help="Optional path to write the markdown report.",
)
@click.option(
    "--json-output", "json_output", is_flag=True,
    help="Emit JSON to stdout (CI / pipeline friendly).",
)
@click.option(
    "--min-lexical-terms", type=int, default=2, show_default=True,
    help="Minimum shared content terms for a lexical_overlap evidence item.",
)
@click.option(
    "--no-llm", is_flag=True,
    help="Disable the LLM enrichment layer (rule-based only).",
)
@click.option(
    "--llm-backend", type=click.Choice(SUPPORTED_BACKENDS), default=None,
    help="Override the default LLM backend.",
)
@click.option(
    "--max-enrichments", type=int, default=30, show_default=True,
    help="Cap on number of correspondences to enrich.",
)
def bridge(
    segments_path: str,
    themes_path: str,
    out_path: str | None,
    json_output: bool,
    min_lexical_terms: int,
    no_llm: bool,
    llm_backend: str | None,
    max_enrichments: int,
) -> None:
    """Run the bridge: surface correspondences between segments and themes."""
    segments = load_segments(segments_path)
    themes = load_themes(themes_path)

    report = build_bridge(
        segments,
        themes,
        min_lexical_terms=min_lexical_terms,
        enrich=not no_llm,
        backend=llm_backend,
        max_enrichments=max_enrichments,
    )

    if json_output:
        click.echo(render_json(report))
        return

    _print_terminal_summary(report)

    md = render_markdown(report)
    if out_path:
        Path(out_path).write_text(md, encoding="utf-8")
        console.print(f"\n[green]Markdown report written to[/green] {out_path}")
    else:
        console.print()
        console.print(Panel.fit(
            "Use --out <path>.md to save the full markdown report,\n"
            "or --json-output to emit JSON for downstream pipelines.",
            border_style="dim",
        ))


def _print_terminal_summary(report) -> None:
    console.print()
    console.print(Panel.fit(
        f"[bold]Quant–Qual Bridge[/bold]\n[dim]{PREAMBLE}[/dim]",
        border_style="cyan",
    ))
    console.print()

    summary = Table(title="Run summary", show_header=False, expand=False)
    summary.add_row("Segments", str(len(report.segments)))
    summary.add_row("Themes", str(len(report.themes)))
    summary.add_row("Correspondences", str(len(report.correspondences)))
    summary.add_row("Enrichments", str(len(report.enrichments)))
    if report.metadata.get("backend_used"):
        summary.add_row("LLM backend", report.metadata["backend_used"])
    console.print(summary)

    if not report.correspondences:
        console.print("\n[yellow]No correspondences surfaced.[/yellow]")
        return

    console.print()
    table = Table(title="Surfaced correspondences (inspect each)", show_lines=False)
    table.add_column("Segment", style="cyan", no_wrap=False)
    table.add_column("Theme", style="magenta", no_wrap=False)
    table.add_column("Evidence kinds", style="white")

    seg_idx = {s.segment_id: s for s in report.segments}
    theme_idx = {t.theme_id: t for t in report.themes}
    ordered = sorted(report.correspondences, key=lambda c: (c.segment_id, c.theme_id))

    for corr in ordered:
        seg = seg_idx.get(corr.segment_id)
        theme = theme_idx.get(corr.theme_id)
        seg_label = f"{corr.segment_id} · {seg.name}" if seg else corr.segment_id
        theme_label = f"{corr.theme_id} · {theme.name}" if theme else corr.theme_id
        kinds = ", ".join(corr.evidence_kinds)
        table.add_row(seg_label, theme_label, kinds)
    console.print(table)


@main.command()
@click.option("--port", type=int, default=8501, show_default=True)
def ui(port: int) -> None:
    """Launch the Streamlit UI."""
    try:
        import streamlit.web.cli as stcli  # noqa: WPS433
    except Exception:
        console.print("[red]Streamlit is not installed. Install with: pip install 'quant-qual-bridge[ui]'[/red]")
        sys.exit(1)

    app_path = str(Path(__file__).resolve().parent / "app.py")
    sys.argv = ["streamlit", "run", app_path, "--server.port", str(port)]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
