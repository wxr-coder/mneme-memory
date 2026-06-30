"""CLI entry point for mneme-memory."""

from __future__ import annotations

import click
from rich.console import Console

from mneme_core.capability import detect_hardware, detect_tier
from mneme_core.config import load_config

console = Console()


@click.group()
@click.version_option()
def main():
    """mneme-memory: Human-like memory system for AI agents."""


@main.command()
def init():
    """Initialize mneme-memory (detect tier, show config)."""
    hardware = detect_hardware()
    config = load_config()
    tier = detect_tier(hardware, override=config.tier)

    console.print("[bold green]mneme-memory initialized[/bold green]")
    console.print(f"  Tier: [bold]{tier.value}[/bold]")
    console.print(f"  GPU: {hardware.gpu_name or 'None'} ({hardware.gpu_vram_gb:.1f} GB VRAM)")
    console.print(f"  CPU cores: {hardware.cpu_cores}")
    console.print(f"  RAM: {hardware.ram_gb:.1f} GB")
    console.print(f"  Retrieval paths: {tier.retrieval_paths}")
    console.print(f"  Reflect rounds: {tier.reflect_max_rounds}")
    console.print(f"  Consolidation: {tier.consolidation_mode}")
    console.print(f"  Reranker: {'yes' if tier.has_reranker else 'no'}")
    console.print(f"  Personality momentum: {tier.personality_momentum}")


@main.command()
def status():
    """Show current status and tier."""
    init()


@main.command()
@click.option("--content", "-c", prompt="Memory content", help="Memory text content")
def retain(content):
    """Store a memory."""
    console.print(f"[green]Retained:[/green] {content[:100]}")


@main.command()
@click.argument("query")
@click.option("--top-k", "-k", default=10, help="Number of results")
def recall(query, top_k):
    """Search memories."""
    console.print(f"[yellow]Searching:[/yellow] {query} (top_k={top_k})")
    console.print("[dim]No storage backend configured yet[/dim]")


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
