from pathlib import Path

import typer
from rich import print

from . import core

app = typer.Typer(help="Parse and repath ass files, bundle all required resources.")


@app.command()
def run(
    source: Path = typer.Argument(..., help="Source directory of the ass files."),
    target: Path = typer.Argument(..., help="Target directory for all resources."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't write any files."),
):
    """Run via commandline."""
    file_map = core.remap_ass_files(source, target, fetch_only=dry_run)
    core.copy_images(file_map, target, dry_run=dry_run)
    # Kick "C:/Program Files/Autodesk/Arnold/maya2020/bin/kick.exe" -i testdata/test_bundled.ass -o testdata/test_bundled.0001.exr


@app.command()
def gui():
    """Start the GUI."""
    print("[bold red]Not yet implemented ...[/bold red]")
