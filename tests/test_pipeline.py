"""End-to-end pipeline test on the fixture site: render, publish, research."""

from __future__ import annotations

from pathlib import Path

import pytest
from skillarum.render import validate_skill_package

from fractiskills.analysis import build_analysis
from fractiskills.figures import build_figures
from fractiskills.models import load_json
from fractiskills.pipeline import publish_skills, render_site
from fractiskills.publication import build_research_package

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_full_pipeline(loaded_spec, fixture_inventory, tmp_path: Path):
    inventory, output_dir, _ = fixture_inventory
    summary = render_site(
        inventory,
        loaded_spec,
        output_dir=output_dir,
        evidence_origin="fixture",
        allow_private_hosts=True,
    )
    skills_dir = str(tmp_path / "skills")
    receipt = publish_skills(output_dir, skills_dir)
    return inventory, output_dir, summary, receipt


def test_render_publishes_one_skill_per_page(loaded_spec, fixture_inventory, tmp_path) -> None:
    inventory, _, summary, receipt = _run_full_pipeline(loaded_spec, fixture_inventory, tmp_path)
    assert all(run.ok for run in summary.runs)
    assert sum(len(run.rendered) for run in summary.runs) == len(inventory.entries)
    assert receipt["count"] == len(inventory.entries)
    assert summary.evidence_origin == "fixture"


def test_published_packages_validate_and_carry_provenance(
    loaded_spec, fixture_inventory, tmp_path
) -> None:

    _, output_dir, _, receipt = _run_full_pipeline(loaded_spec, fixture_inventory, tmp_path)
    for skill in receipt["skills"]:
        package_root = Path(receipt["skills_dir"]) / skill["area"] / skill["skill"]
        validate_skill_package(package_root / "SKILL.md")
        manifest = load_json(str(package_root / "manifest.json"))
        assert manifest["source_urls"]
        assert manifest["profile_id"].startswith("fixturesite-")


def test_augmented_skill_carries_document(loaded_spec, fixture_inventory, tmp_path) -> None:
    _, _, _, receipt = _run_full_pipeline(loaded_spec, fixture_inventory, tmp_path)
    reader = next(s for s in receipt["skills"] if s["target_id"] == "reader-html-id-doc1")
    skill_md = (
        Path(receipt["skills_dir"]) / reader["area"] / reader["skill"] / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "Document One · Real Paper" in skill_md
    assert "Dynamic document retrieved from" in skill_md


def test_publish_reconciles_stale_packages(loaded_spec, fixture_inventory, tmp_path) -> None:
    _, output_dir, _, receipt = _run_full_pipeline(loaded_spec, fixture_inventory, tmp_path)
    skills_root = Path(receipt["skills_dir"])
    stale = skills_root / "Core" / "Stale-Thing"
    stale.mkdir(parents=True, exist_ok=True)
    (stale / "SKILL.md").write_text("---\nname: stale\n---\nbody\n", encoding="utf-8")
    publish_skills(output_dir, str(skills_root))
    assert not stale.exists()


def test_analysis_counts_match_published_tree(loaded_spec, fixture_inventory, tmp_path) -> None:
    inventory, output_dir, _, receipt = _run_full_pipeline(loaded_spec, fixture_inventory, tmp_path)
    analysis = build_analysis(
        output_dir=output_dir,
        skills_dir=receipt["skills_dir"],
        inventory=inventory,
        render_summary=load_json(f"{output_dir}/data/render_summary.json"),
        publish_receipt=receipt,
    )
    assert analysis["skills"]["count"] == len(inventory.entries)
    assert analysis["inventory"]["discovered_pages"] == len(inventory.entries)
    assert analysis["augmentation"]["attempts"] >= 1
    assert analysis["augmentation"]["failed"] == 0
    assert analysis["runs"]["evidence_origins"] == ["fixture"]
    assert (Path(output_dir) / "data" / "skills.csv").is_file()


def test_figures_and_research_package_bind(loaded_spec, fixture_inventory, tmp_path) -> None:

    inventory, output_dir, _, receipt = _run_full_pipeline(loaded_spec, fixture_inventory, tmp_path)
    analysis = build_analysis(
        output_dir=output_dir,
        skills_dir=receipt["skills_dir"],
        inventory=inventory,
        render_summary=load_json(f"{output_dir}/data/render_summary.json"),
        publish_receipt=receipt,
    )
    registry = build_figures(analysis, output_dir=output_dir)
    assert len(registry) == 10
    for figure in registry:
        assert Path(figure["path"]).is_file()
    variables_receipt = build_research_package(
        str(REPO_ROOT), output_dir, skills_dir=receipt["skills_dir"]
    )
    assert variables_receipt["figures"] == 10
    bound = Path(output_dir) / "manuscript"
    assert (bound / "00_abstract.md").is_file()
    assert "{{" not in (bound / "00_abstract.md").read_text(encoding="utf-8")
    catalog = (bound / "06_skill_catalog.md").read_text(encoding="utf-8")
    assert "reader.html?id=doc1" in catalog


def test_unknown_token_fails_loudly(loaded_spec, fixture_inventory, tmp_path) -> None:
    inventory, output_dir, _, receipt = _run_full_pipeline(loaded_spec, fixture_inventory, tmp_path)
    from fractiskills.publication import bind_manuscript

    with pytest.raises(ValueError, match="unknown manuscript tokens"):
        bind_manuscript(
            manuscript_dir=str(REPO_ROOT / "manuscript"),
            output_dir=output_dir,
            variables={"ONLY_ONE": "x"},
        )
