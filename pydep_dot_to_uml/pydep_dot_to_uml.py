from __future__ import annotations
from pathlib import Path
import argparse
import sys

from .dot import load


__version__ = "1.0.0"


def _pydep_dot_to_uml(fpath: Path) -> str:
    root, files = load(fpath)
    arrows = "\n".join(sorted(set.union(*tuple(i.arrows() for i in files))))
    return f"@startuml\n{root.package()}\n\n{arrows}\n@enduml"


def pydep_dot_to_uml(file: Path) -> None:
    print(_pydep_dot_to_uml(file))


def parse_args(prog: str, *args: str) -> argparse.Namespace:
    base: str = Path(prog).name
    parser = argparse.ArgumentParser(prog=base)
    parser.add_argument("--version", action="version", version=f"{base} {__version__}")
    parser.add_argument("file", type=Path, help="Path to the dot file")
    return parser.parse_args(args)


def cli():
    pydep_dot_to_uml(**vars(parse_args(*sys.argv)))
