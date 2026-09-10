"""FractiSkills stage orchestration: discover, render sections, publish skills."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from skillarum.render import validate_skill_package, write_skill_index

from .generator import AugmentedGenerator
from .models import (
    RenderSummary,
    SectionRun,
    SiteInventory,
    SiteSpec,
    write_json_atomic,
)
from .profiles import build_section_profiles


def render_site(
    inventory: SiteInventory,
    spec: SiteSpec,
    *,
    output_dir: str,
    backend: str = "deterministic",
    evidence_origin: str = "live",
    refresh: bool = False,
    force_process: bool = False,
    allow_private_hosts: bool = False,
) -> RenderSummary:
    """Render one skill per inventory page, one Skillarum profile per section."""
    from skillarum.pipeline import run_profile

    profiles = build_section_profiles(inventory, spec, allow_private_hosts=allow_private_hosts)
    receipts_path = Path(output_dir) / "data" / "augmentation_receipts.jsonl"
    runs: list[SectionRun] = []
    for profile in profiles:
        generator = AugmentedGenerator(
            base_url=spec.base_url,
            bindings=spec.bindings,
            augment_timeout_seconds=spec.augment_timeout_seconds,
            allow_private_hosts=allow_private_hosts,
            receipts_path=str(receipts_path),
        )
        try:
            rendered = run_profile(
                profile,
                output_dir=output_dir,
                backend=backend,
                refresh=refresh,
                force_process=force_process,
                generator=generator,
                evidence_origin=evidence_origin,
            )
            runs.append(
                SectionRun(
                    section=profile.area,
                    profile_id=profile.id,
                    run_id=_latest_run_id(output_dir, profile.id),
                    rendered=tuple(str(path) for path in rendered),
                    target_count=len(profile.targets),
                    ok=True,
                )
            )
        except Exception as exc:  # noqa: BLE001 - one failing section must not stop the others
            runs.append(
                SectionRun(
                    section=profile.area,
                    profile_id=profile.id,
                    run_id=_latest_run_id(output_dir, profile.id, failed=True),
                    target_count=len(profile.targets),
                    ok=False,
                    error=f"{type(exc).__name__}: {exc}"[:500],
                )
            )
    summary = RenderSummary(
        generated_at=datetime.now(timezone.utc).isoformat(),
        backend=backend,
        evidence_origin=evidence_origin,
        runs=tuple(runs),
    )
    write_json_atomic(f"{output_dir}/data/render_summary.json", summary.to_dict())
    return summary


def _latest_run_id(output_dir: str, profile_id: str, *, failed: bool = False) -> str:
    """Return the newest run directory name for one profile id."""
    runs_root = Path(output_dir) / "runs"
    if not runs_root.is_dir():
        return ""
    prefix = profile_id
    candidates = [
        run_dir
        for run_dir in runs_root.iterdir()
        if run_dir.name.startswith(prefix) and run_dir.is_dir()
    ]
    if failed:
        candidates = [run_dir for run_dir in candidates if (run_dir / "failure.json").exists()]
    else:
        candidates = [run_dir for run_dir in candidates if (run_dir / "manifest.json").exists()]
    if not candidates:
        return ""
    return max(candidates, key=lambda run_dir: run_dir.stat().st_mtime).name


def publish_skills(
    output_dir: str,
    skills_dir: str,
) -> dict:
    """Validate and copy rendered packages into the tracked skills tree.

    Reconciles: packages absent from the current render are removed so the
    tracked tree is always a clean cut of the latest run. Returns the receipt.
    """
    source_root = Path(output_dir) / "skills"
    destination_root = Path(skills_dir)
    if not source_root.is_dir():
        raise ValueError(f"no rendered skills directory: {source_root}")
    published: list[dict] = []
    staged: set[tuple[str, str]] = set()
    for area_dir in sorted(source_root.iterdir()):
        if not area_dir.is_dir() or area_dir.name.startswith("."):
            continue
        for skill_dir in sorted(area_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue
            validate_skill_package(skill_dir / "SKILL.md")
            manifest = json.loads((skill_dir / "manifest.json").read_text(encoding="utf-8"))
            destination = destination_root / area_dir.name / skill_dir.name
            if destination.exists():
                shutil.rmtree(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(skill_dir, destination)
            staged.add((area_dir.name, skill_dir.name))
            published.append(
                {
                    "area": area_dir.name,
                    "skill": skill_dir.name,
                    "skill_name": manifest.get("skill_name"),
                    "target_id": manifest.get("target_id"),
                    "source_urls": manifest.get("source_urls", []),
                    "generator": manifest.get("generator"),
                }
            )
    # Reconcile stale packages that a previous publish left behind.
    if destination_root.exists():
        for area_dir in sorted(destination_root.iterdir()):
            if not area_dir.is_dir():
                continue
            for skill_dir in sorted(area_dir.iterdir()):
                if skill_dir.is_dir() and (area_dir.name, skill_dir.name) not in staged:
                    shutil.rmtree(skill_dir)
    index_path = write_skill_index(destination_root)
    receipt = {
        "published_at": datetime.now(timezone.utc).isoformat(),
        "skills_dir": str(destination_root),
        "index_path": str(index_path),
        "count": len(published),
        "skills": sorted(published, key=lambda item: (item["area"], item["skill"])),
    }
    write_json_atomic(f"{output_dir}/data/publish_receipt.json", receipt)
    return receipt
