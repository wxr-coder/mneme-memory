"""CLI entry point for mneme-memory.

Thin wrapper around the mneme SDK. All business logic lives in the SDK/engine.
"""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.table import Table

from mneme import Mneme

console = Console()


@click.group()
@click.version_option()
@click.option(
    "--remote",
    "-r",
    default=None,
    help="Connect to remote mneme-server URL instead of embedded mode",
)
@click.pass_context
def main(ctx, remote):
    """mneme-memory: Human-like memory system for AI agents."""
    if remote:
        ctx.obj = Mneme.connect(remote)
    else:
        ctx.obj = Mneme.embed()


@main.command()
@click.pass_obj
def init(mneme: Mneme):
    """Initialize mneme-memory (detect tier, show config)."""
    _show_status(mneme)


@main.command()
@click.pass_obj
def status(mneme: Mneme):
    """Show current status and tier."""
    _show_status(mneme)


def _show_status(mneme: Mneme) -> None:
    """Shared logic for init and status commands."""
    health = asyncio.run(mneme.health())
    stats = asyncio.run(mneme.stats())

    console.print("[bold green]mneme-memory initialized[/bold green]")
    console.print(f"  Mode: [bold]{health.get('mode', 'remote')}[/bold]")
    console.print(f"  Tier: [bold]{health['tier']}[/bold]")

    hw = health.get("hardware", {})
    gpu_name = hw.get("gpu_name", "None")
    gpu_vram = hw.get("gpu_vram_gb", 0)
    console.print(f"  GPU: {gpu_name} ({gpu_vram:.1f} GB VRAM)")
    console.print(f"  CPU cores: {hw.get('cpu_cores', '?')}")
    console.print(f"  RAM: {hw.get('ram_gb', 0):.1f} GB")

    table = Table(title="Engine Capabilities")
    table.add_column("Capability", style="cyan")
    table.add_column("Value", style="green")
    for key, val in stats.items():
        table.add_row(key, str(val))
    console.print(table)


@main.command()
@click.option("--content", "-c", prompt="Memory content", help="Memory text content")
@click.option("--type", "-t", "fact_type", default="experience", help="Memory layer")
@click.pass_obj
def retain(mneme: Mneme, content, fact_type):
    """Store a memory."""
    result = asyncio.run(mneme.retain(content=content, fact_type=fact_type))
    console.print(f"[green]Retained:[/green] {result.get('content_preview', content[:100])}")
    console.print(f"  ID: {result.get('memory_id', '?')}")
    console.print(f"  Tier: {result.get('tier', '?')}")


@main.command()
@click.argument("query")
@click.option("--top-k", "-k", default=10, help="Number of results")
@click.pass_obj
def recall(mneme: Mneme, query, top_k):
    """Search memories."""
    console.print(f"[yellow]Searching:[/yellow] {query} (top_k={top_k})")
    results = asyncio.run(mneme.recall(query=query, top_k=top_k))

    if not results:
        console.print("[dim]No results (no storage backend configured yet)[/dim]")
        return

    table = Table(title=f"Results for: {query}")
    table.add_column("#", style="dim")
    table.add_column("Score", style="green")
    table.add_column("Type", style="cyan")
    table.add_column("Content")
    table.add_column("Source", style="dim")

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            f"{r.get('score', 0):.3f}",
            r.get("fact_type", "?"),
            r.get("content", "")[:80],
            r.get("source", "?"),
        )
    console.print(table)


@main.command()
@click.argument("query")
@click.option("--top-k", "-k", default=10, help="Number of results to consider")
@click.pass_obj
def reflect(mneme: Mneme, query, top_k):
    """Run agentic reflection on a query."""
    console.print(f"[cyan]Reflecting on:[/cyan] {query}")
    result = asyncio.run(mneme.reflect(query=query, top_k=top_k))

    console.print(f"  Rounds: {result.get('rounds', 0)}")
    console.print(f"  Memories found: {result.get('memories_found', 0)}")

    synthesis = result.get("synthesis")
    if synthesis:
        console.print(f"\n[bold]Synthesis:[/bold]\n{synthesis}")
    else:
        console.print(f"\n[dim]{result.get('message', 'No synthesis available')}[/dim]")


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", "-p", default=9177, help="Port to bind")
def serve(host, port):
    """Start the API server."""
    console.print(f"[bold green]Starting mneme-server on {host}:{port}[/bold green]")
    import uvicorn

    from mneme_server.main import app

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
