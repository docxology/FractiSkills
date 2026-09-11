"""Deterministic matplotlib visualizations from the persisted analysis.

Offline layer: reads analysis records, writes PNG figures plus a registry
consumed by the manuscript binder. No timestamps are drawn inside figures;
color is the colorblind-safe Okabe-Ito palette throughout.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

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
    """Hide top/right spines and shrink tick labels."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)


def _save(fig, path: str) -> str:
    """Save the figure at the standard DPI, close it, and return the path."""
    fig.savefig(path, dpi=_DPI)
    plt.close(fig)
    return path


def _pages_per_section(analysis: dict) -> list[tuple[str, int]]:
    """Return (section, pages) pairs sorted by pages then name."""
    return [
        (row["section"], row["pages"])
        for row in sorted(analysis["sections"], key=lambda row: (row["pages"], row["section"]))
    ]


def figure_site_sections(analysis: dict, output_dir: str) -> str:
    """Horizontal bars of pages per section (sorted by pages, ties by name),
    annotated with mean words per page; writes fig1-site-sections.png."""
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
    return _save(fig, path)


def figure_discovery_provenance(analysis: dict, output_dir: str) -> str:
    """Stacked horizontal bars splitting each section's pages into
    sitemap-declared versus crawl-discovered-only; writes
    fig2-discovery-provenance.png."""
    order = {name: index for index, (name, _) in enumerate(_pages_per_section(analysis))}
    rows = sorted(analysis["sections"], key=lambda row: order[row["section"]])
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
    return _save(fig, path)


def figure_corpus_share(analysis: dict, output_dir: str) -> str:
    """Grouped bars comparing each section's share of total pages against
    its share of total skill words; writes fig3-corpus-share.png."""
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
    return _save(fig, path)


def figure_skill_sizes(analysis: dict, output_dir: str) -> str:
    """Horizontal box plots of skill body word counts per section (ordered
    by mean size) with the overall median line; writes
    fig4-skill-size-distribution.png."""
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
    return _save(fig, path)


def figure_section_link_graph(analysis: dict, output_dir: str) -> str:
    """Circular directed graph of cross-section link flow quoted in rendered
    skills: node area = section pages, edge weight = skill-quoted link count;
    writes fig5-section-link-graph.png."""
    persisted = analysis.get("section_edges", {})
    edges: Counter = Counter()
    for source, targets in persisted.items():
        for target, count in targets.items():
            edges[(source, target)] += count
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
    return _save(fig, path)


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
    median = statistics.median(values) if values else 0
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
    return _save(fig, path)


def figure_discovery_funnel(analysis: dict, output_dir: str) -> str:
    """Three-bar funnel from declared sitemap URLs to distinct sitemap pages
    to the full union, with yield/union annotations; writes
    fig7-discovery-funnel.png."""
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
    return _save(fig, path)


def figure_crawl_depth(analysis: dict, output_dir: str) -> str:
    """Vertical bars of page counts by BFS discovery depth (digit keys
    ascending, "unfetched" last) annotated with percentages; writes
    fig8-crawl-depth.png."""
    histogram = analysis["depth_histogram"]
    keys = sorted(histogram, key=lambda k: (k == "unfetched", int(k) if k.isdigit() else 99))
    values = [histogram[key] for key in keys]
    labels = list(keys)
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
    return _save(fig, path)


def figure_top_indegree(analysis: dict, output_dir: str) -> str:
    """Horizontal bars of the most inbound-linked discovered pages, colored
    by section and labeled section · path; writes fig9-top-indegree.png."""
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
    return _save(fig, path)


def figure_augmentation_effect(analysis: dict, output_dir: str) -> str:
    """Two bars comparing median skill body size for static versus
    augmented pages, annotated with counts; writes
    fig10-augmentation-effect.png."""
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
    return _save(fig, path)


def _top_word_sections(analysis: dict) -> list[dict]:
    """Sections sorted by skill-word mass, descending (ties by name)."""
    return sorted(analysis["sections"], key=lambda row: (-row["words"], row["section"]))


