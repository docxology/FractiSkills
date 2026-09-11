"""FractiSkills command-line interface: thin dispatch over the package stages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import SiteSpec, resolve_evidence_origin

# Backward-compatible alias for scripts that imported the CLI private.
_resolve_evidence_origin = resolve_evidence_origin


def _spec(args: argparse.Namespace) -> SiteSpec:
    """Load the SiteSpec named by ``args.spec``."""
    return SiteSpec.load(args.spec)


def _inventory(output_dir: str):
    """Load the persisted inventory from an output directory (no acquisition)."""
    from .publication import load_inventory

    return load_inventory(output_dir)


def _analysis_record(args: argparse.Namespace) -> dict:
    """Build the analysis record from the artifacts an output dir holds."""
    from .analysis import build_analysis
    from .models import try_load_json

    return build_analysis(
        output_dir=args.output_dir,
        skills_dir=args.skills_dir,
        inventory=_inventory(args.output_dir),
        render_summary=try_load_json(f"{args.output_dir}/data/render_summary.json"),
        publish_receipt=try_load_json(f"{args.output_dir}/data/publish_receipt.json"),
    )


def cmd_preflight(args: argparse.Namespace) -> int:
    """Verify the site spec loads, report bindings and origin policy, and
    confirm the output directory is writable. Exits 0 on a loadable spec."""
    spec = _spec(args)
    if args.json:
        print(
            json.dumps(
                {
                    "profile_id": spec.profile_id,
                    "base_url": spec.base_url,
                    "bindings": len(spec.bindings),
                    "origin": resolve_evidence_origin("auto", spec.base_url),
                },
                indent=1,
            )
        )
    else:
        print(f"spec ok: {spec.profile_id} -> {spec.base_url}")
        print(f"bindings: {len(spec.bindings)} declared")
        print(f"origin resolution: {resolve_evidence_origin('auto', spec.base_url)}")
        Path(args.output_dir).mkdir(exist_ok=True)
        print("output/ writable")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    """Run sitemap+crawl discovery and persist the inventory; prints section
    counts. Exit 1 when the crawl hit a limit (incomplete)."""
    from .discover import discover_site

    spec = _spec(args)
    inventory, path = discover_site(
        spec, output_dir=args.output_dir, allow_private_hosts=args.allow_private
    )
    payload = {
        "inventory_path": path,
        "discovered_pages": len(inventory.entries),
        "sitemap_url_count": inventory.sitemap_url_count,
        "crawl_accepted_count": inventory.crawl_accepted_count,
        "sections": {name: len(entries) for name, entries in inventory.sections().items()},
        "incomplete": inventory.incomplete,
        "warnings": list(inventory.crawl_warnings),
    }
    if args.json:
        print(json.dumps(payload, indent=1))
    else:
        print(f"discovered {payload['discovered_pages']} pages -> {path}")
        for name, count in payload["sections"].items():
            print(f"  {name}: {count}")
        if payload["incomplete"]:
            print("WARNING: discovery crawl hit a limit; inventory may be incomplete")
    return 1 if payload["incomplete"] else 0


def cmd_render(args: argparse.Namespace) -> int:
    """Render all sections from the persisted inventory and write
    render_summary.json; per-section status to stdout, failures to stderr.
    Exit 1 when any section failed."""
    from .pipeline import render_site

    spec = _spec(args)
    inventory = _inventory(args.output_dir)
    evidence_origin = resolve_evidence_origin(args.evidence_origin, spec.base_url)
    allow_private = evidence_origin == "fixture" or getattr(args, "allow_private", False)
    summary = render_site(
        inventory,
        spec,
        output_dir=args.output_dir,
        evidence_origin=evidence_origin,
        refresh=args.refresh,
        force_process=args.force_process,
        allow_private_hosts=allow_private,
    )
    rendered_total = sum(len(run.rendered) for run in summary.runs)
    payload = {
        "evidence_origin": summary.evidence_origin,
        "runs": [run.to_dict() for run in summary.runs],
        "rendered_total": rendered_total,
    }
    if args.json:
        print(json.dumps(payload, indent=1))
    else:
        print(
            f"rendered {rendered_total} skills "
            f"(origin={summary.evidence_origin}, refresh={args.refresh})"
        )
        for run in summary.runs:
            status = "ok" if run.ok else f"FAILED: {run.error}"
            print(f"  {run.section}: {len(run.rendered)}/{run.target_count} — {status}")
    failed = [run for run in summary.runs if not run.ok]
    for run in failed:
        print(f"section {run.section} failed: {run.error}", file=sys.stderr)
    return 1 if failed else 0


def cmd_publish(args: argparse.Namespace) -> int:
    """Publish rendered packages into the tracked skills tree and write
    publish_receipt.json. Always exits 0."""
    from .pipeline import publish_skills

    receipt = publish_skills(args.output_dir, args.skills_dir)
    payload = {
        "count": receipt["count"],
        "skills_dir": receipt["skills_dir"],
        "index_path": receipt["index_path"],
    }
    if args.json:
        print(json.dumps(payload, indent=1))
    else:
        print(f"published {payload['count']} skills -> {payload['skills_dir']}")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Aggregate persisted artifacts into the analysis record and print it;
    never acquires. Always exits 0."""
    analysis = _analysis_record(args)
    if args.json:
        print(json.dumps(analysis["inventory"] | {"sections": analysis["sections"]}, indent=1))
    else:
        print(
            f"analyzed {analysis['inventory']['discovered_pages']} pages, "
            f"{analysis['skills']['count']} skills, "
            f"{analysis['skills']['total_words']} words"
        )
    return 0


