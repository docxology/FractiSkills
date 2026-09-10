"""Thin wrapper: publish stage (see scripts/README.md)."""

import sys

from fractiskills.cli import main

if __name__ == "__main__":
    sys.exit(main(["publish", *sys.argv[1:]]))
