"""Deterministic matplotlib visualizations from the persisted analysis.

Offline layer: reads analysis records, writes PNG figures plus a registry
consumed by the manuscript binder. No timestamps are drawn inside figures;
color is the colorblind-safe Okabe-Ito palette throughout.
"""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .discover import section_for_path  # noqa: E402
from .models import write_json_atomic  # noqa: E402

_DPI = 200

# Okabe-Ito colorblind-safe palette
_C_TEAL = "#0072B2"
_C_ORANGE = "#E69F00"
_C_BLUE = "#56B4E9"
_C_GREEN = "#009E73"
_C_RED = "#D55E00"
_C_PURPLE = "#CC79A7"
_C_GREY = "#7F7F7F"
_C_LIGHT = "#9ECAE1"


def _style_axes(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)


def _pages_per_section(analysis: dict) -> list[tuple[str, int]]:
    return [
        (row["section"], row["pages"])
        for row in sorted(analysis["sections"], key=lambda row: (row["pages"], row["section"]))
    ]


def figure_site_sections(analysis: dict, output_dir: str) -> str:
    rows = _pages_per_section(analysis)
    names = [name for name, _ in rows]
    values = [count for _, count in rows]
    words_per_page = {
        row["section"]: (row["words"] / row["pages"]) if row["pages"] else 0
        for row in analysis["sections"]
    }
    fig, ax = plt.subplots(figsize=(8.4, 0.55 * max(len(rows), 3) + 1.6))
    bars = ax.barh(names, values, color=_C_TEAL)
    ax.bar_label(bars, padding=3, fontsize=8)
    xmax = max(values) or 1
    ax.set_xlim(0, xmax * 1.28)
    for index, name in enumerate(names):
        wpp = words_per_page.get(name, 0)
        ax.annotate(
            f"{wpp:,.0f} w/page",
            (xmax * 1.255, index),
            ha="right",
            va="center",
            fontsize=7,
            color=_C_GREY,
        )
    ax.set_xlabel("Discovered pages")
    ax.set_title(f"SS Vibelandia pages per section (n={sum(values)})", fontsize=11)
    _style_axes(ax)
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
    fig, ax = plt.subplots(figsize=(8.4, 0.55 * max(len(rows), 3) + 1.6))
    ax.barh(names, sitemap, color=_C_BLUE, label="In declared sitemap")
    ax.barh(names, crawl_only, left=sitemap, color=_C_ORANGE, label="Crawl-discovered only")
    total_sitemap = sum(sitemap)
    total_crawl = sum(crawl_only)
    ax.annotate(
        f"sitemap {total_sitemap} / crawl-only {total_crawl}",
        (0.98, 1.03),
        xycoords="axes fraction",
        ha="right",
        va="bottom",
        fontsize=8,
        color=_C_GREY,
    )
    ax.set_xlabel("Discovered pages")
    ax.set_title("Discovery provenance by section", fontsize=11)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    _style_axes(ax)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig2-discovery-provenance.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def figure_corpus_share(analysis: dict, output_dir: str) -> str:
    rows = sorted(analysis["sections"], key=lambda row: row["pages"], reverse=True)
    names = [row["section"] for row in rows]
    total_pages = sum(row["pages"] for row in rows) or 1
    total_words = sum(row["words"] for row in rows) or 1
    pages_share = [100 * row["pages"] / total_pages for row in rows]
    words_share = [100 * row["words"] / total_words for row in rows]
    x = range(len(names))
    width = 0.4
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.bar([i - width / 2 for i in x], pages_share, width, color=_C_BLUE, label="Share of pages")
    ax.bar(
        [i + width / 2 for i in x], words_share, width, color=_C_TEAL, label="Share of skill words"
    )
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Share (%)")
    ax.set_title("Where the site's mass lives: pages versus words", fontsize=11)
    ax.legend(fontsize=8, frameon=False)
    _style_axes(ax)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig3-corpus-share.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def figure_skill_sizes(analysis: dict, output_dir: str) -> str:
    records = analysis["skills"]["records"]
    sections = sorted({r["area"] for r in records})
    by_area = {area: [r["word_count"] for r in records if r["area"] == area] for area in sections}
    order = sorted(sections, key=lambda a: sum(by_area[a]) / max(len(by_area[a]), 1))
    data = [by_area[area] for area in order]
    fig, ax = plt.subplots(figsize=(8.6, 0.45 * max(len(order), 3) + 1.8))
    boxes = ax.boxplot(
        data,
        vert=False,
        tick_labels=order,
        showfliers=True,
        flierprops={"markersize": 2.5, "alpha": 0.5},
        patch_artist=True,
        medianprops={"color": _C_RED, "linewidth": 1.4},
    )
    for box in boxes["boxes"]:
        box.set(facecolor=_C_LIGHT, edgecolor=_C_BLUE, linewidth=0.8)
    for counts, area in zip(data, order, strict=True):
        ax.annotate(
            f"n={len(counts)}",
            (1.0, order.index(area) + 1),
            xycoords=("axes fraction", "data"),
            va="center",
            ha="left",
            fontsize=7,
            color=_C_GREY,
        )
    median = analysis["skills"]["median_words"]
    ax.axvline(median, color=_C_RED, linestyle="--", linewidth=1, alpha=0.7)
    ax.annotate(
        f"overall median {median:,.0f}",
        (median, 0.02),
        xycoords=("data", "axes fraction"),
        rotation=90,
        fontsize=7,
        color=_C_RED,
        ha="right",
    )
    ax.set_xlabel("Words per rendered SKILL.md body")
    ax.set_title("Skill size distribution by section", fontsize=11)
    ax.set_xlim(left=0)
    _style_axes(ax)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig4-skill-size-distribution.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def _skill_links(skill: dict, analysis: dict) -> list[str]:
    """Outbound same-origin links quoted by one skill's source page."""
    links_by_page = analysis.get("links_by_page", {})
    for url in skill["source_urls"]:
        if url in links_by_page:
            return list(links_by_page[url])
    return []


