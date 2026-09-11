"""CLI dispatch smoke tests over the fixture site."""

from __future__ import annotations

import json
from pathlib import Path

from fractiskills.cli import main
from fractiskills.models import write_json_atomic

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_discover_and_validate_cli_json(run_env, spec_file, capsys) -> None:
    output = run_env / "out"
    code = main(
        [
            "discover",
            "--spec",
            str(spec_file),
            "--output-dir",
            str(output),
            "--allow-private",
            "--json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["discovered_pages"] >= 4
    assert payload["incomplete"] is False

    empty = run_env / "empty-skills"
    empty.mkdir()
    code = main(["validate", "--skills-dir", str(empty), "--json"])
    assert code == 0  # zero tracked packages is a valid empty state
    capsys.readouterr()


def test_full_run_cli(run_env, spec_file, capsys) -> None:
    output = run_env / "out"
    skills = run_env / "skills"
    code = main(
        [
            "run",
            "--spec",
            str(spec_file),
            "--output-dir",
            str(output),
            "--skills-dir",
            str(skills),
            "--allow-private",
            "--json",
        ]
    )
    assert code == 0
    capsys.readouterr()
    # The tracked tree now holds validated packages and a discovery index.
    assert (skills / "index.json").is_file()
    packages = sorted(1 for p in skills.glob("*/*/SKILL.md"))
    assert len(packages) >= 4
    assert (output / "data" / "fractiskills_analysis.json").is_file()
    assert (output / "data" / "manuscript_receipt.json").is_file()


def test_render_reports_failed_section(run_env, spec_file, tmp_path, capsys) -> None:
    """A page that dies between discovery and render fails its section loudly."""

    from fractiskills.cli import cmd_render
    from fractiskills.discover import discover_site
    from fractiskills.models import SiteInventory, SiteSpec

    spec = SiteSpec.load(str(spec_file))
    discover_site(spec, output_dir=str(tmp_path / "out"), allow_private_hosts=True)
    # Rewrite the inventory to include a page the fixture server will not serve.
    payload = json.loads((tmp_path / "out" / "data" / "inventory.json").read_text())
    payload["entries"].append(
        {
            "url": f"{spec.base_url}vanishing-page",
            "path": "/vanishing-page",
            "section": "Core",
            "via_sitemap": False,
            "via_crawl": True,
            "title": None,
        }
    )
    write_json_atomic(
        str(tmp_path / "out" / "data" / "inventory.json"),
        SiteInventory.from_dict(payload).to_dict(),
    )
    args = type(
        "NS",
        (),
        {
            "spec": str(spec_file),
            "output_dir": str(tmp_path / "out"),
            "skills_dir": str(tmp_path / "skills"),
            "json": False,
            "refresh": False,
            "force_process": False,
            "evidence_origin": "fixture",
            "allow_private": True,
        },
    )()
    code = cmd_render(args)
    assert code == 1
