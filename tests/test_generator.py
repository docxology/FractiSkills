"""Profile compilation and augmentation generator tests."""

from __future__ import annotations

from skillarum.models import PreparedCorpus, PreparedPage

from fractiskills.generator import AugmentedGenerator, html_to_text
from fractiskills.models import BindingSpec
from fractiskills.profiles import (
    build_discovery_profile,
    build_resolve_profile,
    build_section_profiles,
    readable_name_for_path,
    slug_for_path,
)


class TestProfiles:
    def test_discovery_profile_shape(self, loaded_spec) -> None:
        profile = build_discovery_profile(loaded_spec, ("https://x.example/sitemap-page",))
        assert profile.crawl.follow_links is True
        assert profile.targets[0].urls[0] == "/"
        assert "https://x.example/sitemap-page" in profile.targets[0].urls
        assert profile.targets[0].include_prefixes == ("/",)

    def test_section_profiles_grouping(self, loaded_spec, fixture_inventory) -> None:
        inventory, _, _ = fixture_inventory
        profiles = build_section_profiles(inventory, loaded_spec)
        areas = {profile.area for profile in profiles}
        assert any(area == "Core" for area in areas)
        total_targets = sum(len(profile.targets) for profile in profiles)
        assert total_targets == len(inventory.entries)
        for profile in profiles:
            assert profile.crawl.follow_links is False
            ids = [target.id for target in profile.targets]
            assert len(ids) == len(set(ids))

    def test_resolve_profile_is_exact_single_page(self, loaded_spec) -> None:
        profile = build_resolve_profile(loaded_spec, "https://x.example/one")
        assert len(profile.targets) == 1
        assert profile.targets[0].urls == ("https://x.example/one",)
        assert profile.crawl.follow_links is False

    def test_names_and_slugs_derived_from_path(self) -> None:
        assert readable_name_for_path("/") == "Home"
        assert (
            readable_name_for_path("/ship-blog/eddy-current-mirror")
            == "Ship Blog Eddy Current Mirror"
        )
        assert readable_name_for_path("/reader.html?id=doc-one") == "Reader Doc One"
        assert slug_for_path("/reader.html?id=doc-one") == "reader-html-id-doc-one"


def _corpus(pages: tuple[PreparedPage, ...]) -> PreparedCorpus:
    return PreparedCorpus(
        profile_id="fixturesite-core",
        profile_name="Fixture Site: Core",
        target_id="reader-html-id-doc1",
        skill_name="Reader Doc1",
        pages=pages,
        area="Core",
    )


class TestAugmentedGenerator:
    def _generator(self, loaded_spec, receipts_path: str = "") -> AugmentedGenerator:
        return AugmentedGenerator(
            base_url=loaded_spec.base_url,
            bindings=loaded_spec.bindings,
            augment_timeout_seconds=10,
            allow_private_hosts=True,
            receipts_path=receipts_path,
        )

    def test_static_page_passes_through(self, loaded_spec) -> None:
        page = PreparedPage(
            url=f"{loaded_spec.base_url}blog/a",
            title="Blog A",
            headings=("Blog A",),
            text="post alpha",
            links=(),
        )
        draft = self._generator(loaded_spec).generate(_corpus((page,)))
        assert draft.metadata["fractiskills_augmentation"] == []
        assert "post alpha" in draft.body
        assert draft.name == "Reader Doc1"

    def test_dynamic_page_is_augmented(self, loaded_spec, tmp_path) -> None:
        receipts = tmp_path / "receipts.jsonl"
        page = PreparedPage(
            url=f"{loaded_spec.base_url}reader.html?id=doc1",
            title="Reader Shell",
            headings=(),
            text="Loading document...",
            links=(),
        )
        draft = self._generator(loaded_spec, str(receipts)).generate(_corpus((page,)))
        assert "Document One · Real Paper" in draft.body
        assert "Doc body line one." in draft.body
        assert "Dynamic document retrieved from" in draft.body
        receipts_list = draft.metadata["fractiskills_augmentation"]
        assert len(receipts_list) == 1
        receipt = receipts_list[0]
        assert receipt["ok"] is True
        assert receipt["title"] == "Document One · Real Paper"
        assert receipt["text_chars"] > 0
        assert receipt["content_sha256"]
        assert receipts.exists()
        assert '"ok": true' in receipts.read_text()

    def test_failed_augmentation_degrades_honestly(self, loaded_spec, httpserver) -> None:
        httpserver.expect_request("/api/broken").respond_with_json({"ok": False}, status=500)
        generator = AugmentedGenerator(
            base_url=loaded_spec.base_url,
            bindings=(BindingSpec(match_path="/broken.html", api_template="/api/broken"),),
            augment_timeout_seconds=5,
            allow_private_hosts=True,
        )
        page = PreparedPage(
            url=f"{loaded_spec.base_url}broken.html",
            title="Broken Shell",
            headings=(),
            text="Loading...",
            links=(),
        )
        draft = generator.generate(_corpus((page,)))
        receipt = draft.metadata["fractiskills_augmentation"][0]
        assert receipt["ok"] is False
        assert receipt["error"]
        assert "Loading..." in draft.body
        assert any("augmentation failed" in warning for warning in draft.metadata["warnings"])

    def test_binding_requires_same_origin(self, loaded_spec) -> None:
        generator = AugmentedGenerator(
            base_url=loaded_spec.base_url,
            bindings=(
                BindingSpec(match_path="/evil.html", api_template="https://other.example/api"),
            ),
            allow_private_hosts=True,
        )
        page = PreparedPage(
            url=f"{loaded_spec.base_url}evil.html",
            title="Evil",
            headings=(),
            text="x",
            links=(),
        )
        draft = generator.generate(_corpus((page,)))
        receipt = draft.metadata["fractiskills_augmentation"][0]
        assert receipt["ok"] is False
        assert "cross-origin" in receipt["error"]

    def test_cache_key_reflects_bindings(self, loaded_spec) -> None:
        generator = self._generator(loaded_spec)
        other = AugmentedGenerator(
            base_url=loaded_spec.base_url,
            bindings=(BindingSpec(match_path="/x", api_template="/api/x"),),
            allow_private_hosts=True,
        )
        assert generator.cache_key() != other.cache_key()
        assert generator.cache_key() == self._generator(loaded_spec).cache_key()


class TestHtmlToText:
    def test_strips_scripts_and_preserves_lines(self) -> None:
        html = "<p>One</p><script>evil()</script><br><p>Two</p><style>.x{}</style>"
        text = html_to_text(html)
        assert "One" in text and "Two" in text
        assert "evil" not in text and ".x" not in text
        assert "\n" in text
