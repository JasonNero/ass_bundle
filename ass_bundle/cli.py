from enum import Enum
from pathlib import Path
import subprocess

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
        fetch_only=dry_run or remap_mode == RemapMode.ass
    )

    if copy:
        core.copy_images(file_map, target, dry_run=dry_run)

    if remap_mode == RemapMode.pathmap:
        core.write_pathmap(file_map, target)


@app.command()
def kick_compare(
    source: Path = typer.Argument(..., help="Source directory of the ass files."),
    target: Path = typer.Argument(..., help="Target directory for all resources."),
    number: int = typer.Argument(..., help="Number of files to test/compare.")
):
    """Render images of original and remapped ass file, compare the results and highlight the differences.
    """
    return
    version = "2023"
    cmd = [
        f"/Applications/Autodesk/Arnold/mtoa/{version}/bin/kick",
        f"-i {first_kick}",
        "-r 640 480",
        "-as 4",
        f"-o {output_image}",
    ]
    subprocess.Popen(cmd)


@app.command()
def gui():
    """Open the graphical user interface."""
    print("[bold red]Not yet implemented ...[/bold red]")
