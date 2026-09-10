"""Opt-in live tests: real site checks, gated behind FRACTISKILLS_RUN_LIVE=1."""

from __future__ import annotations

import os

import pytest

from fractiskills.discover import discover_site
from fractiskills.models import SiteSpec

pytestmark = pytest.mark.live

requires_live = pytest.mark.skipif(
    os.environ.get("FRACTISKILLS_RUN_LIVE") != "1",
    reason="live-site checks are opt-in via FRACTISKILLS_RUN_LIVE=1",
)


@requires_live
def test_live_discovery_covers_sitemap(tmp_path) -> None:
    spec = SiteSpec.load("data/sources/ssvibelandia.yaml")
    inventory, _ = discover_site(spec, output_dir=str(tmp_path / "output"))
    assert inventory.sitemap_url_count >= 50
    assert len(inventory.entries) >= inventory.sitemap_url_count
    assert inventory.incomplete is False
    assert not any("not represented" in w for w in inventory.crawl_warnings)
    sections = inventory.sections()
    assert "Interfaces" in sections and "Ship-Blog" in sections
