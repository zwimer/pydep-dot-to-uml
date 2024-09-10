from functools import cache
import sys


INIT = "_init_"  # Avoid __ since UML will interpret it


class Arrow:
    """
    Different types of arrows
    """

    EXTERNAL = "---down[#red]--->"
    PKG = "--down[#green]-->"
    INTRA = "-down[#blue]->"


@cache
def warn(msg):
    """
    Print a message to stderr, do not duplicate
    """
    print(msg, file=sys.stderr)
