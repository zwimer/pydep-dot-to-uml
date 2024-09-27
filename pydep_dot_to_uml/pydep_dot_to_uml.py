from __future__ import annotations
from pathlib import Path
import argparse

from .dot import load


__version__ = "1.0.2"


def _pydep_dot_to_uml(fpath: Path) -> str:
    root, files = load(fpath)
    arrows = "\n".join(sorted(set.union(*tuple(i.arrows() for i in files))))
    return f"@startuml\n{root.package()}\n\n{arrows}\n@enduml"


def cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=f"{parser.prog} {__version__}")
    parser.add_argument("file", type=Path, help="Path to the dot file")
    print(_pydep_dot_to_uml(parser.parse_args().file))
