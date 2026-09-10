"""Coverage-focused edge tests: human CLI output, validation failures, aliases."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pytest_httpserver import HTTPServer

from fractiskills.analysis import _skill_frontmatter_description, write_skills_csv
from fractiskills.cli import main
from fractiskills.discover import discover_site
from fractiskills.models import SiteSpec

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def run_env(tmp_path, monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    return tmp_path


def test_frontmatter_description_variants() -> None:
    md = '---\nname: x\ndescription: "A quoted, described skill"\n---\nbody'
    assert _skill_frontmatter_description(md) == "A quoted, described skill"
    assert _skill_frontmatter_description("no frontmatter at all") == ""
    assert _skill_frontmatter_description("---\nname: x\n---\nbody") == ""


def test_write_skills_csv_empty(tmp_path: Path) -> None:
    write_skills_csv([], str(tmp_path / "out"))
    assert (tmp_path / "out" / "data" / "skills.csv").is_file()


def test_cli_human_output_paths(run_env, spec_file, capsys) -> None:
    output = run_env / "out"
    skills = run_env / "skills"
    assert (
        main(
            [
                "run",
                "--spec",
                str(spec_file),
                "--output-dir",
                str(output),
                "--skills-dir",
                str(skills),
                "--allow-private",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "discovered" in captured.out
    assert "rendered" in captured.out
    assert "published" in captured.out
    assert "figures bound" in captured.out


def test_cli_validate_reports_corrupt_package(run_env, spec_file, capsys) -> None:
    output = run_env / "out"
    skills = run_env / "skills"
    assert (
        main(
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
        == 0
    )
    capsys.readouterr()
    corrupt = skills / "Core" / "Corrupt-Thing"
    corrupt.mkdir(parents=True, exist_ok=True)
    (corrupt / "SKILL.md").write_text("not a valid skill", encoding="utf-8")
    assert main(["validate", "--spec", str(spec_file), "--skills-dir", str(skills)]) == 1
    captured = capsys.readouterr()
    assert "FAILED" in captured.err


def test_discover_resolves_chained_redirect_alias(tmp_path: Path) -> None:
    server = HTTPServer()
    server.expect_request("/robots.txt").respond_with_data("User-agent: *\nAllow: /\n")
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    server.expect_request("/sitemap.xml").respond_with_data(
        f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}/start</loc></url></urlset>",
        content_type="application/xml",
    )
    server.expect_request("/start").respond_with_data(
        "", status=301, headers={"Location": "/middle"}
    )
    server.expect_request("/middle").respond_with_data(
        "", status=302, headers={"Location": "/final"}
    )
    server.expect_request("/final").respond_with_data(
        "<html><head><title>Final</title></head><body><article>content</article></body></html>",
        content_type="text/html",
    )
    spec = {
        "id": "chain",
        "name": "Chain",
        "base_url": f"{base}/",
        "sitemap_url": f"{base}/sitemap.xml",
        "discovery": {"min_delay_seconds": 0.0},
        "crawl": {"min_delay_seconds": 0.0},
    }
    spec_path = tmp_path / "chain.yaml"
    spec_path.write_text(yaml.safe_dump(spec))
    try:
        inventory, _ = discover_site(
            SiteSpec.load(str(spec_path)),
            output_dir=str(tmp_path / "out"),
            allow_private_hosts=True,
        )
        finals = [entry for entry in inventory.entries if entry.url.endswith("/final")]
        assert len(finals) == 1
        aliases = {alias for entry in inventory.entries for alias in entry.alias_urls}
        assert any(alias.endswith("/start") for alias in aliases)
        assert any(alias.endswith("/middle") for alias in aliases)
        assert inventory.sitemap_url_count == 1
    finally:
        server.stop()
