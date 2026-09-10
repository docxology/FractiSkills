"""Thin wrapper: analyze stage (see scripts/README.md)."""

import sys

from fractiskills.cli import main

if __name__ == "__main__":
    sys.exit(main(["analyze", *sys.argv[1:]]))
