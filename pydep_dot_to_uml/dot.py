from __future__ import annotations
from typing import TYPE_CHECKING

from .file import MutableFile, File
from .util import INIT, warn

if TYPE_CHECKING:
    from pathlib import Path


class _QueryDict(dict):
    """
    A dict that constructs a MutableFile if an entry is missing
    """

    def __missing__(self, key):
        self[key] = MutableFile(key)
        return self[key]


def _parse_dot(data: str) -> tuple[str, ...]:
    """
    :fpath: The path to the dot file to parse
    :return: The arrow strings within the file
    """
    # Find all the labels and names within the dot text
    sect: int = data.rfind("\n", 0, data.find("label"))
    pkg: str = data[data.rfind("\n", 0, sect) : sect].strip().split(" ")[0]
    lines = (i.strip() for i in data[sect : data.find("\n", data.rfind("label"))].strip().split("\n"))
    lines = (i.replace(r"\.\n", ".") for i in lines)
    pairs = [(i.split(" ")[0], i[i.find('label="') + 7 : i.rfind('"')]) for i in lines] + [(pkg, pkg)]
    # Rename the dot labels with the actual names
    for i, k in sorted(pairs, key=lambda x: -len(x[0])):  # Sort to handle tags containing others
        data = data.replace(i, k)
    # Return only the arrow lines
    return tuple(i.strip() for i in data.split("\n") if "->" in i)


def _rm_classes(x: str) -> str:
    """
    If any character is a capital letter, assume it is a class and replace it with its enclosing package
    """
    cap = tuple(i for i in x if i.isupper())
    if len(cap) == 0:
        return x
    p = x[: x.find(cap[0]) - 1]
    warn(f"Replacing class {x} with parent {p}")
    return p


def _create_files(lines: tuple[str, ...]) -> set[MutableFile]:
    """
    Create a set of MutableFiles from the lines of a dot file
    This does not populate any fields other than name
    """
    files = _QueryDict()
    for line in (i.split(" [fill")[0] for i in lines):
        dependency, name = line.split(" -> ")
        if dependency != name:
            files[_rm_classes(name)].requires.add(files[_rm_classes(dependency)])
    return set(files.values())


def load(fpath: Path) -> tuple[File, set[File]]:
    # Create files
    data: str = fpath.read_text()
    files: set[MutableFile] = _create_files(_parse_dot(data))
    # Define parents
    for f in files:
        parents = tuple(i for i in files if f.name.startswith(f"{i.name}."))
        if parents:
            f.parent = max(parents, key=lambda x: len(x.name))
    roots = tuple(i for i in files if i.parent is None)
    if len(roots) != 1:
        raise ValueError("There should be exactly one root file")
    # Define children
    for f in files:
        f.children = {i for i in files if i.parent is not None and i.parent.name == f.name}
    # Define dirname's
    for f in files:
        f.dirname = f.name if f.children or f.parent is None else f.parent.name
    # Fix names
    for f in files:
        if f.children:
            f.name += f".{INIT}"
    # Construct Files
    delim: str = "_"
    while delim in data:
        delim += "_"
    return File.from_mutable(roots[0], delim)