def cmd_figures(args: argparse.Namespace) -> int:
    """Build the analysis record, render its figures, and print the
    registry. Always exits 0."""
    from .figures import build_figures

    analysis = _analysis_record(args)
    registry = build_figures(analysis, output_dir=args.output_dir)
    if args.json:
        print(json.dumps(registry, indent=1))
    else:
        for figure in registry:
            print(f"  {figure['figure_id']} -> {figure['path']}")
    return 0


def cmd_research(args: argparse.Namespace) -> int:
    """Bind analysis, figures, and variables into the research package rooted
    at the cwd and print the receipt. Always exits 0."""
    from .publication import build_research_package

    receipt = build_research_package(str(Path.cwd()), args.output_dir)
    if args.json:
        print(json.dumps(receipt, indent=1))
    else:
        print(f"research package built: {receipt['figures']} figures bound")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate every tracked skill package and rewrite the index; exit 1 on
    any validation failure (printed to stderr)."""
    from .pipeline import validate_skills_tree

    count, failures = validate_skills_tree(args.skills_dir)
    if args.json:
        print(json.dumps({"validated": count, "failures": failures}, indent=1))
    else:
        print(f"validated {count} skill packages")
        for failure in failures:
            print(f"  FAILED {failure}", file=sys.stderr)
    return 1 if failures else 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run discover, render, publish, research in sequence, stopping at the
    first nonzero exit code."""
    for command in (cmd_discover, cmd_render, cmd_publish, cmd_research):
        code = command(args)
        if code != 0:
            return code
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the fractiskills parser; all subcommands share --spec,
    --output-dir, --skills-dir, and --json defaults."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--spec",
        default="data/sources/ssvibelandia.yaml",
        help="site spec YAML (default: data/sources/ssvibelandia.yaml)",
    )
    common.add_argument(
        "--output-dir",
        default="output",
        help="generated-output root (default: output)",
    )
    common.add_argument(
        "--skills-dir",
        default="skills",
        help="tracked canonical skills tree (default: skills)",
    )
    common.add_argument("--json", action="store_true", help="machine-readable output")

    parser = argparse.ArgumentParser(
        prog="fractiskills",
        description="One portable agent SKILL per page of the SS Vibelandia Canvas",
        parents=[common],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser(
        "preflight", help="verify the site spec and output writability", parents=[common]
    )
    preflight.set_defaults(func=cmd_preflight)

    discover = sub.add_parser(
        "discover", help="sitemap + bounded crawl inventory", parents=[common]
    )
    discover.add_argument(
        "--allow-private",
        action="store_true",
        help="allow private/loopback hosts (fixture servers only)",
    )
    discover.set_defaults(func=cmd_discover)

    render = sub.add_parser(
        "render", help="render one SKILL.md per discovered page", parents=[common]
    )
    render.add_argument(
        "--refresh", action="store_true", help="refetch instead of using acquisition cache"
    )
    render.add_argument(
        "--force-process", action="store_true", help="rerun the generator even on cache hit"
    )
    render.add_argument(
        "--evidence-origin",
        choices=["auto", "live", "fixture", "unknown"],
        default="auto",
        help="evidence origin recorded in run manifests (default: auto)",
    )
    render.set_defaults(func=cmd_render)

    publish = sub.add_parser(
        "publish",
        help="validate + copy rendered skills into the tracked tree",
        parents=[common],
    )
    publish.set_defaults(func=cmd_publish)

    analyze = sub.add_parser(
        "analyze",
        help="aggregate persisted artifacts into the analysis record",
        parents=[common],
    )
    analyze.set_defaults(func=cmd_analyze)

    figures = sub.add_parser(
        "figures", help="render visualizations from the analysis", parents=[common]
    )
    figures.set_defaults(func=cmd_figures)

    research = sub.add_parser(
        "research", help="analyze + figures + manuscript binding", parents=[common]
    )
    research.set_defaults(func=cmd_research)

    validate = sub.add_parser(
        "validate", help="validate every tracked skill package", parents=[common]
    )
    validate.set_defaults(func=cmd_validate)

    run = sub.add_parser(
        "run", help="full pipeline: discover, render, publish, research", parents=[common]
    )
    run.add_argument("--refresh", action="store_true")
    run.add_argument("--force-process", action="store_true")
    run.add_argument("--allow-private", action="store_true")
    run.add_argument(
        "--evidence-origin",
        choices=["auto", "live", "fixture", "unknown"],
        default="auto",
    )
    run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse argv and dispatch to the selected ``cmd_*``; returns its exit
    code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
