# TODO

Backlog with acceptance lines. A line is done when its acceptance holds.

- [ ] **Refresh observation cadence.** Rerun the full pipeline on a weekly
  cadence and attach the new dated receipts to each release.
  Acceptance: a dated `render_summary.json` with all sections `ok`.
- [ ] **Browser-backed fetcher.** Skillarum's v1 fetcher protocol is the
  boundary; a browser-backed fetcher would serve JS-only pages that lack
  declared bindings. Acceptance: an opt-in fetcher swap that keeps fixture
  tests hermetic.
- [ ] **Inventory diff report.** Compare two inventories (added/removed/
  renamed pages) and surface it in the analysis record.
  Acceptance: `render` on an unchanged site yields an empty diff.
- [ ] **Per-skill effect annotations review.** The deterministic effect floor
  is `readonly` for the whole corpus; spot-check any pages whose source
  instructions could raise the floor. Acceptance: annotation audit recorded
  in `data/claim_ledger.yaml`.
- [ ] **PyPI publication.** Publish the `fractiskills` package once the
  skill library stabilizes. Acceptance: `pip install fractiskills` renders
  the fixture pipeline.

## Workflowz review — 2026-11-10

Coverage is limited to the supplied packet: project guidance, README and existing TODO; Python/runtime metadata; the visible orchestration, CLI, profile-building, and script-dispatch excerpts; and the opt-in live-site test. All 30 Python candidate files and the full 1,700-file repository were not available. The review found no concrete, behaviorally verifiable improvement supported by an exact visible path:line. Per-section exception isolation in `pipeline.py`, fixture origin handling in `cli.py`, opt-in live testing, and thin script wrappers are explicit design choices, not silent production substitutes. The packet does not expose `.python-version` as `3.15.2`, so no interpreter-pin change is asserted. Re-review on a concrete failure or when omitted source/test content or changed runtime/deployment constraints are supplied.
