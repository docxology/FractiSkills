"""Deterministic generative cover art for the FractiSkills manuscript.

Research layer: reads the persisted analysis record and renders a single
portrait PNG (the PDF cover) into ``{output_dir}/figures/cover.png``. Never
acquires pages; the drawing is fully deterministic (no RNG, no timestamps)
so regeneration byte-for-byte matches. The visual language mirrors the
site's own motif — holographic nested domes: golden-ratio (Φ = 1.618)
nested arcs on a deep near-black navy background, twelve radial spokes
whose lengths encode each section's word mass, one small dot per
discovered page, and a central convergence node. Color is the
colorblind-safe Okabe-Ito palette throughout; the cover carries no axis
furniture.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc, Circle, Wedge  # noqa: E402

_DPI = 200
_FIGSIZE = (10, 14)  # portrait: 2000 x 2800 px at 200 dpi
_PHI = (1 + math.sqrt(5)) / 2

# Okabe-Ito colorblind-safe palette
_PALETTE = (
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # green
    "#D55E00",  # vermillion
    "#CC79A7",  # purple
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
)

_BACKGROUND = "#0B1026"
_INK = "#E8ECF8"  # light text on the dark ground


def _section_slices(analysis: dict) -> list[tuple[str, float, int]]:
    """Return ``(name, words, pages)`` rows ordered by words descending.

    Angular spans for spokes and page dots are proportional to each
    section's word mass, so the slices partition the full circle.
    """
    return [
        (row["section"], float(row["words"]), int(row["pages"]))
        for row in sorted(analysis["sections"], key=lambda row: -row["words"])
    ]


def _draw_nested_arcs(ax) -> None:
    """Concentric arcs whose radii grow in Φ progression (holographic
    nested domes), each a thin Okabe-Ito stroke at low alpha."""
    radius = 0.18
    step = 0
    while radius <= 2.1:
        color = _PALETTE[step % len(_PALETTE)]
        for phase, alpha in ((0.0, 0.38), (math.pi * 0.16, 0.18)):
            ax.add_patch(
                Arc(
                    (0, 0),
                    2 * radius,
                    2 * radius,
                    theta1=math.degrees(phase),
                    theta2=math.degrees(phase + 2 * math.pi * 0.62),
                    lw=1.3,
                    color=color,
                    alpha=alpha,
                )
            )
        step += 1
        radius *= _PHI


def _draw_spokes(ax, rows: list[tuple[str, float, int]]) -> None:
    """Radial spokes; each section's angular span is its share of word
    mass and the spoke length scales to that mass, normalized so the
    densest section reaches the outermost dome ring."""
    total_words = sum(words for _, words, _ in rows)
    max_words = max(words for _, words, _ in rows)
    angle = math.pi / 2  # start at 12 o'clock, sweep clockwise
    for index, (_name, words, _pages) in enumerate(rows):
        span = 2 * math.pi * words / total_words
        mid = angle - span / 2
        reach = 0.35 + 1.15 * words / max_words
        color = _PALETTE[index % len(_PALETTE)]
        ax.plot(
            [0, reach * math.cos(mid)],
            [0, reach * math.sin(mid)],
            lw=2.2,
            color=color,
            alpha=0.85,
            solid_capstyle="round",
        )
        # Faint annular band along the section's angular span.
        ax.add_patch(
            Wedge(
                (0, 0),
                reach,
                math.degrees(angle - span),
                math.degrees(angle),
                width=0.012,
                lw=0,
                facecolor=color,
                alpha=0.10,
            )
        )
        angle -= span


def _draw_page_dots(ax, rows: list[tuple[str, float, int]]) -> None:
    """One small dot per discovered page, angle-distributed within its
    section's arc; dots sit at one of two radii by section word mass
    (mass-dense sections ring farther out)."""
    total_words = sum(words for _, words, _ in rows)
    median_words = sorted(words for _, words, _ in rows)[len(rows) // 2]
    angle = math.pi / 2
    for index, (_name, words, pages) in enumerate(rows):
        span = 2 * math.pi * words / total_words
        radius = 1.42 if words >= median_words else 1.14
        color = _PALETTE[index % len(_PALETTE)]
        for dot_index in range(pages):
            dot_angle = angle - span * (dot_index + 0.5) / pages
            ax.plot(
                radius * math.cos(dot_angle),
                radius * math.sin(dot_angle),
                marker="o",
                ms=3.5,
                color=color,
                alpha=0.75,
                linestyle="none",
            )
        angle -= span


def _draw_center(ax) -> None:
    """Central convergence node: a bright core with a soft halo."""
    ax.add_patch(Circle((0, 0), 0.075, facecolor="#F0E442", alpha=0.25, lw=0))
    ax.add_patch(Circle((0, 0), 0.035, facecolor="#F0E442", lw=0))
    ax.add_patch(Circle((0, 0), 0.012, facecolor=_BACKGROUND, lw=0))


def _draw_typography(ax, analysis: dict, rows: list[tuple[str, float, int]]) -> None:
    """Title, subtitle, derived stats line, and the subtle Φ watermark."""
    total_words = int(sum(words for _, words, _ in rows))
    total_pages = int(analysis["inventory"]["discovered_pages"])
    ax.text(
        0,
        -1.72,
        "FractiSkills",
        ha="center",
        va="center",
        fontsize=54,
        color=_INK,
        family="DejaVu Sans",
    )
    ax.text(
        0,
        -1.90,
        "One Portable Agent Skill per Page · SS Vibelandia Omniversal Canvas",
        ha="center",
        va="center",
        fontsize=13,
        color="#E8F0FF",
    )
    ax.text(
        0,
        -2.06,
        f"{total_pages} pages · {len(rows)} sections · {total_words:,} words",
        ha="center",
        va="center",
        fontsize=11,
        color="#B9C4E8",
    )
    # Ghost glyph watermark behind the dome system.
    ax.text(
        0,
        0.02,
        "Φ",
        ha="center",
        va="center",
        fontsize=140,
        color=_INK,
        alpha=0.045,
        family="DejaVu Serif",
    )


def build_cover(analysis: dict, output_dir: str) -> str:
    """Render the manuscript cover PNG from the analysis record.

    Draws the "holographic nested domes" motif: golden-ratio nested arcs,
    twelve radial section spokes scaled by word mass
    (``analysis["sections"]``), one dot per page
    (``analysis["inventory"]["discovered_pages"]``) inside its section's
    arc, a central convergence node, a Φ watermark, and light-on-dark
    typography ("FractiSkills" title, "One Portable Agent Skill per Page ·
    SS Vibelandia Omniversal Canvas" subtitle, and a stats line derived
    from the analysis page/section/word totals). Fully deterministic; no
    RNG and no timestamps.

    Writes ``{output_dir}/figures/cover.png`` (2000 x 2800 px portrait at
    200 dpi, deep navy ``#0B1026`` ground) and returns the path string.
    The caller is responsible for copying the rendered file to the
    canonical committed asset (e.g. ``cover/FractiSkills_cover.png``).
    """
    Path(output_dir, "figures").mkdir(parents=True, exist_ok=True)
    out_path = str(Path(output_dir, "figures", "cover.png"))

    rows = _section_slices(analysis)
    fig = plt.figure(figsize=_FIGSIZE, facecolor=_BACKGROUND)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_facecolor(_BACKGROUND)
    ax.set_axis_off()
    # Data coordinates centered on the canvas; typography lives below the domes.
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-2.24, 2.56)
    ax.set_aspect("equal")

    _draw_nested_arcs(ax)
    _draw_spokes(ax, rows)
    _draw_page_dots(ax, rows)
    _draw_center(ax)
    _draw_typography(ax, analysis, rows)

    fig.savefig(out_path, dpi=_DPI, facecolor=_BACKGROUND)
    plt.close(fig)
    return out_path
