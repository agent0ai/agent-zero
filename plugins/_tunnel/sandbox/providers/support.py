"""Provider-local filesystem/log helpers; never import the Agent Zero framework."""
from pathlib import Path
import sys


class files:
    @staticmethod
    def get_abs_path(*parts):
        return str(Path('/var/lib/a0-tunnel').joinpath(*parts))


class PrintStyle:
    @staticmethod
    def error(*args):
        print(*args, file=sys.stderr, flush=True)
