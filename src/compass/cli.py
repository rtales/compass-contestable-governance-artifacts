from __future__ import annotations

from pathlib import Path
import typer
from rich.console import Console

from compass.pipeline.run import run_recipe
from compass.snapshots.fetch import fetch_snapshot

app = typer.Typer(add_completion=False)
console = Console()

@app.command()
def fetch(dataset: str, catalog: Path = Path("snapshots/catalog.yaml")):
    """Install a snapshot into ./data (never at runtime)."""
    fetch_snapshot(dataset_id=dataset, catalog_path=catalog)
    console.print(f"[green]OK[/green] Installed snapshot: {dataset}")

@app.command()
def run(recipe: Path):
    """Run an experiment from a single recipe YAML."""
    out = run_recipe(recipe)
    console.print(f"[green]OK[/green] Run completed. Outputs: {out}")

if __name__ == "__main__":
    app()
