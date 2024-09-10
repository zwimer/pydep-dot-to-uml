from __future__ import annotations
from dataclasses import dataclass, field
from typing import cast

from .util import INIT, Arrow


@dataclass
class MutableFile:
    name: str
    dirname: str | None = None
    parent: MutableFile | None = None
    requires: set[MutableFile] = field(default_factory=set)
    children: set[MutableFile] = field(default_factory=set)

    def __hash__(self) -> int:
        """
        Hash should only be based on the name
        """
        return hash(self.name)

    def _reachable(self, key: str) -> set[MutableFile]:
        got = getattr(self, key)
        return set.union(*(i.reachable(require_root=False) for i in got)) if got else set()

    def reachable(self, *, require_root: bool = True) -> set[MutableFile]:
        """
        :return: All MutableFiles recursively reachable via the given key, including the given file
        """
        if require_root and self.parent is not None:
            raise ValueError("Only the root file should be converted to a non-mutable File")
        return self._reachable("children") | self._reachable("requires") | {self}


@dataclass(kw_only=True)  # Effectively frozen = true, but we need it false for internal construction
class File:
    """
    An abstraction for a python file
    This class freezes is frozen if .frozen is True
    name is the pydep name give to the specific file
    """

    name: str
    dirname: str
    delim: str  # A delimiter to separate names in tags that is not present in any UML
    parent: File | None = None
    requires: set[File] = field(default_factory=set)
    children: set[File] = field(default_factory=set)
    frozen: bool = False

    def __hash__(self) -> int:
        """
        Hash should only be based on the name
        """
        return hash(self.name)

    def __setattr__(self, key, value):
        """
        Prevent setting any attributes if frozen
        """
        if self.frozen:
            raise AttributeError("Cannot set attributes on a frozen File")
        object.__setattr__(self, key, value)

    #
    # Properties
    #

    @property
    def lineage(self) -> set[str]:
        """
        :return: The directories that contain this file
        """
        ret = set()
        node = self
        while node.parent is not None:
            ret.add(node.dirname)
            node = node.parent
        return ret

    @property
    def src_tag(self) -> str:
        """
        :return: The tag when this node is the source node in the UML
        """
        if not self.init_py:
            return self.dst_tag
        return self.dirname.replace(".", self.delim)

    @property
    def dst_tag(self) -> str:
        """
        :return: The tag when this node is the destination node in the UML
        """
        return self.name.replace(".", self.delim)

    @property
    def init_py(self) -> bool:
        """
        :return: True if this file represents a __init__.py file
        """
        return self.name.endswith(INIT)

    #
    # Helper methods
    #

    def _arrow(self, requirement: File) -> str:
        """
        :return: The desired arrow based on the requirement
        """
        if self.dirname == requirement.dirname:
            return Arrow.INTRA
        return Arrow.PKG if self.dirname in requirement.lineage else Arrow.EXTERNAL

    #
    # Public methods
    #

    def package(self, *, _require_root: bool = True) -> str:
        """
        :return: The UML representation of this file excluding the arrows
        """
        if _require_root and self.parent is not None:
            raise ValueError("Only the root file should be converted to a package")
        name = self.name.rsplit(".", 1)[-1]
        if not self.init_py:
            return f'file "{name}" as {self.src_tag}'
        items = [i.package(_require_root=False) for i in self.children]
        items.append(f'file "{INIT}" as {self.src_tag}')
        name = self.dirname.rsplit(".", 1)[-1]
        ret = f'package "{name}" as {self.dst_tag} {{\n{"\n".join(sorted(items))}\n}}'
        return ret.replace("\n\n", "\n")

    def arrows(self) -> set[str]:
        """
        :return: The set of UML arrows that this file requires
        """
        return {f"{self.src_tag} {self._arrow(i)} {i.dst_tag}" for i in self.requires}

    @staticmethod
    def from_mutable(file: MutableFile, delim: str, *, _require_root: bool = True) -> tuple[File, set[File]]:
        """
        :return: A File given file and the File's that had to be constructed to produce it
        """
        if file.parent is not None:
            raise ValueError("Only the root file should be converted to a non-mutable File")
        muts: set[MutableFile] = file.reachable()
        if any(i.dirname is None for i in muts):
            raise ValueError("Cannot convert files with None .dirname")
        rv = {i: File(name=i.name, dirname=cast(str, i.dirname), delim=delim) for i in muts}
        for old, new in rv.items():
            new.parent = rv[old.parent] if old.parent is not None else None
            new.requires = {rv[i] for i in old.requires}
            new.children = {rv[i] for i in old.children}
            new.frozen = True  # Freeze the file
        return rv[file], set(rv.values())