def figure_words_vs_pages(analysis: dict, output_dir: str) -> str:
    """Annotated scatter of pages (x) versus skill words (y) per section,
    with the corpus-average words-per-page reference line; points too small
    to label individually are grouped into a shared cluster note. Writes
    fig11-words-vs-pages.png."""
    rows = analysis["sections"]
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    xs = [row["pages"] for row in rows]
    ys = [row["words"] for row in rows]
    total_pages = sum(xs) or 1
    total_words = sum(ys) or 1
    avg_wpp = total_words / total_pages
    x_max = max(xs) * 1.12
    ax.plot(
        [0, x_max],
        [0, x_max * avg_wpp],
        color=_C_GREY,
        linestyle=":",
        linewidth=1.2,
        label=f"corpus average ({avg_wpp:,.0f} words/page)",
    )
    ax.scatter(xs, ys, s=90, color=_C_PURPLE, zorder=2, alpha=0.9, edgecolors="white")
    cluster = []
    for row in rows:
        name = row["section"]
        if row["pages"] >= 14:
            ax.annotate(
                name,
                (row["pages"], row["words"]),
                textcoords="offset points",
                xytext=(7, 5),
                fontsize=7.5,
                color="#333333",
            )
        else:
            cluster.append(name)
    if cluster:
        ax.annotate(
            "small sections\n(" + ", ".join(cluster) + ")",
            (
                max(rows_i["pages"] for rows_i in rows if rows_i["pages"] < 10),
                max(rows_i["words"] for rows_i in rows if rows_i["pages"] < 10),
            ),
            textcoords="offset points",
            xytext=(14, -4),
            fontsize=7,
            color=_C_GREY,
            arrowprops={"arrowstyle": "-", "color": _C_GREY, "linewidth": 0.7},
        )
    ax.set_xlabel("Pages", fontsize=9)
    ax.set_ylabel("Skill words", fontsize=9)
    ax.set_title(
        f"Mass per section: pages against rendered words\n"
        f"(corpus: {total_pages} pages, {total_words:,} words)",
        fontsize=11,
    )
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    _style_axes(ax)
    fig.tight_layout()
    return _save(fig, f"{output_dir}/figures/fig11-words-vs-pages.png")


