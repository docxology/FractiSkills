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
