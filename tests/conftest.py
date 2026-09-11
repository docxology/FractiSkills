"""Shared fixtures: a local multi-page fixture site served over real HTTP."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pytest_httpserver import HTTPServer

from fractiskills.models import SiteSpec

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def run_env(tmp_path, monkeypatch):
    """Chdir into the repo root and hand back a tmp_path for outputs."""
    monkeypatch.chdir(REPO_ROOT)
    return tmp_path


def _page(title: str, body: str, links: list[str] | None = None) -> str:
    nav = "".join(f'<a href="{link}">{link}</a> ' for link in (links or []))
    return (
        "<!doctype html><html><head><title>"
        f"{title}</title></head><body><article><h1>{title}</h1>"
        f"<p>{body}</p>{nav}</article></body></html>"
    )


SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{base}/</loc><priority>1.0</priority></url>
  <url><loc>{base}/blog/a</loc><priority>0.9</priority></url>
  <url><loc>{base}/blog/b</loc><priority>0.8</priority></url>
  <url><loc>{base}/old-page</loc><priority>0.5</priority></url>
  <url><loc>{base}/reader.html?id=doc1</loc><priority>0.7</priority></url>
  <url><loc>{base}/papers</loc><priority>0.6</priority></url>
  <url><loc>https://other.example.com/foreign</loc></url>
</urlset>
"""


@pytest.fixture()
def fixture_site():
    """Serve a small site with sitemap, redirect alias, and dynamic pages."""
    server = HTTPServer()
    server.expect_request("/robots.txt").respond_with_data(
        "User-agent: *\nAllow: /\n", content_type="text/plain"
    )
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    server.expect_request("/sitemap.xml").respond_with_data(
        SITEMAP_XML.format(base=base), content_type="application/xml"
    )
    server.expect_request("/").respond_with_data(
        _page("Fixture Home", "welcome home", links=["/blog/a", "/blog/b", "/reader.html?id=doc1"]),
        content_type="text/html",
    )
    server.expect_request("/blog/a").respond_with_data(
        _page("Blog A", "post alpha with real content", links=["/blog/b"]),
        content_type="text/html",
    )
    server.expect_request("/blog/b").respond_with_data(
        _page("Blog B", "post beta with more content"),
        content_type="text/html",
    )
    server.expect_request("/old-page").respond_with_data(
        "", status=301, headers={"Location": "/blog/a"}
    )
    server.expect_request("/reader.html").respond_with_data(
        _page("Reader Shell", "Loading document...", links=["/blog/a"]),
        content_type="text/html",
    )
    server.expect_request("/papers").respond_with_data(
        _page("Papers Shell", "Loading catalog..."),
        content_type="text/html",
    )
    server.expect_request("/api/whitepaper").respond_with_json(
        {
            "ok": True,
            "id": "doc1",
            "title": "Document One · Real Paper",
            "html": "<p><strong>Doc</strong> body line one.</p><p>Line two.</p>",
        }
    )
    server.expect_request("/api/whitepaper-catalog").respond_with_json(
        {
            "ok": True,
            "documents": [{"id": "doc1"}, {"id": "doc2"}],
            "html": "<p>Catalog of two documents.</p>",
        }
    )
    yield base
    server.stop()


@pytest.fixture()
def spec_file(fixture_site: str, tmp_path: Path) -> Path:
    """A site spec pointing at the fixture server, written to tmp_path."""
    spec = {
        "id": "fixturesite",
        "name": "Fixture Site",
        "base_url": fixture_site + "/",
        "sitemap_url": fixture_site + "/sitemap.xml",
        "user_agent": "FractiSkills-Test/0.1",
        "discovery": {
            "max_pages": 50,
            "max_requests": 300,
            "max_depth": 3,
            "min_delay_seconds": 0.0,
        },
        "crawl": {"min_delay_seconds": 0.0, "request_timeout_seconds": 10},
        "augment": {"timeout_seconds": 10},
        "bindings": [
            {"match_path": "/reader.html", "api_template": "/api/whitepaper?id={id}"},
            {"match_path": "/papers", "api_template": "/api/whitepaper-catalog"},
        ],
    }
    path = tmp_path / "fixturesite.yaml"
    path.write_text(yaml.safe_dump(spec), encoding="utf-8")
    return path


@pytest.fixture()
def loaded_spec(spec_file: Path) -> SiteSpec:
    """SiteSpec loaded from spec_file against the running fixture server."""
    return SiteSpec.load(str(spec_file))


@pytest.fixture()
def fixture_inventory(fixture_site: str, loaded_spec: SiteSpec, tmp_path: Path):
    """Run discovery against the fixture site; returns (inventory,
    output_dir, inventory_path). Performs local-HTTP acquisition and writes
    inventory.json under tmp_path."""
    from fractiskills.discover import discover_site

    output_dir = str(tmp_path / "output")
    inventory, path = discover_site(loaded_spec, output_dir=output_dir, allow_private_hosts=True)
    return inventory, output_dir, path
