"""Parent-template hook: rebuild research inputs before rendering."""

import sys
from pathlib import Path

from fractiskills.publication import build_research_package

if __name__ == "__main__":
    project = Path(__file__).resolve().parents[1]
    receipt = build_research_package(str(project), str(project / "output"))
    if receipt["receipt"]["used_tokens"] == {}:
        print("warning: no manuscript tokens were bound", file=sys.stderr)
        sys.exit(1)
    print(f"bound {len(receipt['receipt']['rendered_chapters'])} chapters")