def figure_cumulative_words(analysis: dict, output_dir: str) -> str:
    """Pareto curve of cumulative skill-word share over sections sorted by
    mass, annotating how few sections carry most of the corpus; writes
    fig12-cumulative-words.png."""
    rows = _top_word_sections(analysis)
    total = sum(row["words"] for row in rows) or 1
    names = [row["section"] for row in rows]
    shares = [row["words"] / total for row in rows]
    cumulative = []
    running = 0.0
    for share in shares:
        running += share
        cumulative.append(100 * running)
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.plot(range(1, len(names) + 1), cumulative, marker="o", color=_C_TEAL, linewidth=1.6)
    ax.fill_between(range(1, len(names) + 1), cumulative, color=_C_LIGHT, alpha=0.35)
    ax.set_xticks(range(1, len(names) + 1))
    ax.set_xticklabels(names, rotation=35, ha="right", fontsize=8)
    for index, value in enumerate(cumulative, start=1):
        ax.annotate(
            f"{value:.0f}%",
            (index, value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=7,
            color=_C_GREY,
        )
    ax.set_ylabel("Cumulative share of skill words (%)")
    ax.set_xlabel("Sections, ordered by word mass")
    ax.set_title(
        f"Corpus concentration: the top 2 sections carry {cumulative[1]:.0f}% of {total:,} words",
        fontsize=11,
    )
    ax.set_ylim(0, 108)
    _style_axes(ax)
    fig.tight_layout()
    return _save(fig, f"{output_dir}/figures/fig12-cumulative-words.png")


def figure_section_adjacency(analysis: dict, output_dir: str) -> str:
    """Heatmap of the section-by-section link-count matrix quoted in
    rendered skills, with counts annotated in each cell; writes
    fig13-section-adjacency.png."""
    persisted = analysis.get("section_edges", {})
    edges: Counter = Counter()
    for source, targets in persisted.items():
        for target, count in targets.items():
            edges[(source, target)] += count
    sections = sorted({row["section"] for row in analysis["sections"]})
    matrix = [[edges.get((s, t), 0) for t in sections] for s in sections]
    fig, ax = plt.subplots(figsize=(8.6, 7.4))
    image = ax.imshow(matrix, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(sections)))
    ax.set_yticks(range(len(sections)))
    ax.set_xticklabels(sections, rotation=35, ha="right", fontsize=7)
    ax.set_yticklabels(sections, fontsize=7)
    peak = max((max(row) for row in matrix), default=1) or 1
    for i in range(len(sections)):
        for j in range(len(sections)):
            count = matrix[i][j]
            if count:
                ax.annotate(
                    str(count),
                    (j, i),
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color="white" if count > peak * 0.55 else "#333333",
                )
    fig.colorbar(image, ax=ax, shrink=0.75, label="Skill-quoted link count")
    ax.set_title(
        "Section adjacency: quoted links from rows to columns\n"
        "(diagonal within-section links are excluded)",
        fontsize=11,
    )
    fig.tight_layout()
    return _save(fig, f"{output_dir}/figures/fig13-section-adjacency.png")


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
                f"{biggest['section']} with {biggest['pages']} pages; compare the right-hand words-per-page annotations against bar lengths to spot mass-dense sections."
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
                f"{inv['via_crawl_only']} crawl-only). Orange-dominant rows — Ship-Blog, Voyage, most of Interfaces — are invisible to sitemap-only ingestion."
            ),
            "alt_text": "Stacked horizontal bar chart of sitemap versus crawl-only page counts per section.",
        },
        {
            "figure_id": "corpus-share",
            "path": figure_corpus_share(analysis, output_dir),
            "caption": (
                "Share of pages versus share of rendered skill words by section. "
                f"{heavy['section']} carries {100 * heavy['words'] / max(skills['total_words'], 1):.0f}% "
                "of the corpus words; gaps between the paired bars flag sections whose average page is much heavier (Interfaces, Whitepaper) or lighter (Ship-Blog) than the corpus mean."
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
                "sections (arrows point from the quoting section to the quoted section). The dominant Ship-Blog-to-Core edge is the site's own reading spine: posts quote the deck-level pages that define their vocabulary."
            ),
            "alt_text": "Circular directed graph of link flow between site sections.",
        },
        {
            "figure_id": "augmentation",
            "path": figure_augmentation(analysis, output_dir),
            "caption": (
                "Dynamic-document augmentation: same-origin API documents retrieved for "
                "client-rendered pages "
                f"({augmentation['ok']} succeeded, {augmentation['failed']} failed with persisted receipts). The distribution is right-skewed: most retrieved documents cluster near the median with a long tail of long-form whitepapers."
            ),
            "alt_text": "Histogram of retrieved document character sizes for dynamic-page augmentations.",
        },
        {
            "figure_id": "discovery-funnel",
            "path": figure_discovery_funnel(analysis, output_dir),
            "caption": (
                "Discovery funnel: declared sitemap URLs, distinct pages reached through them, and "
                f"the full union ({inv['discovered_pages']} pages = "
                f"{inv['discovered_pages'] / max(inv['sitemap_url_count'], 1):.1f}× the sitemap count). The steep first step is sitemap yield; the tall second step is pure crawl gain."
            ),
            "alt_text": "Horizontal funnel bar chart from sitemap URLs to the full page union.",
        },
        {
            "figure_id": "crawl-depth",
            "path": figure_crawl_depth(analysis, output_dir),
            "caption": (
                "Pages by breadth-first discovery depth: most pages sit several hops from the root, "
                "which is why a sitemap-only render would have missed them; the modal depth "
                f"alone holds {analysis['mode_depth_share']:.0f}% of all pages."
            ),
            "alt_text": "Bar chart of page counts by BFS discovery depth.",
        },
        {
            "figure_id": "top-indegree",
            "path": figure_top_indegree(analysis, output_dir),
            "caption": (
                f"The {len(analysis['indegree']['top'])} most-linked pages by inbound links from other "
                "discovered pages, colored by section: the site's hub structure; links to redirect stubs and canonical duplicates fold onto their target pages, so these counts are page-level, not URL-level."
            ),
            "alt_text": "Horizontal bar chart of the most inbound-linked pages colored by section.",
        },
        {
            "figure_id": "augmentation-effect",
            "path": figure_augmentation_effect(analysis, output_dir),
            "caption": (
                "Median skill body size for static pages versus augmented (document-bearing) pages "
                f"(n={skills['static_count']} static, n={skills['augmented_count']} augmented). The gap is the measured value of honest augmentation: the same pipeline without the declared bindings would ship the shorter median throughout."
            ),
            "alt_text": "Bar chart comparing median skill sizes of static and augmented skills.",
        },
        {
            "figure_id": "words-vs-pages",
            "path": figure_words_vs_pages(analysis, output_dir),
            "caption": (
                "Pages against rendered skill words per section (log-spread "
                "annotated). Sections above the reference diagonal pack more "
                "words per page than the corpus at large: Interfaces and "
                "Whitepaper are mass-dense, while Voyage and Ship-Blog carry "
                "many lighter pages."
            ),
            "alt_text": "Scatter plot of section page counts against skill word counts with labels.",
        },
        {
            "figure_id": "cumulative-words",
            "path": figure_cumulative_words(analysis, output_dir),
            "caption": (
                "Pareto curve of cumulative skill-word share over sections "
                "ordered by mass. The curve quantifies concentration: the "
                "first two sections already carry the majority of the "
                "corpus, so a render that dropped them would lose most of "
                "the substance."
            ),
            "alt_text": "Cumulative share line chart of skill words by section.",
        },
        {
            "figure_id": "section-adjacency",
            "path": figure_section_adjacency(analysis, output_dir),
            "caption": (
                "Section-by-section heatmap of skill-quoted link counts "
                "(rows quote columns; the within-section diagonal is "
                "excluded). Dense off-diagonal cells expose the reading "
                "paths the site's own authors build between areas."
            ),
            "alt_text": "Heatmap of link counts between site sections.",
        },
    ]
    # The parent validator reads the registry from output/figures/; keep the
    # data/ copy for the analysis record consumers.
    # The parent validator's envelope shape matches references by each
    # entry's "label" field (fig:<figure_id>).
    registry_payload = {
        "schema_version": 1,
        "figures": [{**figure, "label": f"fig:{figure['figure_id']}"} for figure in registry],
    }
    write_json_atomic(f"{output_dir}/figures/figure_registry.json", registry_payload)
    write_json_atomic(f"{output_dir}/data/figure_registry.json", registry_payload)
    return registry
