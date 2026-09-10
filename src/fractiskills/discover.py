"""Page discovery: sitemap enumeration plus a bounded, robots-respecting crawl.

The discovery boundary owns these network touches:

1. ``GET <sitemap_url>`` — the site declares its own sitemap; parsed as XML.
2. One bounded breadth-first crawl through Skillarum's ``WebsiteCrawler``
   (same-origin only, robots respected, streamed, rate-limited) seeded with
   ``/`` and every sitemap URL so redirect aliases resolve to their canonical
   page during the union.
3. One exact-page resolution fetch per sitemap URL the BFS could not accept —
   the site declares canonical duplicates (``<link rel="canonical">``), so a
   sitemap URL that duplicates an accepted page becomes an alias of it, and
   only genuinely unfetchable URLs are recorded as notes.

Everything else in FractiSkills consumes the persisted inventory.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from skillarum.crawler import CrawlError, WebsiteCrawler
from skillarum.urls import normalize_url, resolve_url, same_origin

from .models import PageEntry, SiteInventory, SiteSpec, write_json_atomic
from .profiles import (
    build_discovery_profile,
    build_resolve_profile,
    slug_for_path,
)

_SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def fetch_sitemap_entries(
    sitemap_url: str,
    *,
    base_url: str,
    user_agent: str,
    timeout_seconds: float = 30.0,
) -> tuple[list[dict[str, object]], list[str]]:
    """Fetch and parse a sitemap into normalized, same-origin URL records."""
    notes: list[str] = []
    with httpx.Client(
        headers={"User-Agent": user_agent},
        timeout=timeout_seconds,
        follow_redirects=False,
        trust_env=False,
    ) as client:
        response = client.get(sitemap_url)
    if response.status_code in {301, 302, 303, 307, 308}:
        location = response.headers.get("location", "")
        if location:
            sitemap_url = resolve_url(sitemap_url, location)
            with httpx.Client(
                headers={"User-Agent": user_agent},
                timeout=timeout_seconds,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = client.get(sitemap_url)
    response.raise_for_status()
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        raise ValueError(f"sitemap is not parseable XML: {sitemap_url}: {exc}") from exc
    entries: list[dict[str, object]] = []
    for node in root.iter():
        if not node.tag.endswith("url"):
            continue
        loc_node = node.find(f"{_SITEMAP_NS}loc")
        if loc_node is None or not (loc_node.text or "").strip():
            continue
        try:
            loc = normalize_url((loc_node.text or "").strip())
        except ValueError:
            notes.append(f"sitemap URL rejected as unsafe: {loc_node.text!r}")
            continue
        if not same_origin(base_url, loc):
            notes.append(f"sitemap URL rejected as cross-origin: {loc}")
            continue
        priority_node = node.find(f"{_SITEMAP_NS}priority")
        changefreq_node = node.find(f"{_SITEMAP_NS}changefreq")
        priority: float | None = None
        if priority_node is not None and (priority_node.text or "").strip():
            try:
                priority = float(priority_node.text or "")
            except ValueError:
                notes.append(f"sitemap URL has non-numeric priority: {loc}")
        entries.append(
            {
                "url": loc,
                "priority": priority,
                "changefreq": (changefreq_node.text or "").strip() or None
                if changefreq_node is not None
                else None,
            }
        )
    return entries, notes


def _resolve_alias_chain(alias_map: dict[str, str], url: str) -> str:
    seen: set[str] = set()
    current = url
    while current in alias_map and current not in seen:
        seen.add(current)
        current = alias_map[current]
    return current


def section_for_path(path: str) -> str:
    """Derive the skill area (section) from a site path.

    Multi-segment paths take their area from the first path segment (with
    ``/interfaces/nesting/`` promoted to its own area); single-segment pages
    belong to the deck-level ``Core`` area.
    """
    from skillarum.utils import artifact_name

    parts = [part for part in urlparse(path).path.split("/") if part]
    if not parts or len(parts) == 1:
        return "Core"
    if parts[0] == "interfaces":
        if parts[1] == "nesting":
            return "Nesting"
        return "Interfaces"
    return artifact_name(parts[0].replace("-", " ").title())


def _page_info(page) -> dict[str, object]:  # noqa: ANN001 - PageRecord contract
    return {
        "title": page.title,
        "depth": int(page.depth),
        "links": tuple(page.links),
    }


def discover_site(
    spec: SiteSpec,
    *,
    output_dir: str,
    allow_private_hosts: bool = False,
) -> tuple[SiteInventory, str]:
    """Run discovery and persist the inventory.

    Returns the inventory and the path of the persisted JSON file.
    """
    sitemap_entries, sitemap_notes = fetch_sitemap_entries(
        spec.sitemap_url,
        base_url=spec.base_url,
        user_agent=spec.user_agent,
    )
    sitemap_urls = [str(entry["url"]) for entry in sitemap_entries]
    sitemap_meta = {str(entry["url"]): entry for entry in sitemap_entries}

    profile = build_discovery_profile(spec, tuple(sitemap_urls), allow_private_hosts)
    with WebsiteCrawler(profile) as crawler:
        bundle = crawler.crawl(profile.targets[0])
        events = [dict(event) for event in bundle.events]
        fetch_entries = dict(crawler.fetch_cache)

    alias_map: dict[str, str] = {}
    for event in events:
        if event.get("kind") == "redirect":
            source, location = str(event.get("url", "")), str(event.get("location", ""))
            if source and location:
                alias_map.setdefault(source, location)

    pages: dict[str, dict[str, object]] = {}
    for page in bundle.pages:
        identity = str(page.canonical_url or page.final_url)
        current = pages.get(identity)
        if current is None:
            pages[identity] = _page_info(page)
            continue
        if page.title and not current.get("title"):
            current["title"] = page.title
        current["depth"] = min(int(current["depth"]), int(page.depth))
        current["links"] = tuple(sorted(set(current["links"]) | set(page.links)))  # type: ignore[union-attr]

    accepted_final_urls = {str(page.final_url) for page in bundle.pages} | {
        str(page.canonical_url) for page in bundle.pages if page.canonical_url
    }
    for page in bundle.pages:
        identity = str(page.canonical_url or page.final_url)
        requested = str(page.requested_url)
        if requested != identity:
            # Any accepted page reached under a different URL spelling (a
            # canonical duplicate, redirect stub, or trailing-slash variant)
            # becomes an alias of the identity it was accepted as.
            alias_map.setdefault(requested, identity)

    # Duplicate-rejected requests carry their canonical only inside the
    # crawler's fetch cache; recover it so canonical-declared duplicates
    # (a landing page reached under two spellings) fold onto the page they
    # duplicate.
    from bs4 import BeautifulSoup

    for event in events:
        if event.get("kind") != "duplicate":
            continue
        url = str(event.get("url", ""))
        if not url or url in alias_map or url in pages:
            continue
        entry = fetch_entries.get(url)
        if entry is None or not entry.content:
            continue
        soup = BeautifulSoup(entry.content, "html.parser")
        canonical_node = soup.select_one('link[rel~="canonical"][href]')
        if canonical_node is None:
            continue
        try:
            candidate = resolve_url(url, str(canonical_node.get("href")))
        except (TypeError, ValueError):
            continue
        if candidate in pages:
            alias_map.setdefault(url, candidate)

    for requested in {str(page.requested_url) for page in bundle.pages}:
        if requested in sitemap_urls:
            resolved = _resolve_alias_chain(alias_map, requested)
            if resolved != requested:
                alias_map.setdefault(requested, resolved)

    # Resolve sitemap URLs the BFS could not accept: each is either a declared
    # canonical duplicate (an alias of an accepted page) or a page of its own.
    covered_sitemap = {url for url in sitemap_urls if url in alias_map or url in pages}
    uncovered = [
        url
        for url in sitemap_urls
        if url not in covered_sitemap and _resolve_alias_chain(alias_map, url) not in pages
    ]
    for url in uncovered:
        resolve_profile = build_resolve_profile(spec, url, allow_private_hosts=allow_private_hosts)
        try:
            with WebsiteCrawler(resolve_profile) as crawler:
                resolve_bundle = crawler.crawl(resolve_profile.targets[0])
        except (CrawlError, httpx.HTTPError, ValueError) as exc:
            sitemap_notes.append(f"sitemap URL could not be fetched: {url}: {exc}")
            continue
        if not resolve_bundle.pages:
            sitemap_notes.append(f"sitemap URL produced no page: {url}")
            continue
        page = resolve_bundle.pages[0]
        identity = str(page.canonical_url or page.final_url)
        if identity not in pages:
            pages[identity] = _page_info(page)
            accepted_final_urls.add(str(page.final_url))
        alias_map.setdefault(url, identity)

    resolved_aliases = {url: _resolve_alias_chain(alias_map, url) for url in alias_map}
    entries: list[PageEntry] = []
    for identity, info in sorted(pages.items()):
        identity = str(identity)
        parsed = urlparse(identity)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        aliases = sorted(
            url
            for url, target in resolved_aliases.items()
            if target == identity and url != identity
        )
        sitemap_hits = sorted(url for url in sitemap_urls if url == identity or url in aliases)
        via_sitemap = bool(sitemap_hits)
        via_crawl = identity in accepted_final_urls
        if not (via_sitemap or via_crawl):
            continue
        meta = sitemap_meta.get(identity)
        if meta is None:
            for url in sitemap_hits:
                if url in sitemap_meta:
                    meta = sitemap_meta[url]
                    break
        for url in sitemap_hits:
            covered_sitemap.add(url)
        entries.append(
            PageEntry(
                url=identity,
                path=path,
                section=section_for_path(path),
                via_sitemap=via_sitemap,
                via_crawl=via_crawl,
                title=str(info["title"]) if info["title"] else None,
                sitemap_priority=meta["priority"] if meta else None,  # type: ignore[arg-type]
                sitemap_changefreq=str(meta["changefreq"])  # type: ignore[arg-type]
                if meta and meta.get("changefreq")  # type: ignore[union-attr]
                else None,
                crawl_depth=int(info["depth"]),  # type: ignore[arg-type]
                links=tuple(str(link) for link in info["links"]),  # type: ignore[arg-type]
                alias_urls=tuple(aliases),
            )
        )
    for url in sitemap_urls:
        if url not in covered_sitemap:
            sitemap_notes.append(f"sitemap URL not represented in inventory: {url}")

    # Merge entries whose path identity collides after query routing (for
    # example a UI-flag query on the same route): the first URL stays the
    # page, the others become recorded aliases of it.
    by_slug: dict[str, PageEntry] = {}
    merged_entries: list[PageEntry] = []
    for entry in entries:
        slug = slug_for_path(entry.path)
        keeper = by_slug.get(slug)
        if keeper is None:
            by_slug[slug] = entry
            merged_entries.append(entry)
            continue
        alias = entry.url
        sitemap_notes.append(f"path alias merged: {alias} -> {keeper.url}")
        merged_aliases = set(keeper.alias_urls) | {alias} | set(entry.alias_urls)
        merged_aliases.discard(keeper.url)
        depth_candidates = [d for d in (keeper.crawl_depth, entry.crawl_depth) if d is not None]
        replacement = PageEntry(
            url=keeper.url,
            path=keeper.path,
            section=keeper.section,
            via_sitemap=keeper.via_sitemap or entry.via_sitemap,
            via_crawl=keeper.via_crawl or entry.via_crawl,
            title=keeper.title or entry.title,
            sitemap_priority=(
                keeper.sitemap_priority
                if keeper.sitemap_priority is not None
                else entry.sitemap_priority
            ),
            sitemap_changefreq=keeper.sitemap_changefreq or entry.sitemap_changefreq,
            crawl_depth=min(depth_candidates) if depth_candidates else None,
            links=tuple(sorted(set(keeper.links) | set(entry.links))),
            alias_urls=tuple(sorted(merged_aliases)),
        )
        by_slug[slug] = replacement
        merged_entries[merged_entries.index(keeper)] = replacement

    inventory = SiteInventory(
        base_url=spec.base_url,
        sitemap_url=spec.sitemap_url,
        generated_at=datetime.now(timezone.utc).isoformat(),
        entries=tuple(merged_entries),
        sitemap_url_count=len(sitemap_urls),
        crawl_accepted_count=len(bundle.pages),
        crawl_warnings=tuple(dict.fromkeys(bundle.warnings)) + tuple(sitemap_notes),
        incomplete=any("limit reached" in warning for warning in bundle.warnings),
    )
    output_path = f"{output_dir}/data/inventory.json"
    write_json_atomic(output_path, inventory.to_dict())
    return inventory, output_path


__all__ = [
    "discover_site",
    "fetch_sitemap_entries",
    "section_for_path",
]
