"""Deterministic matplotlib visualizations from the persisted analysis.

Offline layer: reads analysis records, writes PNG figures plus a registry
consumed by the manuscript binder. No timestamps are drawn inside figures.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .models import write_json_atomic  # noqa: E402

_DPI = 200


def _pages_per_section(analysis: dict) -> list[tuple[str, int]]:
    return [
        (row["section"], row["pages"])
        for row in sorted(analysis["sections"], key=lambda row: (row["pages"], row["section"]))
    ]


def figure_site_sections(analysis: dict, output_dir: str) -> str:
    rows = _pages_per_section(analysis)
    names = [name for name, _ in rows]
    values = [count for _, count in rows]
    fig, ax = plt.subplots(figsize=(8, 0.6 * max(len(rows), 3) + 1.5))
    bars = ax.barh(names, values, color="#0f766e")
    ax.bar_label(bars, padding=3)
    ax.set_xlabel("Discovered pages")
    ax.set_title(f"SS Vibelandia pages per section (n={sum(values)})")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig1-site-sections.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def figure_discovery_provenance(analysis: dict, output_dir: str) -> str:
    rows = sorted(analysis["sections"], key=lambda row: (row["pages"], row["section"]))
    names = [row["section"] for row in rows]
    sitemap = [row["via_sitemap"] for row in rows]
    crawl_only = [row["via_crawl_only"] for row in rows]
    fig, ax = plt.subplots(figsize=(8, 0.6 * max(len(rows), 3) + 1.5))
    ax.barh(names, sitemap, color="#1e3a8a", label="In sitemap")
    ax.barh(
        names,
        crawl_only,
        left=sitemap,
        color="#93c5fd",
        label="Crawl-discovered only",
    )
    ax.set_xlabel("Discovered pages")
    ax.set_title("Discovery provenance by section")
    ax.legend(loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig2-discovery-provenance.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def figure_skill_sizes(analysis: dict, output_dir: str) -> str:
    words = [skill["word_count"] for skill in analysis["skills"]["records"]]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(words, bins=min(max(len(words) // 3, 6), 24), color="#0f766e", edgecolor="white")
    median = analysis["skills"]["median_words"]
    ax.axvline(median, color="#b45309", linestyle="--", label=f"Median = {median:.0f} words")
    ax.set_xlabel("Words per rendered SKILL.md body")
    ax.set_ylabel("Skills")
    ax.set_title(f"Skill size distribution (n={len(words)})")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig3-skill-size-distribution.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def _section_of_link(link: str) -> str:
    from urllib.parse import urlparse

    from .discover import section_for_path

    path = urlparse(link).path or "/"
    query = urlparse(link).query
    if query:
        path = f"{path}?{query}"
    return section_for_path(path)


def figure_section_link_graph(analysis: dict, output_dir: str) -> str:
    from collections import Counter

    edges: Counter = Counter()
    for skill in analysis["skills"]["records"]:
        source_section = skill["area"]
        for link in _skill_links(skill, analysis):
            target_section = _section_of_link(link)
            if target_section != source_section:
                edges[(source_section, target_section)] += 1
    sections = sorted(
        {row["section"] for row in analysis["sections"]},
    )
    page_counts = {row["section"]: row["pages"] for row in analysis["sections"]}
    if not sections:
        sections = ["(empty)"]
    n = len(sections)
    positions = {
        section: (
            math.cos(2 * math.pi * index / n),
            math.sin(2 * math.pi * index / n),
        )
        for index, section in enumerate(sorted(sections))
    }
    fig, ax = plt.subplots(figsize=(8.5, 8.5))
    max_edge = max(edges.values(), default=1)
    for (source, target), count in sorted(edges.items()):
        x0, y0 = positions.get(source, (0.0, 0.0))
        x1, y1 = positions.get(target, (0.0, 0.0))
        ax.plot(
            [x0, x1],
            [y0, y1],
            color="#64748b",
            alpha=0.25 + 0.55 * (count / max_edge),
            linewidth=0.6 + 2.4 * (count / max_edge),
            zorder=1,
        )
    max_pages = max(page_counts.values(), default=1)
    for section, (x, y) in positions.items():
        size = 220 + 2600 * (page_counts.get(section, 0) / max_pages)
        ax.scatter([x], [y], s=size, color="#1e3a8a", zorder=2, alpha=0.9)
        ax.annotate(
            f"{section}\n({page_counts.get(section, 0)})",
            (x, y),
            textcoords="offset points",
            xytext=(0, 12),
            ha="center",
            fontsize=8,
            zorder=3,
        )
    ax.set_title(
        "Cross-section link flow in rendered skills\n"
        "(node area = pages, edge weight = skill-quoted links)"
    )
    ax.set_axis_off()
    ax.set_aspect("equal")
    fig.tight_layout()
    path = f"{output_dir}/figures/fig4-section-link-graph.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def _skill_links(skill: dict, analysis: dict) -> list[str]:
    """Outbound same-origin links quoted by one skill's source page."""
    links_by_page = analysis.get("inventory", {}).get("_links_by_page", {})
    for url in skill["source_urls"]:
        if url in links_by_page:
            return list(links_by_page[url])
    return []


