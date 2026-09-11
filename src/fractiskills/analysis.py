"""Research aggregation over the inventory, run manifests, and rendered skills.

Pure offline layer: reads persisted artifacts, never acquires pages.
"""

from __future__ import annotations

import csv
import json
import re
import statistics
from pathlib import Path

from .models import SiteInventory, load_json, write_json_atomic

_FRONTMATTER_DESCRIPTION = re.compile(
    r"(?s)\A---\s*\n.*?^description:\s*(.+?)\s*\n.*?^---", re.MULTILINE
)


def _skill_frontmatter_description(skill_md: str) -> str:
    """Extract the frontmatter ``description:`` value from a rendered
    SKILL.md; empty string when absent."""
    match = _FRONTMATTER_DESCRIPTION.search(skill_md)
    if not match:
        return ""
    return match.group(1).strip().strip("\"'")


def _iter_published_skills(skills_dir: str):
    """Yield (area, skill, SKILL.md path, manifest path) for every published
    skill directory containing both files, sorted by area then skill."""
    root = Path(skills_dir)
    if not root.is_dir():
        return
    for area_dir in sorted(root.iterdir()):
        if not area_dir.is_dir() or area_dir.name.startswith(".") or area_dir.name == "index.json":
            continue
        for skill_dir in sorted(area_dir.iterdir()):
            skill_path = skill_dir / "SKILL.md"
            manifest_path = skill_dir / "manifest.json"
            if skill_path.is_file() and manifest_path.is_file():
                yield area_dir.name, skill_dir.name, skill_path, manifest_path


def _load_run_manifests(output_dir: str) -> dict[str, dict]:
    """Load every runs/<name>/manifest.json keyed by run name, silently
    skipping missing or unreadable manifests."""
    manifests: dict[str, dict] = {}
    runs_root = Path(output_dir) / "runs"
    if not runs_root.is_dir():
        return manifests
    for run_dir in sorted(runs_root.iterdir()):
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            manifests[run_dir.name] = load_json(str(manifest_path))
        except (OSError, json.JSONDecodeError):
            continue
    return manifests


def _augmentation_receipts(output_dir: str) -> list[dict]:
    """Parse data/augmentation_receipts.jsonl into receipt dicts, skipping
    blank and malformed lines."""
    path = Path(output_dir) / "data" / "augmentation_receipts.jsonl"
    if not path.is_file():
        return []
    receipts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                receipts.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return receipts


