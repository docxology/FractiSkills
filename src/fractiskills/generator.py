"""Deterministic extraction plus same-origin dynamic-document augmentation.

The site renders several pages client-side: their static HTML is a thin shell
("Loading document…") and the real document arrives from a same-origin JSON
API declared in the site spec's ``bindings``. ``AugmentedGenerator`` keeps
Skillarum's deterministic body structure and, for pages with a matching
binding, fetches the declared JSON document and prepends its extracted text
with full provenance (API URL, timestamp, ETag, content hash). Failures are
recorded as receipts and warnings — never silently dropped and never faked.

This module is a declared FractiSkills network boundary: it performs GET
requests only, to same-origin API paths resolved from the reviewed site spec.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from skillarum.generators import DeterministicGenerator
from skillarum.models import PreparedCorpus, PreparedPage, RetryConfig, SkillDraft
from skillarum.urls import is_public_http_url, same_origin
from skillarum.utils import sha256_bytes, sha256_json

from .models import BindingSpec

_BLOCK_ELEMENTS = {
    "p",
    "div",
    "br",
    "li",
    "tr",
    "ul",
    "ol",
    "table",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "pre",
    "section",
    "article",
}


@dataclass(frozen=True)
class AugmentationReceipt:
    """Provenance for one dynamic-document augmentation attempt."""

    page_url: str
    api_url: str
    ok: bool
    status_code: int = 0
    title: str | None = None
    text_chars: int = 0
    content_sha256: str = ""
    etag: str | None = None
    fetched_at: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize with every provenance field present (empty-string
        sentinels for absent status/etag), matching the receipts JSONL."""
        return {
            "page_url": self.page_url,
            "api_url": self.api_url,
            "ok": self.ok,
            "status_code": self.status_code,
            "title": self.title,
            "text_chars": self.text_chars,
            "content_sha256": self.content_sha256,
            "etag": self.etag,
            "fetched_at": self.fetched_at,
            "error": self.error,
        }


def html_to_text(html: str) -> str:
    """Extract line-structured text from a document HTML fragment.

    Block-level elements become line breaks; inline elements stay in one
    line so ``<strong>`` and similar tags do not fragment sentences.
    """
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style"]):
        node.decompose()
    for element in soup.find_all(True):
        if element.name in _BLOCK_ELEMENTS:
            element.append("\n")
    text = soup.get_text(" ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


@dataclass
class AugmentedGenerator(DeterministicGenerator):
    """Deterministic skill bodies with declared same-origin API augmentation."""

    name: str = "fractiskills-augmented-deterministic"
    requires_retrieval: bool = True
    base_url: str = ""
    bindings: tuple[BindingSpec, ...] = ()
    augment_timeout_seconds: float = 30.0
    allow_private_hosts: bool = False
    receipts_path: str = ""
    retry: RetryConfig = field(default_factory=RetryConfig)

    def cache_key(self) -> str:
        """Version-stamped digest of the serialized bindings so augmentation
        config changes invalidate cached drafts."""
        digest = sha256_json([binding.to_dict() for binding in self.bindings])
        return f"fractiskills-augmented-v1:{digest}"

    def binding_for(self, page_url: str) -> BindingSpec | None:
        """Return the first declared binding whose match_path equals or
        prefixes the page URL path; ``None`` for static-only pages."""
        path = urlparse(page_url).path
        for binding in self.bindings:
            if path == binding.match_path or path.startswith(binding.match_path):
                return binding
        return None

    def fetch_document(self, api_url: str) -> tuple[dict[str, Any], int, str | None]:
        """GET one same-origin JSON document. Returns (payload, status, etag)."""
        if not is_public_http_url(
            api_url, allow_private=self.allow_private_hosts, resolve_dns=True
        ):
            raise ValueError(f"augmentation URL rejected as unsafe: {api_url}")
        if not same_origin(self.base_url, api_url):
            raise ValueError(f"augmentation URL rejected as cross-origin: {api_url}")
        with httpx.Client(
            timeout=self.augment_timeout_seconds,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            response = client.get(api_url)
        if response.status_code != 200:
            raise ValueError(f"augmentation API returned HTTP {response.status_code}")
        content_type = response.headers.get("content-type", "").lower()
        if "json" not in content_type:
            raise ValueError(f"augmentation API returned non-JSON content ({content_type})")
        payload = json.loads(response.content.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("augmentation API payload is not a JSON object")
        return payload, response.status_code, response.headers.get("etag")

    def _generate_once(self, corpus: PreparedCorpus) -> SkillDraft:
        """Augment matching corpus pages via declared same-origin GETs,
        record one receipt per attempt, then delegate to the deterministic
        generator and attach the receipts to ``draft.metadata``."""
        augmented_pages: list[PreparedPage] = []
        receipts: list[dict[str, Any]] = []
        failure_warnings: list[str] = []
        for page in corpus.pages:
            binding = self.binding_for(page.url)
            if binding is None:
                augmented_pages.append(page)
                continue
            api_url = binding.api_for(page.url)
            absolute_api = api_url if "://" in api_url else f"{self.base_url.rstrip('/')}{api_url}"
            try:
                payload, status_code, etag = self.fetch_document(absolute_api)
                document_html = str(payload.get("html") or "")
                document_title = str(payload.get("title") or "").strip()
                document_text = html_to_text(document_html) if document_html else ""
                if not document_text:
                    raise ValueError("augmentation API payload carried no document text")
                fetched_at = datetime.now(timezone.utc).isoformat()
                content_sha256 = sha256_bytes(document_text.encode("utf-8"))
                header = (
                    f"Dynamic document retrieved from {absolute_api} at {fetched_at} "
                    f"(HTTP {status_code}, content sha256 {content_sha256}"
                    + (f", ETag {etag}" if etag else "")
                    + ")."
                )
                receipts.append(
                    AugmentationReceipt(
                        page_url=page.url,
                        api_url=absolute_api,
                        ok=True,
                        status_code=status_code,
                        title=document_title or None,
                        text_chars=len(document_text),
                        content_sha256=content_sha256,
                        etag=etag,
                        fetched_at=fetched_at,
                    ).to_dict()
                )
                augmented_pages.append(
                    replace(
                        page,
                        title=document_title or page.title,
                        text=f"{header}\n\n{document_text}\n\n[Static shell text:]\n{page.text}",
                        warnings=page.warnings + ("fractiskills:augmented-from-api",),
                    )
                )
            except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
                error = f"{type(exc).__name__}: {exc}"
                receipts.append(
                    AugmentationReceipt(
                        page_url=page.url,
                        api_url=absolute_api,
                        ok=False,
                        error=error,
                        fetched_at=datetime.now(timezone.utc).isoformat(),
                    ).to_dict()
                )
                failure_warnings.append(f"augmentation failed for {page.url}: {error}")
                augmented_pages.append(page)
        augmented_corpus = replace(
            corpus,
            pages=tuple(augmented_pages),
            warnings=corpus.warnings + tuple(failure_warnings),
        )
        draft = super()._generate_once(augmented_corpus)
        metadata = {**draft.metadata, "fractiskills_augmentation": receipts}
        augmented_draft = replace(draft, metadata=metadata)
        if self.receipts_path:
            self._append_receipts(receipts)
        return augmented_draft

    def _append_receipts(self, receipts: list[dict[str, Any]]) -> None:
        """Append each receipt to ``receipts_path`` as one sorted-key JSON
        line; no-op on an empty list."""
        if not receipts:
            return
        with open(self.receipts_path, "a", encoding="utf-8") as handle:
            for receipt in receipts:
                handle.write(json.dumps(receipt, sort_keys=True) + "\n")
