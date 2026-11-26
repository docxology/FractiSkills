"""Prepare the benign local site artifacts for a disposable Template render."""

from pathlib import Path

from conftest import serve_fixture_site, write_fixture_spec

from fractiskills.discover import discover_site
from fractiskills.models import SiteSpec
from fractiskills.pipeline import publish_skills, render_site


def main() -> None:
    """Build a fresh fixture inventory and publish only into ignored output."""
    project = Path(__file__).resolve().parents[1]
    output = project / "output"
    if output.exists():
        raise SystemExit("Use a disposable checkout with no existing output directory.")
    output.mkdir()
    with serve_fixture_site() as base_url:
        spec = SiteSpec.load(str(write_fixture_spec(base_url, output)))
        inventory, _ = discover_site(spec, output_dir=str(output), allow_private_hosts=True)
        summary = render_site(
            inventory,
            spec,
            output_dir=str(output),
            evidence_origin="fixture",
            allow_private_hosts=True,
        )
        if not all(run.ok for run in summary.runs):
            raise SystemExit("Local fixture rendering failed.")
        publish_skills(str(output), str(output / "fixture-skills"))


if __name__ == "__main__":
    main()
