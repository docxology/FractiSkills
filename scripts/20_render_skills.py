"""Thin wrapper: render stage (see scripts/README.md)."""

import sys

from fractiskills.cli import main

if __name__ == "__main__":
    sys.exit(main(["render", *sys.argv[1:]]))
