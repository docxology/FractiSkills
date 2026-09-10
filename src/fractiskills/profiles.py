"""Build Skillarum source profiles from the site spec and page inventory."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from skillarum.models import (
    CrawlConfig,
    ExtractionConfig,
    GenerationConfig,
    SourceProfile,
    TargetSpec,
)
from skillarum.utils import slugify

from .models import PageEntry, SiteInventory, SiteSpec


def query_identity(path: str) -> str:
    """Stable identity string for a page path, including its routing query."""
    parsed = urlparse(path)
    query = parse_qs(parsed.query)
    id_values = query.get("id")
    if id_values:
        return f"{parsed.path}?id={id_values[0]}"
    return parsed.path


def slug_for_path(path: str) -> str:
    """Stable slug identifier for one page path."""
    return slugify(query_identity(path))


def readable_name_for_path(path: str) -> str:
    """Readable, stable skill name derived from the page path (not its title)."""
    parsed = urlparse(path)
    if parsed.path in ("", "/") and not parsed.query:
        return "Home"
    words: list[str] = []
    for segment in [seg for seg in parsed.path.split("/") if seg]:
        segment = re.sub(r"\.(html?|php|aspx)$", "", segment, flags=re.IGNORECASE)
        words.extend(word.capitalize() for word in segment.split("-") if word)
    id_values = parse_qs(parsed.query).get("id")
    if id_values:
        words.extend(word.capitalize() for word in id_values[0].split("-") if word)
    return (" ".join(words) or "Page")[:80]


def _crawl_config(
    spec: SiteSpec,
    *,
    max_pages: int,
    max_requests: int,
    follow_links: bool,
    max_depth: int,
    min_delay_seconds: float,
    allow_private_hosts: bool = False,
) -> CrawlConfig:
    return CrawlConfig(
        respect_robots=True,
        same_origin_only=True,
        allow_private_hosts=allow_private_hosts,
        follow_links=follow_links,
        max_pages=max_pages,
        max_requests=max_requests,
        max_depth=max_depth,
        request_timeout_seconds=spec.crawl_request_timeout_seconds,
        min_delay_seconds=min_delay_seconds,
        max_response_bytes=spec.crawl_max_response_bytes,
        user_agent=spec.user_agent,
    )


def build_resolve_profile(
    spec: SiteSpec, url: str, *, allow_private_hosts: bool = False
) -> SourceProfile:
    """One exact-page profile that resolves a single URL's identity."""
    return SourceProfile(
        id=f"{spec.profile_id}-resolve",
        name=f"{spec.profile_name}: resolve one URL",
        base_url=spec.base_url,
        area="",
        crawl=_crawl_config(
            spec,
            max_pages=1,
            max_requests=12,
            follow_links=False,
            max_depth=0,
            min_delay_seconds=0.0,
            allow_private_hosts=allow_private_hosts,
        ),
        extraction=ExtractionConfig(max_chars_per_page=spec.max_chars_per_page),
        generation=GenerationConfig(backend="deterministic"),
        targets=(TargetSpec(id="resolve", name="Resolve", urls=(url,)),),
    )


def build_discovery_profile(
    spec: SiteSpec,
    sitemap_urls: tuple[str, ...] = (),
    allow_private_hosts: bool = False,
) -> SourceProfile:
    """One bounded BFS profile whose accepted pages become the inventory."""
    start_urls = ("/", *sitemap_urls)
    return SourceProfile(
        id=f"{spec.profile_id}-discovery",
        name=f"{spec.profile_name}: discovery crawl",
        base_url=spec.base_url,
        area="",
        crawl=_crawl_config(
            spec,
            max_pages=spec.discovery_max_pages,
            max_requests=spec.discovery_max_requests,
            follow_links=True,
            max_depth=spec.discovery_max_depth,
            min_delay_seconds=spec.discovery_min_delay_seconds,
            allow_private_hosts=allow_private_hosts,
        ),
        extraction=ExtractionConfig(max_chars_per_page=spec.max_chars_per_page),
        generation=GenerationConfig(backend="deterministic"),
        targets=(
            TargetSpec(
                id="discovery",
                name="Discovery Crawl",
                urls=start_urls,
                include_prefixes=("/",),
            ),
        ),
    )


def build_section_profiles(
    inventory: SiteInventory,
    spec: SiteSpec,
    *,
    allow_private_hosts: bool = False,
) -> list[SourceProfile]:
    """One profile per site section; one exact-page target per discovered page."""
    profiles: list[SourceProfile] = []
    for section, entries in inventory.sections().items():
        targets = tuple(
            TargetSpec(
                id=slug_for_path(entry.path),
                name=readable_name_for_path(entry.path),
                urls=(entry.url,),
            )
            for entry in entries
        )
        page_count = len(targets)
        profiles.append(
            SourceProfile(
                id=f"{spec.profile_id}-{slugify(section)}",
                name=f"{spec.profile_name}: {section}",
                base_url=spec.base_url,
                area=section,
                crawl=_crawl_config(
                    spec,
                    max_pages=page_count + 5,
                    max_requests=page_count * 3 + 20,
                    follow_links=False,
                    max_depth=0,
                    min_delay_seconds=spec.crawl_min_delay_seconds,
                    allow_private_hosts=allow_private_hosts,
                ),
                extraction=ExtractionConfig(max_chars_per_page=spec.max_chars_per_page),
                generation=GenerationConfig(backend="deterministic"),
                targets=targets,
            )
        )
    return profiles


def target_for_entry(entry: PageEntry) -> TargetSpec:
    """The exact-page target contract for one inventory entry."""
    return TargetSpec(
        id=slug_for_path(entry.path),
        name=readable_name_for_path(entry.path),
        urls=(entry.url,),
    )