def figure_augmentation(analysis: dict, output_dir: str) -> str:
    receipts = [r for r in analysis["augmentation"]["receipts"] if r.get("ok")]
    from urllib.parse import urlparse

    receipts = sorted(receipts, key=lambda r: r.get("text_chars", 0))
    labels = [
        urlparse(receipt.get("page_url", "")).path.lstrip("/")[-42:] or "(root)"
        for receipt in receipts
    ]
    values = [receipt.get("text_chars", 0) for receipt in receipts]
    fig, ax = plt.subplots(figsize=(8, 0.45 * max(len(values), 3) + 1.5))
    bars = ax.barh(labels, values, color="#b45309")
    ax.bar_label(bars, padding=3, fontsize=7)
    ax.set_xlabel("Document characters retrieved from the declared API")
    ax.set_title(
        "Dynamic-document augmentation sizes "
        f"(n={len(values)} of {analysis['augmentation']['attempts']} attempts)"
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig5-augmentation.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def build_figures(analysis: dict, *, output_dir: str) -> list[dict]:
    """Render every figure and persist the registry with captions."""
    Path(output_dir, "figures").mkdir(parents=True, exist_ok=True)
    total_pages = analysis["inventory"]["discovered_pages"]
    section_rows = analysis["sections"]
    biggest = max(section_rows, key=lambda row: row["pages"], default=None)
    augmentation = analysis["augmentation"]
    registry = [
        {
            "figure_id": "site-sections",
            "path": figure_site_sections(analysis, output_dir),
            "caption": (
                f"Discovered pages per section of the SS Vibelandia site "
                f"(n={total_pages}). The largest section is "
                f"{biggest['section']} with {biggest['pages']} pages."
                if biggest
                else "Discovered pages per section (no pages)."
            ),
            "alt_text": "Horizontal bar chart of page counts per site section.",
        },
        {
            "figure_id": "discovery-provenance",
            "path": figure_discovery_provenance(analysis, output_dir),
            "caption": (
                "Discovery provenance: pages listed in the declared sitemap "
                "versus pages found only by the bounded breadth-first crawl."
            ),
            "alt_text": "Stacked horizontal bar chart of sitemap versus crawl-only page counts.",
        },
        {
            "figure_id": "skill-size-distribution",
            "path": figure_skill_sizes(analysis, output_dir),
            "caption": (
                "Body-size distribution of the "
                f"{analysis['skills']['count']} rendered SKILL.md documents "
                f"(median {analysis['skills']['median_words']:.0f} words)."
            ),
            "alt_text": "Histogram of rendered skill body sizes in words.",
        },
        {
            "figure_id": "section-link-graph",
            "path": figure_section_link_graph(analysis, output_dir),
            "caption": (
                "Cross-section link flow quoted inside rendered skills: node "
                "area is proportional to section page count and edge weight to "
                "the number of skill-quoted links between sections."
            ),
            "alt_text": "Circular graph of link flow between site sections.",
        },
        {
            "figure_id": "augmentation",
            "path": figure_augmentation(analysis, output_dir),
            "caption": (
                "Dynamic-document augmentation: same-origin API documents "
                f"retrieved for client-rendered pages "
                f"({augmentation['ok']} succeeded, {augmentation['failed']} failed)."
            ),
            "alt_text": "Horizontal bar chart of retrieved document sizes for dynamic pages.",
        },
    ]
    write_json_atomic(f"{output_dir}/data/figure_registry.json", {"figures": registry})
    return registry
