import glob
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

# Append Arnold Python installation to PATH.
version = "2020"
sys.path.append(f"C:/Program Files/Autodesk/Arnold/maya{version}/scripts")
import arnold


@contextmanager
def init_universe():
    try:
        arnold.AiBegin()
        yield
    except Exception as e:
        print(e)
        raise e
    finally:
        arnold.AiEnd()


def universe_nodes(node_type):
    iter = arnold.AiUniverseGetNodeIterator(node_type)
    while not arnold.AiNodeIteratorFinished(iter):
        yield arnold.AiNodeIteratorGetNext(iter)
    arnold.AiNodeIteratorDestroy(iter)


def remap_images(ass_file: Path, target_folder: Path) -> dict:
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
                arnold.AiNodeSetStr(node, "filename", new_path_str)
                file_map[curr_path] = new_path

        target_ass = ass_file.as_posix().replace(".ass", "_bundled.ass")
        arnold.AiASSWrite(target_ass)

    return file_map


def copy_images(file_map: dict, target_folder: Path):
    """Preprocesses the filepath mapping and starts the copy process.
    """
    # Preprocess <udim> image files.
    for f in list(file_map.keys()):
        if "<udim>" in f.as_posix():
            for udim_file in glob.glob(f.as_posix().replace("<udim>", "????")):
                udim_file = Path(udim_file)
                file_map[udim_file] = target_folder / Path(udim_file).name
            del file_map[f]

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


if __name__ == "__main__":
    target_folder = Path("./testdata/bundled/")
    ass_file = Path("./testdata/test.ass")

    file_map = remap_images(ass_file, target_folder)
    copy_images(file_map, target_folder)

# Kick it:
# "C:/Program Files/Autodesk/Arnold/maya2020/bin/kick.exe" -i testdata/test_bundled.ass -o testdata/test_bundled.0001.exr