def _section_of_link(link: str) -> str:
    path = urlparse(link).path or "/"
    query = urlparse(link).query
    if query:
        path = f"{path}?{query}"
    return section_for_path(path)


def figure_section_link_graph(analysis: dict, output_dir: str) -> str:
    edges: Counter = Counter()
    for skill in analysis["skills"]["records"]:
        source_section = skill["area"]
        for link in _skill_links(skill, analysis):
            target_section = _section_of_link(link)
            if target_section != source_section:
                edges[(source_section, target_section)] += 1
    sections = sorted({row["section"] for row in analysis["sections"]}) or ["(empty)"]
    page_counts = {row["section"]: row["pages"] for row in analysis["sections"]}
    n = len(sections)
    radius = 1.0
    positions = {
        section: (
            radius * math.cos(2 * math.pi * index / n),
            radius * math.sin(2 * math.pi * index / n),
        )
        for index, section in enumerate(sections)
    }
    fig, ax = plt.subplots(figsize=(9, 9))
    max_edge = max(edges.values(), default=1)
    for (source, target), count in sorted(edges.items()):
        x0, y0 = positions.get(source, (0.0, 0.0))
        x1, y1 = positions.get(target, (0.0, 0.0))
        weight = count / max_edge
        dx, dy = x1 - x0, y1 - y0
        shrink = 0.09
        ax.annotate(
            "",
            xy=(x1 - shrink * dx, y1 - shrink * dy),
            xytext=(x0 + shrink * dx, y0 + shrink * dy),
            arrowprops={
                "arrowstyle": "-|>",
                "color": _C_GREY,
                "alpha": 0.3 + 0.6 * weight,
                "linewidth": 0.6 + 3.2 * weight,
                "shrinkA": 0,
                "shrinkB": 0,
            },
            zorder=1,
        )
    max_pages = max(page_counts.values(), default=1)
    for section, (x, y) in positions.items():
        size = 220 + 2600 * (page_counts.get(section, 0) / max_pages)
        ax.scatter(
            [x], [y], s=size, color=_C_BLUE, zorder=2, alpha=0.9, edgecolors="white", linewidths=1.2
        )
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
        "Cross-section link flow quoted in rendered skills\n"
        "(node area = pages, edge weight = skill-quoted links)",
        fontsize=11,
    )
    ax.set_axis_off()
    ax.set_aspect("equal")
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig5-section-link-graph.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def figure_augmentation(analysis: dict, output_dir: str) -> str:
    """Histogram of retrieved document sizes for successful augmentations."""
    receipts = [r for r in analysis["augmentation"]["receipts"] if r.get("ok")]
    values = [r.get("text_chars", 0) for r in receipts]
    augmentation = analysis["augmentation"]
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    if values:
        ax.hist(
            values,
            bins=min(max(len(values) // 6, 8), 28),
            color=_C_ORANGE,
            edgecolor="white",
        )
    median = sorted(values)[len(values) // 2] if values else 0
    ax.axvline(median, color=_C_TEAL, linestyle="--", linewidth=1.2)
    ax.annotate(
        f"median {median:,.0f} chars",
        (median, 0.92),
        xycoords=("data", "axes fraction"),
        xytext=(6, 0),
        textcoords="offset points",
        fontsize=8,
        color=_C_TEAL,
        va="top",
    )
    ax.set_xlabel("Retrieved document characters (same-origin API)", fontsize=9)
    ax.set_ylabel("Dynamic pages")
    ax.set_title(
        "Dynamic-document augmentation sizes\n"
        f"{len(values)} retrieved of {augmentation['attempts']} attempts "
        f"({augmentation['failed']} failed with receipts)",
        fontsize=11,
    )
    _style_axes(ax)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig6-augmentation.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def figure_discovery_funnel(analysis: dict, output_dir: str) -> str:
    inv = analysis["inventory"]
    stages = [
        ("Sitemap URLs declared", inv["sitemap_url_count"], _C_BLUE),
        ("Distinct pages via sitemap", inv["via_sitemap"], _C_TEAL),
        ("Full union (sitemap ∪ crawl)", inv["discovered_pages"], _C_ORANGE),
    ]
    labels = [name for name, _, _ in stages][::-1]
    values = [value for _, value, _ in stages][::-1]
    colors = [color for _, _, color in stages][::-1]
    fig, ax = plt.subplots(figsize=(8.4, 3.4))
    bars = ax.barh(labels, values, color=colors)
    ax.bar_label(bars, padding=4, fontsize=9, fmt="{:,.0f}")
    xmax = max(values) or 1
    ax.set_xlim(0, xmax * 1.22)
    yield_sitemap = 100 * inv["via_sitemap"] / inv["sitemap_url_count"]
    union_ratio = inv["discovered_pages"] / max(inv["sitemap_url_count"], 1)
    ax.annotate(
        f"sitemap yield {yield_sitemap:.0f}% · union {union_ratio:.1f}× sitemap",
        (0.98, 1.04),
        xycoords="axes fraction",
        ha="right",
        va="bottom",
        fontsize=8,
        color=_C_GREY,
    )
    ax.set_xlabel("Distinct pages")
    ax.set_title("Discovery funnel", fontsize=11)
    _style_axes(ax)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig7-discovery-funnel.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def figure_crawl_depth(analysis: dict, output_dir: str) -> str:
    histogram = analysis["depth_histogram"]
    keys = sorted(histogram, key=lambda k: (k == "unfetched", int(k) if k.isdigit() else 99))
    values = [histogram[key] for key in keys]
    labels = [key if key != "unfetched" else "unfetched" for key in keys]
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    bars = ax.bar(labels, values, color=_C_GREEN)
    ax.bar_label(bars, padding=3, fontsize=8)
    total = sum(values) or 1
    for label, value in zip(labels, values, strict=True):
        ax.annotate(
            f"{100 * value / total:.0f}%",
            (label, value),
            ha="center",
            va="bottom",
            xytext=(0, 2),
            textcoords="offset points",
            fontsize=8,
            color=_C_GREY,
        )
    ax.set_xlabel("BFS depth at discovery")
    ax.set_ylabel("Pages")
    ax.set_title(f"How deep the crawl had to reach (n={total})", fontsize=11)
    _style_axes(ax)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig8-crawl-depth.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def figure_top_indegree(analysis: dict, output_dir: str) -> str:
    top = analysis["indegree"]["top"]
    palette = [_C_BLUE, _C_ORANGE, _C_GREEN, _C_RED, _C_PURPLE]
    section_names = sorted({row["section"] for row in analysis["sections"]})
    color_of = {name: palette[index % len(palette)] for index, name in enumerate(section_names)}
    top = sorted(top, key=lambda row: row["inbound"])
    labels = [(row["section"] + " · " + (row["path"].rstrip("/") or "/"))[-52:] for row in top]
    values = [row["inbound"] for row in top]
    colors = [color_of.get(row["section"], _C_GREY) for row in top]
    fig, ax = plt.subplots(figsize=(8.4, 0.42 * max(len(top), 3) + 1.6))
    bars = ax.barh(labels, values, color=colors)
    ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_xlabel("Inbound links from other discovered pages")
    ax.set_title(f"Top {len(top)} most-linked pages (hub structure)", fontsize=11)
    ax.tick_params(axis="y", labelsize=7)
    ax.set_xlim(left=0)
    _style_axes(ax)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig9-top-indegree.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def figure_augmentation_effect(analysis: dict, output_dir: str) -> str:
    skills = analysis["skills"]
    pairs = [
        ("Static (no document)", skills["static_count"], skills["median_words_static"], _C_BLUE),
        (
            "Augmented (document-bearing)",
            skills["augmented_count"],
            skills["median_words_augmented"],
            _C_ORANGE,
        ),
    ]
    labels = [name for name, _, _, _ in pairs]
    counts = [count for _, count, _, _ in pairs]
    medians = [median for _, _, median, _ in pairs]
    colors = [color for _, _, _, color in pairs]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bars = ax.bar(labels, medians, color=colors, width=0.55)
    for bar, count, median in zip(bars, counts, medians, strict=True):
        ax.annotate(
            f"median {median:,.0f} words · n={count}",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            ha="center",
            va="bottom",
            fontsize=9,
            color=_C_GREY,
            xytext=(0, 4),
            textcoords="offset points",
        )

    ax.set_ylabel("Median skill body words")
    ratio = (medians[1] / medians[0]) if medians[0] else 0
    ax.set_title(f"What augmentation adds to a skill body (median ×{ratio:.1f})", fontsize=11)
    ax.set_ylim(0, max(medians) * 1.22)
    _style_axes(ax)
    fig.tight_layout()
    path = f"{output_dir}/figures/fig10-augmentation-effect.png"
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def build_figures(analysis: dict, *, output_dir: str) -> list[dict]:
    """Render every figure and persist the registry with captions."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir, "figures").mkdir(parents=True, exist_ok=True)
    inv = analysis["inventory"]
    skills = analysis["skills"]
    biggest = max(analysis["sections"], key=lambda row: row["pages"], default=None)
    heavy = max(analysis["sections"], key=lambda row: row["words"], default=None)
    augmentation = analysis["augmentation"]
    registry = [
        {
            "figure_id": "site-sections",
            "path": figure_site_sections(analysis, output_dir),
            "caption": (
                f"Discovered pages per section of the SS Vibelandia site (n={inv['discovered_pages']}), "
                f"annotated with mean skill words per page. The largest section is "
                f"{biggest['section']} with {biggest['pages']} pages."
                if biggest
                else "Discovered pages per section (no pages)."
            ),
            "alt_text": "Horizontal bar chart of page counts per site section with words-per-page annotations.",
        },
        {
            "figure_id": "discovery-provenance",
            "path": figure_discovery_provenance(analysis, output_dir),
            "caption": (
                "Discovery provenance by section: pages listed in the declared sitemap versus pages "
                f"found only by the bounded breadth-first crawl ({inv['via_sitemap']} sitemap, "
                f"{inv['via_crawl_only']} crawl-only)."
            ),
            "alt_text": "Stacked horizontal bar chart of sitemap versus crawl-only page counts per section.",
        },
        {
            "figure_id": "corpus-share",
            "path": figure_corpus_share(analysis, output_dir),
            "caption": (
                "Share of pages versus share of rendered skill words by section. "
                f"{heavy['section']} carries {100 * heavy['words'] / max(skills['total_words'], 1):.0f}% "
                "of the corpus words."
                if heavy
                else "Share of pages versus share of words by section (no data)."
            ),
            "alt_text": "Grouped bar chart comparing page share and word share per section.",
        },
        {
            "figure_id": "skill-size-distribution",
            "path": figure_skill_sizes(analysis, output_dir),
            "caption": (
                "Body-size distribution of the "
                f"{skills['count']} rendered SKILL.md documents, box-plotted per section "
                f"(overall median {skills['median_words']:,.0f} words)."
            ),
            "alt_text": "Horizontal box plot of skill body word counts per site section.",
        },
        {
            "figure_id": "section-link-graph",
            "path": figure_section_link_graph(analysis, output_dir),
            "caption": (
                "Cross-section link flow quoted inside rendered skills: node area is proportional to "
                "section page count and edge weight to the number of skill-quoted links between "
                "sections (arrows point from the quoting section to the quoted section)."
            ),
            "alt_text": "Circular directed graph of link flow between site sections.",
        },
        {
            "figure_id": "augmentation",
            "path": figure_augmentation(analysis, output_dir),
            "caption": (
                "Dynamic-document augmentation: same-origin API documents retrieved for "
                "client-rendered pages "
                f"({augmentation['ok']} succeeded, {augmentation['failed']} failed with persisted receipts)."
            ),
            "alt_text": "Horizontal bar chart of retrieved document sizes for dynamic pages.",
        },
        {
            "figure_id": "discovery-funnel",
            "path": figure_discovery_funnel(analysis, output_dir),
            "caption": (
                "Discovery funnel: declared sitemap URLs, distinct pages reached through them, and "
                f"the full union ({inv['discovered_pages']} pages = "
                f"{inv['discovered_pages'] / max(inv['sitemap_url_count'], 1):.1f}× the sitemap count)."
            ),
            "alt_text": "Horizontal funnel bar chart from sitemap URLs to the full page union.",
        },
        {
            "figure_id": "crawl-depth",
            "path": figure_crawl_depth(analysis, output_dir),
            "caption": (
                "Pages by breadth-first discovery depth: most pages sit several hops from the root, "
                "which is why a sitemap-only render would have missed them."
            ),
            "alt_text": "Bar chart of page counts by BFS discovery depth.",
        },
        {
            "figure_id": "top-indegree",
            "path": figure_top_indegree(analysis, output_dir),
            "caption": (
                f"The {len(analysis['indegree']['top'])} most-linked pages by inbound links from other "
                "discovered pages, colored by section: the site's hub structure."
            ),
            "alt_text": "Horizontal bar chart of the most inbound-linked pages colored by section.",
        },
        {
            "figure_id": "augmentation-effect",
            "path": figure_augmentation_effect(analysis, output_dir),
            "caption": (
                "Median skill body size for static pages versus augmented (document-bearing) pages "
                f"(n={skills['static_count']} static, n={skills['augmented_count']} augmented)."
            ),
            "alt_text": "Bar chart comparing median skill sizes of static and augmented skills.",
        },
    ]
    write_json_atomic(f"{output_dir}/data/figure_registry.json", {"figures": registry})
    return registry
