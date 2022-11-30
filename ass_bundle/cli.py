from pathlib import Path

import typer
from rich import print

from . import core

app = typer.Typer(
    help="Parse and repath ass files, bundle all required resources.",
    no_args_is_help=True,
)


@app.command()
def run(
    source: Path = typer.Argument(..., help="Source directory of the ass files."),
    target: Path = typer.Argument(..., help="Target directory for all resources."),
    remap_only: bool = typer.Option(False, "--remap-only", help="Skips the copy process, only remaps the paths."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't write any files."),
):
    """Run via commandline."""
    file_map = core.remap_ass_files(source, target, fetch_only=dry_run)
    if not remap_only:
        core.copy_images(file_map, target, dry_run=dry_run)


@app.command()
def gui():
    """Start the GUI."""
    print("[bold red]Not yet implemented ...[/bold red]")
