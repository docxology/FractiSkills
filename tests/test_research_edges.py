"""Edge-path tests: research layer, CLI subcommands, and sitemap robustness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from fractiskills.cli import main
from fractiskills.discover import fetch_sitemap_entries
from fractiskills.models import try_load_json
from fractiskills.publication import bind_manuscript

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_fetch_sitemap_follows_redirect() -> None:
    server = HTTPServer()
    server.expect_request("/robots.txt").respond_with_data("User-agent: *\nAllow: /\n")
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    server.expect_request("/sitemap2.xml").respond_with_data(
        f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}/a</loc></url></urlset>",
        content_type="application/xml",
    )
    server.expect_request("/sitemap.xml").respond_with_data(
        "", status=301, headers={"Location": "/sitemap2.xml"}
    )
    try:
        entries, _ = fetch_sitemap_entries(
            f"{base}/sitemap.xml", base_url=f"{base}/", user_agent="Test/0.1"
        )
        assert [str(entry["url"]) for entry in entries] == [f"{base}/a"]
    finally:
        server.stop()


def test_fetch_sitemap_parse_error_raises() -> None:
    server = HTTPServer()
    server.expect_request("/robots.txt").respond_with_data("User-agent: *\nAllow: /\n")
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    server.expect_request("/sitemap.xml").respond_with_data(
        "<not-xml", content_type="application/xml"
    )
    try:
        with pytest.raises(ValueError, match="not parseable XML"):
            fetch_sitemap_entries(f"{base}/sitemap.xml", base_url=f"{base}/", user_agent="T/0.1")
    finally:
        server.stop()


def test_fetch_sitemap_rejects_unsafe_urls() -> None:
    server = HTTPServer()
    server.expect_request("/robots.txt").respond_with_data("User-agent: *\nAllow: /\n")
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    server.expect_request("/sitemap.xml").respond_with_data(
        '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>ftp://x.example/a</loc></url>"
        "<url><loc>https://other.example.com/foreign</loc></url></urlset>",
        content_type="application/xml",
    )
    try:
        entries, notes = fetch_sitemap_entries(
            f"{base}/sitemap.xml", base_url=f"{base}/", user_agent="T/0.1"
        )
        assert entries == []
        assert any("unsafe" in note for note in notes)
        assert any("cross-origin" in note for note in notes)
    finally:
        server.stop()


def test_try_load_missing_returns_none(tmp_path: Path) -> None:
    assert try_load_json(str(tmp_path / "missing.json")) is None


def test_bind_manuscript_rejects_unresolved_braces(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(
        "# Abstract {#sec:abstract}\n\nKnown {{TOTAL_PAGES}} and stray {{lower_case}}.\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unresolved manuscript tokens"):
        bind_manuscript(
            manuscript_dir=str(manuscript),
            output_dir=str(tmp_path / "out"),
            variables={"TOTAL_PAGES": "5"},
        )


def test_cli_all_subcommands(run_env, spec_file, capsys) -> None:
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

    assert (
        main(
            [
                "analyze",
                "--spec",
                str(spec_file),
                "--output-dir",
                str(output),
                "--skills-dir",
                str(skills),
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["discovered_pages"] >= 4

    assert (
        main(
            [
                "figures",
                "--spec",
                str(spec_file),
                "--output-dir",
                str(output),
                "--skills-dir",
                str(skills),
                "--json",
            ]
        )
        == 0
    )
    registry = json.loads(capsys.readouterr().out)
    assert len(registry) == 10

    assert (
        main(
            [
                "research",
                "--spec",
                str(spec_file),
                "--output-dir",
                str(output),
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert (
        main(
            [
                "publish",
                "--spec",
                str(spec_file),
                "--output-dir",
                str(output),
                "--skills-dir",
                str(skills),
                "--json",
            ]
        )
        == 0
    )
    published = json.loads(capsys.readouterr().out)
    assert published["count"] >= 4

    assert main(["validate", "--spec", str(spec_file), "--skills-dir", str(skills), "--json"]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["failures"] == []
