"""Discovery tests against a real local fixture HTTP server."""

from __future__ import annotations

from pathlib import Path

import yaml
from pytest_httpserver import HTTPServer

from fractiskills.discover import discover_site, fetch_sitemap_entries


def test_discover_unions_sitemap_and_crawl(fixture_inventory) -> None:
    inventory, _, _ = fixture_inventory
    urls = {entry.url for entry in inventory.entries}
    # Homepage and blog pages come from both the sitemap and the crawl.
    assert any(url.endswith("/blog/a") for url in urls)
    assert any(url.endswith("/blog/b") for url in urls)
    # Every entry records honest provenance.
    for entry in inventory.entries:
        assert entry.via_sitemap or entry.via_crawl
    assert inventory.sitemap_url_count == 6  # cross-origin entry rejected
    assert inventory.crawl_accepted_count >= 4


def test_discover_records_redirect_alias(fixture_inventory) -> None:
    inventory, _, _ = fixture_inventory
    blog_a = next(e for e in inventory.entries if e.url.endswith("/blog/a"))
    assert blog_a.via_sitemap is True
    # /old-page is a sitemap URL that redirects onto /blog/a: alias, not page.
    aliases = {alias for entry in inventory.entries for alias in entry.alias_urls}
    assert any(alias.endswith("/old-page") for alias in aliases)
    assert not any(
        url.endswith("/old-page") and url not in aliases
        for url in {e.url for e in inventory.entries}
    )


def test_discover_preserves_query_identity(fixture_inventory) -> None:
    inventory, _, _ = fixture_inventory
    reader = next(e for e in inventory.entries if e.path.startswith("/reader.html"))
    assert reader.path == "/reader.html?id=doc1"
    assert reader.section == "Core"
    assert reader.title == "Reader Shell"


def test_discover_rejects_cross_origin_sitemap_entry(fixture_inventory) -> None:
    inventory, _, _ = fixture_inventory
    assert all("other.example.com" not in entry.url for entry in inventory.entries)
    assert any("cross-origin" in warning for warning in inventory.crawl_warnings)


def test_discover_is_complete_for_fixture(fixture_inventory) -> None:
    inventory, _, _ = fixture_inventory
    assert inventory.incomplete is False


def test_fetch_sitemap_entries_reports_bad_priority(fixture_site: str) -> None:
    server = HTTPServer()
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    server.expect_request("/robots.txt").respond_with_data("User-agent: *\nAllow: /\n")
    server.expect_request("/sitemap.xml").respond_with_data(
        f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}/a</loc><priority>not-a-number</priority></url></urlset>",
        content_type="application/xml",
    )
    try:
        entries, notes = fetch_sitemap_entries(
            f"{base}/sitemap.xml", base_url=f"{base}/", user_agent="Test/0.1"
        )
        assert len(entries) == 1
        assert entries[0]["priority"] is None
        assert any("non-numeric priority" in note for note in notes)
    finally:
        server.stop()


def test_discover_handles_unreachable_sitemap_url(fixture_site: str, tmp_path: Path) -> None:
    """A sitemap URL that 404s becomes a recorded note, never a fake page."""
    server = HTTPServer()
    server.start()
    base = f"http://127.0.0.1:{server.port}"
    server.expect_request("/robots.txt").respond_with_data("User-agent: *\nAllow: /\n")
    server.expect_request("/sitemap.xml").respond_with_data(
        f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}/gone</loc></url>"
        f"<url><loc>{base}/blog/a</loc></url></urlset>",
        content_type="application/xml",
    )
    server.expect_request("/blog/a").respond_with_data(
        "<html><head><title>A</title></head><body><article>alpha</article></body></html>",
        content_type="text/html",
    )
    spec_data = {
        "id": "gone",
        "name": "Gone",
        "base_url": f"{base}/",
        "sitemap_url": f"{base}/sitemap.xml",
        "discovery": {"min_delay_seconds": 0.0},
        "crawl": {"min_delay_seconds": 0.0},
    }
    spec_path = tmp_path / "gone.yaml"
    spec_path.write_text(yaml.safe_dump(spec_data))
    from fractiskills.models import SiteSpec

    try:
        inventory, _ = discover_site(
            SiteSpec.load(str(spec_path)),
            output_dir=str(tmp_path / "out"),
            allow_private_hosts=True,
        )
        urls = {entry.url for entry in inventory.entries}
        assert f"{base}/blog/a" in urls
        assert f"{base}/gone" not in urls
        assert any("could not be fetched" in w for w in inventory.crawl_warnings)
    finally:
        server.stop()
