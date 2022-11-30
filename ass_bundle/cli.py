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
def bundle(
    source: Path = typer.Argument(..., help="Source directory of the ass files."),
    target: Path = typer.Argument(..., help="Target directory for all resources."),
    remap_mode: RemapMode = typer.Argument(RemapMode.ass, help="The remap mode."),
    copy: bool = typer.Option(True, help="Do the copy process."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't write any files."),
):
    """Run via commandline."""
    file_map = core.remap_ass_files(
        source, target, 
        fetch_only=dry_run or (remap_mode == RemapMode.pathmap)
    )

    if copy:
        core.copy_images(file_map, target, dry_run=dry_run)

    if remap_mode == RemapMode.pathmap:
        core.write_pathmap(file_map, source, target)


@app.command()
def kick_compare(
    source: Path = typer.Argument(..., help="Source directory of the ass files."),
    use_pathmap: bool = typer.Argument(..., help="Whether to use the pathmap for remapping")
    # number: int = typer.Argument(..., help="Number of files to test/compare.")
):
    """Render images of original and remapped ass file, compare the results and highlight the differences.
    """
    core.kick(source, use_pathmap)
    # core.compare()


@app.command()
def gui():
    """Open the graphical user interface."""
    print("[bold red]Not yet implemented ...[/bold red]")
