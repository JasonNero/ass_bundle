import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

# TODO: Remove hardcoded path, get from environment variable instead.
version = "2022"
sys.path.append(f"C:/Program Files/Autodesk/Arnold/maya{version}/scripts")
import arnold


@contextmanager
def init_universe():
    """Initialize Arnold and exit safely after use.
    """
    try:
        arnold.AiBegin()
        yield
    except Exception as e:
        print(e)
        raise e
    finally:
        arnold.AiEnd()


def universe_nodes(node_type):
    """Iterate Arnold nodes of type `node_type`.
    """
    iter = arnold.AiUniverseGetNodeIterator(node_type)
    while not arnold.AiNodeIteratorFinished(iter):
        yield arnold.AiNodeIteratorGetNext(iter)
    arnold.AiNodeIteratorDestroy(iter)


def remap_images(ass_file: Path, target_folder: Path, fetch_only: bool = False) -> dict:
    """Opens the .ass file and remaps all image paths to the target folder.
    Returns the resulting old to new path mapping for a subsequent copy task.
    """
    target_folder.mkdir(exist_ok=True)
    file_map = {}

    with init_universe():
        arnold.AiMsgSetLogFileName("bundle.log")
        arnold.AiMsgSetLogFileFlags(arnold.AI_LOG_ALL)

        arnold.AiASSLoad(ass_file.as_posix())

        for node in universe_nodes(arnold.AI_NODE_SHADER):
            if arnold.AiNodeIs(node, "image"):
                # Remap filepath to target folder.
                curr_path = Path(arnold.AiNodeGetStr(node, "filename"))
                new_path = target_folder / curr_path.name
                new_path_str = new_path.as_posix().encode("ascii")
                if not fetch_only:
                    arnold.AiNodeSetStr(node, "filename", new_path_str)
                file_map[curr_path] = new_path

        target_ass = ass_file.as_posix().replace(".ass", "_bundled.ass")
        if not fetch_only:
            arnold.AiASSWrite(target_ass)

    return file_map


def copy_images(file_map: dict, target_folder: Path, dry_run: bool = False):
    """Preprocesses the filepath mapping and starts the copy process.
    """
    # Preprocess <udim> image files and update file_map in-place.
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
    for i, (old, new) in enumerate(file_map.items()):
        print(f"Copying file {new.name} - {i+1}/{len(file_map)}")
        shutil.copy2(old, new)


# TODO: Missing mappings to be fully portable:
#   - options > texture_searchpath
#   - options > procedural_searchpath
#   - driver > filename (can also be override by kicks -o flag)

# TODO: Check for unique names since all files will end up in the same
#       folder eventually (invert file_map dict and check length?)

# TODO: Check a single *.0001.ass but remap all ass files/frames.
