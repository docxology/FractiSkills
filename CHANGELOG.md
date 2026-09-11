# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Orchestration review pass: `section_for_path` moved to `profiles.py`
  (research layer no longer imports the acquisition module); `preflight`
  promoted to a CLI subcommand with thin scripts; `cmd_validate` dispatches
  to `pipeline.validate_skills_tree`; derived metrics (sitemap yield,
  augment ratio, mode depth, heavy/biggest section) computed once in the
  analysis record; dead code removed; every module, class, and function in
  `src/fractiskills/` documented.

## [0.1.0] - 2026-09-10

### Added

- Discovery stage: declared-sitemap enumeration plus one bounded,
  robots-respecting breadth-first crawl; redirect and canonical-duplicate
  alias resolution; mechanical section derivation from site paths.
- `AugmentedGenerator`: Skillarum deterministic skill bodies plus declared
  same-origin JSON document augmentation with per-attempt receipts.
- Render orchestration: one Skillarum profile per site section, one
  exact-page target per discovered page, loud per-section failure reporting.
- Tracked, reconciled skill library publication with harness discovery
  index.
- Research layer: aggregated analysis record, skills CSV, five deterministic
  figures with registry, manuscript token variables, and loud token binding.
- `fractiskills` CLI (`discover`, `render`, `publish`, `analyze`, `figures`,
  `research`, `validate`, `run`) and thin numbered scripts.
- Hermetic fixture-site test suite with a 90% branch-coverage gate on
  `src/`; opt-in live-site checks.