"""Manuscript hydration: token variables, binding, and the ordered research build.

Mirrors the parent-template contract: numbered chapter sources stay pristine
under ``manuscript/``; ``{{TOKEN}}`` placeholders are resolved into
``output/manuscript/`` with a receipt that fails loudly on unknown or
unresolved tokens.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from skillarum.pipeline import CACHE_VERSION, PIPELINE_VERSION

from .models import SiteInventory, load_json, try_load_json, write_json_atomic, write_text_atomic

MANUSCRIPT_TOKEN_PATTERN = re.compile(r"\{\{([A-Z][A-Z0-9_]+)\}\}")

_CHAPTER_ORDER = [
    "preamble.md",
    "00_abstract.md",
    "01_introduction.md",
    "02_background.md",
    "03_methods.md",
    "04_results.md",
    "05_visualizations.md",
    "06_skill_catalog.md",
    "07_discussion_and_limitations.md",
    "08_scope_and_related_work.md",
    "09_reproducibility.md",
    "10_glossary.md",
    "11_scope_summary.md",
    "99_references.md",
]


def _md_escape(value: object) -> str:
    """Escape a value for a Markdown table cell (pipes and newlines)."""
    return str(value).replace("|", r"\|").replace("\n", " ")


def _skill_catalog_table(analysis: dict) -> str:
    """Render the per-section skill catalog as a Markdown table with a
    totals footer."""
    by_area: dict[str, list[dict]] = {}
    for skill in analysis["skills"]["records"]:
        by_area.setdefault(skill["area"], []).append(skill)
    rows: list[str] = [
        "| Section | Skill | Source page | Words |",
        "| --- | --- | --- | --- |",
    ]
    for area in sorted(by_area):
        for skill in sorted(by_area[area], key=lambda item: item["skill"]):
            source = "; ".join(skill["source_urls"]) or "(unknown)"
            rows.append(
                f"| {_md_escape(area)} | {_md_escape(skill['skill'])} | "
                f"{_md_escape(source)} | {skill['word_count']} |"
            )
    rows.append(
        f"| **Total** | **{analysis['inventory']['discovered_pages']}** | "
        f"**{analysis['skills']['count']}** | **{analysis['skills']['total_words']}** |"
    )
    return "\n".join(rows)


def _section_table(analysis: dict) -> str:
    """Render per-section page/skill/word counts as a Markdown table with
    a totals footer."""
    rows = [
        "| Section | Pages | Skills | Skill words |",
        "| --- | --- | --- | --- |",
    ]
    for row in analysis["sections"]:
        rows.append(
            f"| {_md_escape(row['section'])} | {row['pages']} | {row['skills']} | {row['words']} |"
        )
    rows.append(
        f"| **Total** | **{analysis['inventory']['discovered_pages']}** | "
        f"**{analysis['skills']['count']}** | **{analysis['skills']['total_words']}** |"
    )
    return "\n".join(rows)


def _observation_window(analysis: dict) -> str:
    """Format the generated-at through published-at observation window, or
    the single timestamp, or ``unavailable``."""
    generated_at = analysis["inventory"].get("generated_at", "")
    published_at = analysis.get("publish_receipt", {}).get("published_at", "")
    if generated_at and published_at:
        return f"{generated_at} through {published_at} (UTC)"
    return generated_at or "unavailable"


def _indegree_table(analysis: dict) -> str:
    """Render the top inbound-link pages as a Markdown table."""
    rows = [
        "| Page | Section | Inbound links |",
        "| --- | --- | --- |",
    ]
    for row in analysis["indegree"]["top"]:
        rows.append(
            f"| {_md_escape(row['path'])} | {_md_escape(row['section'])} | {row['inbound']} |"
        )
    return "\n".join(rows)


def _depth_table(analysis: dict) -> str:
    """Render the crawl-depth histogram with per-depth share, unfetched
    sorted last."""
    histogram = analysis["depth_histogram"]
    total = sum(histogram.values()) or 1
    rows = [
        "| BFS depth | Pages | Share |",
        "| --- | --- | --- |",
    ]
    keys = sorted(histogram, key=lambda k: (k == "unfetched", int(k) if k.isdigit() else 99))
    for key in keys:
        label = "unfetched" if key == "unfetched" else f"depth {key}"
        rows.append(f"| {label} | {histogram[key]} | {100 * histogram[key] / total:.0f}% |")
    rows.append(f"| **Total** | **{total}** | **100%** |")
    return "\n".join(rows)


def build_variables(analysis: dict, figure_registry: dict | None = None) -> dict[str, str]:
    """Return every manuscript token value from the persisted analysis.

    Derived scalars (yield, ratio, mode depth, heavy/biggest section) are
    read flat from the analysis record; figures contribute
    ``FIGURE_<ID>_CAPTION/_ALT`` tokens."""
    """Return every manuscript token value from the persisted analysis."""
    inventory = analysis["inventory"]
    skills = analysis["skills"]
    augmentation = analysis["augmentation"]
    variables = {
        "PROJECT_NAME": "FractiSkills",
        "SITE_NAME": "SS Vibelandia Omniversal Canvas",
        "BASE_URL": inventory["base_url"],
        "SITEMAP_URL": inventory["sitemap_url"],
        "TOTAL_PAGES": str(inventory["discovered_pages"]),
        "SITEMAP_URLS": str(inventory["sitemap_url_count"]),
        "CRAWL_ACCEPTED": str(inventory["crawl_accepted_count"]),
        "VIA_SITEMAP": str(inventory["via_sitemap"]),
        "VIA_CRAWL_ONLY": str(inventory["via_crawl_only"]),
        "ALIAS_PAGES": str(inventory["alias_pages"]),
        "SECTION_COUNT": str(len(analysis["sections"])),
        "SECTION_TABLE": _section_table(analysis),
        "SKILL_COUNT": str(skills["count"]),
        "TOTAL_WORDS": str(skills["total_words"]),
        "MEDIAN_WORDS": f"{skills['median_words']:.0f}",
        "TOTAL_CHARS": str(skills["total_chars"]),
        "SKILL_CATALOG": _skill_catalog_table(analysis),
        "AUGMENT_ATTEMPTS": str(augmentation["attempts"]),
        "AUGMENT_OK": str(augmentation["ok"]),
        "AUGMENT_FAILED": str(augmentation["failed"]),
        "AUGMENT_CHARS": str(augmentation["document_text_chars"]),
        "REQUEST_COUNT": str(analysis["runs"].get("request_count", 0)),
        "EVIDENCE_ORIGINS": ", ".join(analysis["runs"].get("evidence_origins", [])) or "unknown",
        "PIPELINE_VERSION": PIPELINE_VERSION,
        "CACHE_VERSION": str(CACHE_VERSION),
        "OBSERVATION_WINDOW": _observation_window(analysis),
        "TOP_INDEGREE_TABLE": _indegree_table(analysis),
        "DEPTH_TABLE": _depth_table(analysis),
        "TOP_DEPTH": str(
            max((int(k) for k in analysis["depth_histogram"] if k.isdigit()), default=0)
        ),
        "DEPTH_MODE_DEPTH": str(analysis["mode_depth"]),
        "DEPTH_MODE_SHARE": f"{analysis['mode_depth_share']:.0f}%",
        "LINKED_PAGES": str(analysis["indegree"]["linked_pages"]),
        "AUGMENT_SKILLS": str(skills["augmented_count"]),
        "STATIC_SKILLS": str(skills["static_count"]),
        "MEDIAN_WORDS_AUGMENTED": f"{skills['median_words_augmented']:.0f}",
        "MEDIAN_WORDS_STATIC": f"{skills['median_words_static']:.0f}",
        "AUGMENT_RATIO": f"{analysis['augment_ratio']:.1f}",
        "HEAVY_SECTION": str(analysis["heavy_section"]),
        "BIGGEST_SECTION": str(analysis["biggest_section"]),
        "SITEMAP_YIELD": f"{analysis['sitemap_yield']:.0f}%",
    }
    for figure in (figure_registry or {}).get("figures", []):
        prefix = "FIGURE_" + str(figure["figure_id"]).replace("-", "_").upper()
        variables[f"{prefix}_CAPTION"] = str(figure.get("caption", ""))
        variables[f"{prefix}_ALT"] = str(figure.get("alt_text", ""))
    return variables


def validate_manuscript_dir(manuscript_dir: str) -> list[str]:
    """Static token-syntax validation of the chapter sources."""
    errors: list[str] = []
    source_root = Path(manuscript_dir)
    for path in sorted(source_root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "{{" in MANUSCRIPT_TOKEN_PATTERN.sub("", text):
            errors.append(f"{path.name}: malformed token; use exact UPPERCASE_KEY syntax")
    return errors


def bind_manuscript(
    *,
    manuscript_dir: str,
    output_dir: str,
    variables: dict[str, str],
) -> dict:
    """Resolve tokens into ``output/manuscript/`` and return the binding receipt."""
    source_root = Path(manuscript_dir)
    destination_root = Path(output_dir) / "manuscript"
    destination_root.mkdir(parents=True, exist_ok=True)
    chapters = [
        path
        for path in source_root.glob("*.md")
        if path.name in _CHAPTER_ORDER or path.name.startswith(("0", "9"))
    ]
    ordered = sorted(chapters, key=lambda path: _chapter_sort_key(path.name))
    used: dict[str, list[str]] = {}
    rendered: list[str] = []
    for path in ordered:
        text = path.read_text(encoding="utf-8")
        tokens = MANUSCRIPT_TOKEN_PATTERN.findall(text)
        unknown = sorted(set(tokens) - set(variables))
        if unknown:
            raise ValueError(f"{path.name} contains unknown manuscript tokens: {unknown}")
        resolved = MANUSCRIPT_TOKEN_PATTERN.sub(lambda match: variables[match.group(1)], text)
        if "{{" in resolved:
            raise ValueError(f"{path.name} contains unresolved manuscript tokens")
        write_text_atomic(str(destination_root / path.name), resolved)
        used[path.name] = sorted(set(tokens))
        rendered.append(path.name)
    for companion in ("config.yaml", "references.bib", "layer_contract.yaml"):
        source = source_root / companion
        if source.is_file():
            shutil.copyfile(source, destination_root / companion)
    receipt = {
        "bound_at_destination": str(destination_root),
        "rendered_chapters": rendered,
        "used_tokens": used,
    }
    write_json_atomic(f"{output_dir}/data/manuscript_receipt.json", receipt)
    return receipt


def _chapter_sort_key(name: str) -> tuple[int, str]:
    """Return the canonical chapter position, or ``(99, name)`` for files
    outside the canonical order (name breaks ties)."""
    try:
        return (_CHAPTER_ORDER.index(name), name)
    except ValueError:
        return (99, name)


def load_inventory(output_dir: str) -> SiteInventory:
    """Load and validate ``data/inventory.json`` from an output directory."""
    value = load_json(f"{output_dir}/data/inventory.json")
    return SiteInventory.from_dict(value)


def run_research_hook(project_dir: str) -> int:
    """Parent-template pre-render hook entry: rebuild the research package
    and translate a no-token binding into a nonzero exit.

    Returns 0 on success, 1 when the bound chapters carry no tokens.
    """
    import sys

    project = Path(project_dir)
    receipt = build_research_package(str(project), str(project / "output"))
    if not any(receipt["receipt"]["used_tokens"].values()):
        print("warning: no manuscript tokens were bound", file=sys.stderr)
        return 1
    print(f"bound {len(receipt['receipt']['rendered_chapters'])} chapters")
    return 0


def build_research_package(
    project_dir: str, output_dir: str, *, skills_dir: str | None = None
) -> dict:
    """Ordered offline research build: analyze, figures, variables, bind.

    This is the parent-template pre-render hook target (see
    ``scripts/z_generate_manuscript_variables.py``). ``skills_dir`` defaults
    to the tracked tree at the project root.
    """
    from .analysis import build_analysis
    from .cover import build_cover
    from .figures import build_figures

    project = Path(project_dir)
    inventory = load_inventory(output_dir)
    resolved_skills_dir = skills_dir or str(project / "skills")
    render_summary = try_load_json(f"{output_dir}/data/render_summary.json")
    publish_receipt = try_load_json(f"{output_dir}/data/publish_receipt.json")
    analysis = build_analysis(
        output_dir=output_dir,
        skills_dir=resolved_skills_dir,
        inventory=inventory,
        render_summary=render_summary,
        publish_receipt=publish_receipt,
    )
    registry = build_figures(analysis, output_dir=output_dir)
    cover_path = build_cover(analysis, output_dir)
    cover_dir = project / "cover"
    cover_dir.mkdir(exist_ok=True)
    shutil.copyfile(cover_path, cover_dir / "FractiSkills_cover.png")
    variables = build_variables(analysis, {"figures": registry})
    write_json_atomic(
        f"{output_dir}/data/manuscript_variables.json",
        {key: value for key, value in sorted(variables.items())},
    )
    errors = validate_manuscript_dir(str(project / "manuscript"))
    if errors:
        raise ValueError("manuscript validation failed: " + "; ".join(errors))
    receipt = bind_manuscript(
        manuscript_dir=str(project / "manuscript"),
        output_dir=output_dir,
        variables=variables,
    )
    return {
        "analysis_summary": True,
        "figures": len(registry),
        "cover": cover_path,
        "receipt": receipt,
    }
