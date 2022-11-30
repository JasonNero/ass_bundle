from enum import Enum
from pathlib import Path

import typer
from rich import print

from . import core

app = typer.Typer(
    help="Parse and repath ass files, bundle all required resources.",
    no_args_is_help=True,
)


class RemapMode(str, Enum):
    pathmap = "pathmap"
    ass = "ass"


@app.command(no_args_is_help=True)
def run(
    source: Path = typer.Argument(..., help="Source directory of the ass files."),
    target: Path = typer.Argument(..., help="Target directory for all resources."),
    remap_mode: RemapMode = typer.Argument(RemapMode.ass, help="The remap mode."),
    copy: bool = typer.Option(True, help="Do the copy process."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't write any files."),
):
    """Run via commandline."""
    file_map = core.remap_ass_files(
        source, target, 
        fetch_only=dry_run or remap_mode == RemapMode.ass
    )

    if copy:
        core.copy_images(file_map, target, dry_run=dry_run)

    if remap_mode == RemapMode.pathmap:
        core.write_pathmap(file_map, target)


@app.command()
def gui():
    """Start the GUI."""
    print("[bold red]Not yet implemented ...[/bold red]")
