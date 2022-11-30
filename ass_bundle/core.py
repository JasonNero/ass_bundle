import json
import os
import subprocess
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from rich import print
from rich.progress import track

# TODO: Remove hardcoded path, get from environment variable instead.
version = "2023"

if sys.platform == "darwin":
    sys.path.append(f"/Applications/Autodesk/Arnold/mtoa/{version}/scripts")
elif sys.platform == "win32":
    sys.path.append(f"C:/Program Files/Autodesk/Arnold/maya{version}/scripts")
    os.environ["PATH"] += f"C:/Program Files/Autodesk/Arnold/maya{version}/bin"  # Make sure the `ai.dll` file is found.
else:
    raise OSError("Unknown or unsupported OS!")

import arnold


@contextmanager
def init_arnold(log_folder: Path):
    """Initialize Arnold and exit safely after use.

    Args:
        log_folder (Path): Folder to save the 'arnold.log' file to.
    """
    try:
        arnold.AiBegin()
        arnold.AiMsgSetLogFileName((log_folder / "arnold.log").as_posix())
        arnold.AiMsgSetConsoleFlags(arnold.AI_LOG_NONE)
        arnold.AiMsgSetLogFileFlags(arnold.AI_LOG_ALL)
        yield
    except Exception as e:
        print(e)
        raise e
    finally:
        arnold.AiEnd()


def iter_universe_nodes(universe, node_type, node_class=""):
    """Iterate Arnold nodes of type `node_type`."""
    iter = arnold.AiUniverseGetNodeIterator(universe, node_type)
    while not arnold.AiNodeIteratorFinished(iter):
        node = arnold.AiNodeIteratorGetNext(iter)
        if not node_class or arnold.AiNodeIs(node, node_class):
            yield node

    arnold.AiNodeIteratorDestroy(iter)


@contextmanager
def open_scene(ass_file: Path, save_path: Optional[Path] = None):
    """Load the supplied ass file, yield the universe and optionally save it afterwards.

    Args:
        ass_file (Path): Path of the ass file.
        save_path (Path, optional): Save path. Defaults to None, not saving any changes made.
    """
    universe = arnold.AiUniverse()
    arnold.AiASSLoad(universe, ass_file.as_posix())
    yield universe
    if save_path:
        arnold.AiASSWrite(universe, save_path.as_posix())
    arnold.AiUniverseDestroy(universe)


def remap_ass_files(
    ass_folder: Path,
    target_folder: Path,
    fetch_only: bool = False,
) -> dict:
    """Open all .ass files in the directory and remaps all image paths to the target folder.

    Args:
        ass_folder (Path): Folder containing all the ass files for bundling.
        target_folder (Path): Folder to bundle all remapped ass files and textures to.
        fetch_only (bool, optional): Whether to only fetch paths for remapping. Defaults to False.

    Returns:
        dict: A mapping of source texture to target texture path.
    """
    target_folder.mkdir(exist_ok=True)
    file_map = {}

    with init_arnold(log_folder=target_folder):
        ass_files = list(ass_folder.glob("*.ass"))
        for ass_file in track(ass_files, f"Processing {len(ass_files)} ass files ..."):
            target_ass = target_folder / ass_file.name.replace(".ass", "_bundled.ass")

            with open_scene(ass_file, save_path=target_ass) as universe:
                for node in iter_universe_nodes(
                    universe, arnold.AI_NODE_SHADER, "image"
                ):
                    # Remap filepath to target folder.
                    curr_path = Path(arnold.AiNodeGetStr(node, "filename"))
                    new_path = target_folder / curr_path.name
                    if not fetch_only:
                        # Set the filename as relative path.
                        arnold.AiNodeSetStr(
                            node, "filename", ("./" + curr_path.name).encode("ascii")
                        )
                    file_map[curr_path] = new_path

    return file_map


def write_pathmap(
    file_map: dict,
    source_folder: Path,
    target_folder: Path,
):
    """Writes a pathmap.json file that can be used with Arnold by setting the filepath in the
    `ARNOLD_PATHMAP` environment variable.
    """
    filepath = target_folder / "pathmap.json"

    source_dirs = {file.parent for file in file_map.keys()}
    dir_mapping = {source_dir.as_posix(): "." for source_dir in source_dirs}

    pathmap = {
        "windows": dir_mapping,
        "mac": dir_mapping,
        "linux": dir_mapping,
    }

    with filepath.open(mode="w") as f:
        json.dump(pathmap, f, indent=4)


def copy_images(
    file_map: dict,
    target_folder: Path,
    dry_run: bool = False,
):
    """Preprocesses the filepath mapping and starts the copy process.

    Args:
        file_map (dict): A mapping of source texture to target texture path.
        target_folder (Path): Folder to bundle all remapped ass files and textures to.
        dry_run (bool, optional): Whether to skip the copy process. Defaults to False.
    """
    # Remap <udim> image files and update file_map in-place.
    for f in list(file_map.keys()):
        if "<udim>" in f.name:
            search_pattern = f.name.replace("<udim>", "????")
            for udim_file in f.parent.glob(search_pattern):
                file_map[udim_file] = target_folder / udim_file.name
            del file_map[f]

    if dry_run:
        print(f"Dry run detected, NOT copying {len(file_map)} files.")
        return

    # Copy all.
    # TODO: Multithreaded Copy?
    # TODO: Check by timestamp whether it actually needs copying.
    for (old, new) in track(file_map.items(), f"Copying {len(file_map)} files ..."):
        shutil.copy2(old, new)


def kick(source_folder: Path, use_pathmap: bool):
    if use_pathmap:
        print("Setting environment variables for pathmap rendering ...")
        pathmap = source_folder / "pathmap.json"
        os.environ["ARNOLD_PATHMAP"] = pathmap.resolve().as_posix()
        os.environ["BUNDLE_ROOT"] = source_folder.resolve().as_posix()
        print(source_folder.resolve().as_posix())

    ass_files = list(source_folder.glob("*.ass"))
    for ass_file in track(ass_files, f"Processing {len(ass_files)} ass files ..."):
        cmd = [
            "kick",
            "-i", ass_file.resolve().as_posix(),
            "-r", "320", "240",
            "-as", "1",
            "-o", ass_file.resolve().with_suffix(".exr").as_posix(),
            "-logfile", (source_folder / "arnold.log").resolve().as_posix(),
            # "-dw", "-dp",
        ]
        print(" ".join(cmd))

        # NOTE: Kick needs to run in the directory of the ass files to be able to 
        # resolve the relative path in the pathmap or the ass file itself.
        subprocess.Popen(cmd, env=os.environ, cwd=ass_file.parent.as_posix()).wait()

# TODO: Missing mappings to be fully portable:
#   - options > texture_searchpath
#   - options > procedural_searchpath
#   - driver > filename (or just use kicks -o flag)

# TODO: Check for unique names since all files will end up in the same
#       folder eventually (invert file_map dict and check length?)
