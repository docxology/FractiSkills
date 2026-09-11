"""Parent-template hook: rebuild research inputs before rendering.

The parent renderer invokes this file directly; all policy (exit codes,
token-receipt warnings) lives in :func:`fractiskills.publication.run_hook`.
"""

import sys
from pathlib import Path

from fractiskills.publication import run_research_hook

if __name__ == "__main__":
    sys.exit(run_research_hook(Path(__file__).resolve().parents[1]))