def build_analysis(
    *,
    output_dir: str,
    skills_dir: str,
    inventory: SiteInventory,
    render_summary: dict | None = None,
    publish_receipt: dict | None = None,
) -> dict:
    """Aggregate every persisted artifact into one analysis record and
    persist it as data/fractiskills_analysis.json and data/skills.csv."""
    skills: list[dict] = []
    for area, name, skill_path, manifest_path in _iter_published_skills(skills_dir):
        skill_md = skill_path.read_text(encoding="utf-8")
        manifest = load_json(str(manifest_path))
        body = skill_md.split("---", 2)[-1]
        words = len(body.split())
        section_headings = re.findall(r"(?m)^##\s+(.+)$", body)
        skills.append(
            {
                "area": area,
                "skill": name,
                "skill_name": manifest.get("skill_name"),
                "target_id": manifest.get("target_id"),
                "generator": manifest.get("generator"),
                "source_urls": manifest.get("source_urls", []),
                "description": _skill_frontmatter_description(skill_md),
                "body_chars": len(body),
                "word_count": words,
                "provenance_sections": len(section_headings),
            }
        )
    word_counts = [skill["word_count"] for skill in skills] or [0]
    augmentation = _augmentation_receipts(output_dir)
    augmentation_by_page: dict[str, dict] = {}
    for receipt in augmentation:
        augmentation_by_page[str(receipt.get("page_url"))] = receipt
    augmentation_ok = [receipt for receipt in augmentation if receipt.get("ok")]
    aliases = [
        {"url": entry.url, "aliases": list(entry.alias_urls)}
        for entry in inventory.entries
        if entry.alias_urls
    ]
    sections: dict[str, dict] = {}
    for entry in inventory.entries:
        bucket = sections.setdefault(
            entry.section,
            {"section": entry.section, "pages": 0, "via_sitemap": 0, "via_crawl_only": 0},
        )
        bucket["pages"] += 1
        if entry.via_sitemap:
            bucket["via_sitemap"] += 1
        if not entry.via_sitemap:
            bucket["via_crawl_only"] += 1
    for skill in skills:
        skill["augmented"] = any(url in augmentation_by_page for url in skill["source_urls"])
        skill["augmentation_ok"] = any(
            augmentation_by_page.get(url, {}).get("ok") for url in skill["source_urls"]
        )
        bucket = sections.setdefault(
            skill["area"],
            {"section": skill["area"], "pages": 0, "via_sitemap": 0, "via_crawl_only": 0},
        )
        bucket["skills"] = bucket.get("skills", 0) + 1
        bucket["words"] = bucket.get("words", 0) + skill["word_count"]
    # Resolve inbound-link targets to inventory pages: a link to a redirect
    # stub or declared canonical duplicate counts toward the page it
    # forwards to; only links to discovered pages are counted.
    page_urls = {entry.url for entry in inventory.entries}
    alias_resolution: dict[str, str] = {}
    for entry in inventory.entries:
        for alias in entry.alias_urls:
            alias_resolution[alias] = entry.url

    def _resolve_target(link: str) -> str | None:
        # Follow the alias chain with a cycle guard; a link counts only when
        # it lands on a discovered page.
        current = link
        seen: set[str] = set()
        while current not in page_urls and current not in seen:
            seen.add(current)
            if current in alias_resolution:
                current = alias_resolution[current]
            else:
                return current if current in page_urls else None
        return current if current in page_urls else None

    inbound: dict[str, int] = {}
    unresolved_targets: dict[str, int] = {}
    for entry in inventory.entries:
        for link in entry.links:
            resolved = _resolve_target(link)
            if resolved is None:
                unresolved_targets[link] = unresolved_targets.get(link, 0) + 1
                continue
            inbound[resolved] = inbound.get(resolved, 0) + 1
    section_of = {entry.url: entry.section for entry in inventory.entries}
    path_of = {entry.url: entry.path for entry in inventory.entries}
    top_indegree = sorted(inbound.items(), key=lambda item: (-item[1], item[0]))[:15]
    section_outbound: dict[str, int] = {}
    for entry in inventory.entries:
        section_outbound[entry.section] = section_outbound.get(entry.section, 0) + len(entry.links)
    depth_counts: dict[str, int] = {}
    for entry in inventory.entries:
        depth = str(entry.crawl_depth) if entry.crawl_depth is not None else "unfetched"
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    mode_depth = max(depth_counts, key=lambda k: depth_counts[k]) if depth_counts else ""
    mode_depth = "unfetched" if mode_depth == "unfetched" else mode_depth
    total_depth_pages = sum(depth_counts.values()) or 1
    sitemap_yield = (
        100
        * sum(1 for e in inventory.entries if e.via_sitemap)
        / max(inventory.sitemap_url_count, 1)
    )
    augmented_words = [skill["word_count"] for skill in skills if skill["augmentation_ok"]]
    static_words = [skill["word_count"] for skill in skills if not skill["augmentation_ok"]]
    augmented_median = statistics.median(augmented_words) if augmented_words else 0
    static_median = statistics.median(static_words) if static_words else 0
    heavy_section = max(sections.values(), key=lambda b: b.get("words", 0), default=None)
    biggest_section = max(sections.values(), key=lambda b: b.get("pages", 0), default=None)
    run_manifests = _load_run_manifests(output_dir)
    successful_runs = {
        name: manifest
        for name, manifest in run_manifests.items()
        if manifest.get("state") == "rendered"
    }
    analysis = {
        "inventory": {
            "base_url": inventory.base_url,
            "sitemap_url": inventory.sitemap_url,
            "generated_at": inventory.generated_at,
            "sitemap_url_count": inventory.sitemap_url_count,
            "crawl_accepted_count": inventory.crawl_accepted_count,
            "discovered_pages": len(inventory.entries),
            "via_sitemap": sum(1 for e in inventory.entries if e.via_sitemap),
            "via_crawl_only": sum(1 for e in inventory.entries if not e.via_sitemap),
            "alias_pages": len(aliases),
            "incomplete": inventory.incomplete,
            "warnings": list(inventory.crawl_warnings),
        },
        "links_by_page": {
            entry.url: list(entry.links) for entry in inventory.entries if entry.links
        },
        "sections": [
            {
                "section": name,
                "pages": bucket.get("pages", 0),
                "skills": bucket.get("skills", 0),
                "words": bucket.get("words", 0),
                "via_sitemap": bucket.get("via_sitemap", 0),
                "via_crawl_only": bucket.get("via_crawl_only", 0),
            }
            for name, bucket in sorted(sections.items())
        ],
        "indegree": {
            "top": [
                {
                    "url": url,
                    "path": path_of.get(url, url),
                    "section": section_of.get(url, "(unknown)"),
                    "inbound": count,
                }
                for url, count in top_indegree
            ],
            "linked_pages": len(inbound),
            "unresolved_target_count": sum(unresolved_targets.values()),
            "unresolved_top": sorted(
                unresolved_targets.items(), key=lambda item: (-item[1], item[0])
            )[:10],
        },
        "section_outbound": dict(sorted(section_outbound.items(), key=lambda item: -item[1])),
        "depth_histogram": dict(
            sorted(
                depth_counts.items(),
                key=lambda item: (item[0] == "unfetched", item[0]),
            )
        ),
        "mode_depth": f"depth {mode_depth}"
        if mode_depth and mode_depth != "unfetched"
        else (mode_depth or "n/a"),
        "mode_depth_share": round(100 * depth_counts.get(mode_depth, 0) / total_depth_pages, 1),
        "sitemap_yield": round(sitemap_yield, 1),
        "augment_ratio": round(augmented_median / static_median, 1) if static_median else 0.0,
        "heavy_section": heavy_section["section"] if heavy_section else "",
        "biggest_section": (
            f"{biggest_section['section']} ({biggest_section.get('pages', 0)} pages)"
            if biggest_section
            else ""
        ),
        "skills": {
            "count": len(skills),
            "total_words": sum(word_counts),
            "median_words": statistics.median(word_counts),
            "total_chars": sum(skill["body_chars"] for skill in skills),
            "augmented_count": len(augmented_words),
            "static_count": len(static_words),
            "median_words_augmented": statistics.median(augmented_words) if augmented_words else 0,
            "median_words_static": statistics.median(static_words) if static_words else 0,
            "records": skills,
        },
        "augmentation": {
            "attempts": len(augmentation),
            "ok": len(augmentation_ok),
            "failed": len(augmentation) - len(augmentation_ok),
            "document_text_chars": sum(receipt.get("text_chars", 0) for receipt in augmentation_ok),
            "receipts": augmentation,
        },
        "aliases": aliases,
        "runs": {
            "successful": sorted(successful_runs),
            "pipeline_version": next(
                (
                    str(m.get("pipeline_version"))
                    for m in successful_runs.values()
                    if m.get("pipeline_version")
                ),
                "",
            ),
            "request_count": sum(
                manifest.get("request_count", 0) for manifest in successful_runs.values()
            ),
            "evidence_origins": sorted(
                {str(manifest.get("evidence_origin")) for manifest in successful_runs.values()}
            ),
        },
        "render_summary": render_summary or {},
        "publish_receipt": {
            "count": (publish_receipt or {}).get("count", 0),
            "published_at": (publish_receipt or {}).get("published_at", ""),
        },
    }
    write_analysis(analysis, output_dir)
    write_skills_csv(skills, output_dir)
    return analysis


def write_analysis(analysis: dict, output_dir: str) -> None:
    """Persist the analysis record atomically to data/fractiskills_analysis.json."""
    write_json_atomic(f"{output_dir}/data/fractiskills_analysis.json", analysis)


def write_skills_csv(skills: list[dict], output_dir: str) -> None:
    """Write the skill records to data/skills.csv, joining source_urls and
    dropping the description/augmentation flag columns."""
    path = Path(output_dir) / "data" / "skills.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "area",
                "skill",
                "skill_name",
                "target_id",
                "generator",
                "source_urls",
                "word_count",
                "body_chars",
                "provenance_sections",
            ],
        )
        writer.writeheader()
        for skill in skills:
            row = dict(skill)
            row.pop("description", None)
            row.pop("augmented", None)
            row.pop("augmentation_ok", None)
            row["source_urls"] = " ".join(row.get("source_urls", []))
            writer.writerow(row)
