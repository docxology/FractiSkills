"""Unit tests for specs, models, and sectioning rules."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from fractiskills.discover import section_for_path
from fractiskills.models import (
    BindingSpec,
    PageEntry,
    RenderSummary,
    SectionRun,
    SiteInventory,
    SiteSpec,
)


class TestSiteSpec:
    def test_load_valid_spec(self, spec_file: Path) -> None:
        spec = SiteSpec.load(str(spec_file))
        assert spec.profile_id == "fixturesite"
        assert spec.base_url.startswith("http://127.0.0.1:")
        assert len(spec.bindings) == 2

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.safe_dump({"id": "x", "name": "X"}))
        with pytest.raises(ValueError, match="base_url is required"):
            SiteSpec.load(str(path))

    def test_binding_paths_must_be_absolute(self) -> None:
        with pytest.raises(ValueError, match="match_path"):
            BindingSpec.from_mapping({"match_path": "blog", "api_template": "/api"})
        with pytest.raises(ValueError, match="api_template"):
            BindingSpec.from_mapping({"match_path": "/blog", "api_template": "api"})


class TestBindingPlaceholders:
    def test_id_placeholder_uses_query(self) -> None:
        binding = BindingSpec(match_path="/reader.html", api_template="/api/whitepaper?id={id}")
        assert binding.api_for("/reader.html?id=doc-one") == "/api/whitepaper?id=doc-one"

    def test_id_placeholder_without_query_is_empty(self) -> None:
        binding = BindingSpec(match_path="/reader.html", api_template="/api/whitepaper?id={id}")
        assert binding.api_for("/reader.html") == "/api/whitepaper?id="

    def test_last_segment_placeholder(self) -> None:
        binding = BindingSpec(
            match_path="/whitepaper/", api_template="/api/whitepaper?id={last_segment}"
        )
        assert (
            binding.api_for("/whitepaper/syn-sun-wavefield")
            == "/api/whitepaper?id=syn-sun-wavefield"
        )

    def test_path_placeholder(self) -> None:
        binding = BindingSpec(match_path="/x", api_template="/api/p{path}")
        assert binding.api_for("/x/y") == "/api/p/x/y"


class TestSectioning:
    def test_root_and_single_segment_are_core(self) -> None:
        assert section_for_path("/") == "Core"
        assert section_for_path("/questfest") == "Core"
        assert section_for_path("/bulletin-board") == "Core"

    def test_first_segment_sections(self) -> None:
        assert section_for_path("/journey/boriken-convergence") == "Journey"
        assert section_for_path("/ship-blog/eddy-current-mirror") == "Ship-Blog"
        assert section_for_path("/whitepaper/syn-sun") == "Whitepaper"
        assert section_for_path("/special-projects/erdos-audit") == "Special-Projects"

    def test_nesting_promoted_over_interfaces(self) -> None:
        assert section_for_path("/interfaces/nesting/nest-sing13.html") == "Nesting"
        assert section_for_path("/interfaces/valetpru-agent-mode.html") == "Interfaces"


class TestModelRoundtrips:
    def test_page_entry_roundtrip(self) -> None:
        entry = PageEntry(
            url="https://x.example/blog/a",
            path="/blog/a",
            section="Blog",
            via_sitemap=True,
            via_crawl=True,
            title="A",
            links=("https://x.example/",),
            alias_urls=("https://x.example/old-a",),
        )
        assert PageEntry.from_dict(entry.to_dict()) == entry

    def test_inventory_sections_ordered_and_grouped(self) -> None:
        entries = (
            PageEntry(url="https://x/a", path="/a", section="Core"),
            PageEntry(url="https://x/b/c", path="/b/c", section="Bee"),
            PageEntry(url="https://x/d", path="/d", section="Core"),
        )
        inventory = SiteInventory(
            base_url="https://x",
            sitemap_url="https://x/sitemap.xml",
            generated_at="2026-09-10T00:00:00+00:00",
            entries=entries,
        )
        sections = inventory.sections()
        assert set(sections) == {"Core", "Bee"}
        assert len(sections["Core"]) == 2
        assert SiteInventory.from_dict(inventory.to_dict()) == inventory

    def test_render_summary_roundtrip(self) -> None:
        summary = RenderSummary(
            generated_at="2026-09-10T00:00:00+00:00",
            backend="deterministic",
            evidence_origin="live",
            runs=(
                SectionRun(
                    section="Core",
                    profile_id="p-core",
                    run_id="p-core--abc",
                    rendered=("/s/K/SKILL.md",),
                    target_count=1,
                ),
            ),
        )
        assert RenderSummary.from_dict(summary.to_dict()) == summary
