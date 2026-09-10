"""Thin wrapper: environment preflight before any acquisition."""

import sys
from pathlib import Path

from fractiskills.cli import _resolve_evidence_origin
from fractiskills.models import SiteSpec

if __name__ == "__main__":
    spec = SiteSpec.load("data/sources/ssvibelandia.yaml")
    print(f"spec ok: {spec.profile_id} -> {spec.base_url}")
    print(f"bindings: {len(spec.bindings)} declared")
    print(f"origin resolution: {_resolve_evidence_origin('auto', spec.base_url)}")
    Path("output").mkdir(exist_ok=True)
    print("output/ writable")
    sys.exit(0)
