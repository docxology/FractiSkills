"""Thin wrapper: discover stage (see scripts/README.md)."""

import sys

from fractiskills.cli import main

if __name__ == "__main__":
    sys.exit(main(["discover", *sys.argv[1:]]))
