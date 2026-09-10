"""Typed contracts for the site spec, page inventory, and render summaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml


def _strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class BindingSpec:
    """One declared dynamic-content binding for the site.

    ``api_template`` is a same-origin path (optionally containing ``{id}`` or
    ``{path}`` placeholders) whose JSON response carries the real document for
    pages that are rendered client-side.
    """

    match_path: str
    api_template: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> BindingSpec:
        match_path = str(value.get("match_path", "")).strip()
        api_template = str(value.get("api_template", "")).strip()
        if not match_path.startswith("/"):
            raise ValueError("binding.match_path must be an absolute site path")
        if not api_template.startswith("/"):
            raise ValueError("binding.api_template must be an absolute site path")
        return cls(match_path=match_path, api_template=api_template)

    def api_for(self, path: str) -> str:
        """Return the API path for one page path, filling placeholders.

        Supported placeholders: ``{id}`` (the page's ``?id=`` query value),
        ``{path}`` (the page path), and ``{last_segment}`` (the final path
        segment).
        """
        parsed = urlparse(path)
        api = self.api_template
        id_values = parse_qs(parsed.query).get("id")
        if "{id}" in api:
            api = api.replace("{id}", id_values[0] if id_values else "")
        api = api.replace("{path}", parsed.path)
        if "{last_segment}" in api:
            segments = [part for part in parsed.path.split("/") if part]
            api = api.replace("{last_segment}", segments[-1] if segments else "")
        return api

    def to_dict(self) -> dict[str, Any]:
        return {"match_path": self.match_path, "api_template": self.api_template}


@dataclass(frozen=True)
class SiteSpec:
    profile_id: str
    profile_name: str
    base_url: str
    sitemap_url: str
    user_agent: str
    discovery_max_pages: int = 600
    discovery_max_requests: int = 2500
    discovery_max_depth: int = 5
    discovery_min_delay_seconds: float = 0.25
    crawl_min_delay_seconds: float = 0.5
    crawl_request_timeout_seconds: float = 30.0
    crawl_max_response_bytes: int = 3_000_000
    max_chars_per_page: int = 60_000
    augment_timeout_seconds: float = 30.0
    bindings: tuple[BindingSpec, ...] = ()

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> SiteSpec:
        data = dict(value)
        bindings = tuple(BindingSpec.from_mapping(item) for item in (data.get("bindings") or []))
        spec = cls(
            profile_id=str(data.get("id", "")).strip(),
            profile_name=str(data.get("name", "")).strip(),
            base_url=str(data.get("base_url", "")).strip(),
            sitemap_url=str(data.get("sitemap_url", "")).strip(),
            user_agent=str(
                data.get(
                    "user_agent",
                    "FractiSkills/0.1 (+https://github.com/docxology/FractiSkills)",
                )
            ),
            discovery_max_pages=int(data.get("discovery", {}).get("max_pages", 600)),
            discovery_max_requests=int(data.get("discovery", {}).get("max_requests", 2500)),
            discovery_max_depth=int(data.get("discovery", {}).get("max_depth", 5)),
            discovery_min_delay_seconds=float(
                data.get("discovery", {}).get("min_delay_seconds", 0.25)
            ),
            crawl_min_delay_seconds=float(data.get("crawl", {}).get("min_delay_seconds", 0.5)),
            crawl_request_timeout_seconds=float(
                data.get("crawl", {}).get("request_timeout_seconds", 30.0)
            ),
            crawl_max_response_bytes=int(
                data.get("crawl", {}).get("max_response_bytes", 3_000_000)
            ),
            max_chars_per_page=int(data.get("extraction", {}).get("max_chars_per_page", 60_000)),
            augment_timeout_seconds=float(data.get("augment", {}).get("timeout_seconds", 30.0)),
            bindings=bindings,
        )
        for name in ("profile_id", "profile_name", "base_url", "sitemap_url"):
            if not getattr(spec, name):
                raise ValueError(f"site spec field {name} is required")
        return spec

    @classmethod
    def load(cls, path: str) -> SiteSpec:
        with open(path, encoding="utf-8") as handle:
            value = yaml.safe_load(handle) or {}
        if not isinstance(value, dict):
            raise ValueError(f"site spec must contain a mapping: {path}")
        return cls.from_mapping(value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_name": self.profile_name,
            "base_url": self.base_url,
            "sitemap_url": self.sitemap_url,
            "user_agent": self.user_agent,
            "discovery": {
                "max_pages": self.discovery_max_pages,
                "max_requests": self.discovery_max_requests,
                "max_depth": self.discovery_max_depth,
                "min_delay_seconds": self.discovery_min_delay_seconds,
            },
            "crawl": {
                "min_delay_seconds": self.crawl_min_delay_seconds,
                "request_timeout_seconds": self.crawl_request_timeout_seconds,
                "max_response_bytes": self.crawl_max_response_bytes,
            },
            "extraction": {"max_chars_per_page": self.max_chars_per_page},
            "augment": {"timeout_seconds": self.augment_timeout_seconds},
            "bindings": [binding.to_dict() for binding in self.bindings],
        }


@dataclass(frozen=True)
class PageEntry:
    """One discovered page of the site inventory."""

    url: str
    path: str
    section: str
    via_sitemap: bool = False
    via_crawl: bool = False
    title: str | None = None
    sitemap_priority: float | None = None
    sitemap_changefreq: str | None = None
    crawl_depth: int | None = None
    links: tuple[str, ...] = ()
    alias_urls: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> PageEntry:
        return cls(
            url=str(value["url"]),
            path=str(value["path"]),
            section=str(value["section"]),
            via_sitemap=bool(value.get("via_sitemap", False)),
            via_crawl=bool(value.get("via_crawl", False)),
            title=value.get("title"),
            sitemap_priority=value.get("sitemap_priority"),
            sitemap_changefreq=value.get("sitemap_changefreq"),
            crawl_depth=value.get("crawl_depth"),
            links=tuple(str(link) for link in value.get("links", ())),
            alias_urls=tuple(str(item) for item in value.get("alias_urls", ())),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "path": self.path,
            "section": self.section,
            "via_sitemap": self.via_sitemap,
            "via_crawl": self.via_crawl,
            "title": self.title,
            "sitemap_priority": self.sitemap_priority,
            "sitemap_changefreq": self.sitemap_changefreq,
            "crawl_depth": self.crawl_depth,
            "links": list(self.links),
            "alias_urls": list(self.alias_urls),
        }


@dataclass(frozen=True)
class SiteInventory:
    """The complete discovered page set for one origin."""

    base_url: str
    sitemap_url: str
    generated_at: str
    entries: tuple[PageEntry, ...]
    sitemap_url_count: int = 0
    crawl_accepted_count: int = 0
    crawl_warnings: tuple[str, ...] = ()
    incomplete: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> SiteInventory:
        return cls(
            base_url=str(value["base_url"]),
            sitemap_url=str(value["sitemap_url"]),
            generated_at=str(value["generated_at"]),
            entries=tuple(PageEntry.from_dict(item) for item in value["entries"]),
            sitemap_url_count=int(value.get("sitemap_url_count", 0)),
            crawl_accepted_count=int(value.get("crawl_accepted_count", 0)),
            crawl_warnings=tuple(str(w) for w in value.get("crawl_warnings", ())),
            incomplete=bool(value.get("incomplete", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "sitemap_url": self.sitemap_url,
            "generated_at": self.generated_at,
            "entries": [entry.to_dict() for entry in self.entries],
            "sitemap_url_count": self.sitemap_url_count,
            "crawl_accepted_count": self.crawl_accepted_count,
            "crawl_warnings": list(self.crawl_warnings),
            "incomplete": self.incomplete,
        }

    def sections(self) -> dict[str, tuple[PageEntry, ...]]:
        """Group entries into an ordered mapping keyed by section name."""
        grouped: dict[str, list[PageEntry]] = {}
        for entry in self.entries:
            grouped.setdefault(entry.section, []).append(entry)
        return {name: tuple(items) for name, items in grouped.items()}


@dataclass(frozen=True)
class SectionRun:
    """Outcome of rendering one section profile."""

    section: str
    profile_id: str
    run_id: str
    rendered: tuple[str, ...] = ()
    target_count: int = 0
    ok: bool = True
    error: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> SectionRun:
        return cls(
            section=str(value["section"]),
            profile_id=str(value["profile_id"]),
            run_id=str(value["run_id"]),
            rendered=tuple(str(item) for item in value.get("rendered", ())),
            target_count=int(value.get("target_count", 0)),
            ok=bool(value.get("ok", True)),
            error=value.get("error"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "profile_id": self.profile_id,
            "run_id": self.run_id,
            "rendered": list(self.rendered),
            "target_count": self.target_count,
            "ok": self.ok,
            "error": self.error,
        }


@dataclass(frozen=True)
class RenderSummary:
    """All section runs for one render invocation."""

    generated_at: str
    backend: str
    evidence_origin: str
    runs: tuple[SectionRun, ...] = ()
    profile_dir: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> RenderSummary:
        return cls(
            generated_at=str(value["generated_at"]),
            backend=str(value["backend"]),
            evidence_origin=str(value["evidence_origin"]),
            runs=tuple(SectionRun.from_dict(item) for item in value.get("runs", ())),
            profile_dir=str(value.get("profile_dir", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "backend": self.backend,
            "evidence_origin": self.evidence_origin,
            "runs": [run.to_dict() for run in self.runs],
            "profile_dir": self.profile_dir,
        }


def write_json_atomic(path: str, value: Any) -> None:
    """Persist JSON with an atomic replace so readers never see a torn file."""
    import json
    import os
    import tempfile

    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=directory, delete=False, suffix=".tmp"
    )
    try:
        json.dump(value, handle, indent=1, sort_keys=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        os.replace(handle.name, path)
    finally:
        if os.path.exists(handle.name):
            os.unlink(handle.name)


def load_json(path: str) -> Any:
    import json

    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_text_atomic(path: str, text: str) -> None:
    """Persist text with an atomic replace."""
    import os
    import tempfile

    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=directory, delete=False, suffix=".tmp"
    )
    try:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
        os.replace(handle.name, path)
    finally:
        if os.path.exists(handle.name):
            os.unlink(handle.name)
