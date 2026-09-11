# Operations runbook

## Full live run (from clean checkout)

```bash
uv sync --extra dev
uv run python scripts/00_preflight.py
uv run python scripts/10_discover.py            # ~2.5 min against the real site
uv run python scripts/20_render_skills.py --refresh --json
uv run python scripts/30_publish_skills.py --json
uv run python scripts/40_analyze.py
uv run python scripts/50_figures.py --json
uv run python scripts/60_validate.py
```

or one command:

```bash
uv run python -m fractiskills run --refresh --json
```

## Idempotency and recovery

- Acquisition is cached under `output/.cache/fetches/` with ETag/Last-Modified
  conditional revalidation; reruns revalidate instead of refetching bodies.
- Drafts are cached per prepared-corpus + generator fingerprint; `--refresh`
  refetches, `--force-process` reruns the generator on unchanged input.
- A failed section run leaves `output/runs/<run-id>/failure.json` for safe
  diagnosis; rerun `render` (without `--refresh`) to reuse healthy targets.

## Incremental refresh

1. `uv run python scripts/10_discover.py` — refresh the inventory.
2. `uv run python scripts/20_render_skills.py --refresh` — new dated receipts.
3. `uv run python scripts/30_publish_skills.py` — reconcile the tracked tree.
4. `uv run python scripts/40_analyze.py && uv run python scripts/50_figures.py`.
5. Inspect `output/data/render_summary.json` for failed sections; a failed
   section means a page died between discovery and render — rerun discovery.
6. If the page that triggered the refresh is client-rendered, add its
   binding row to `data/sources/ssvibelandia.yaml` (`match_path` +
   `api_template` with `{id}`/`{last_segment}` placeholders) *before*
   step 2; without a binding it renders as a thin shell with a warning
   receipt instead of the real document.
7. A new top-level path segment creates its section automatically — a new
   source profile and a new `skills/<area>/` output area follow from the
   path alone; no registration step exists.
8. Final step: update `data/claim_ledger.yaml` rows for any numbers that
   changed — the parent evidence gate is fail-closed and rejects
   stale/unsupported values — then rerun `scripts/40_analyze.py` and
   `scripts/50_figures.py` so the figure registry and the analysis agree.

## Parent-template rendering

FractiSkills is visible to the parent template through the projects symlink
tree (`template/projects/ongoing/docxology/FractiSkills`). Pre-render,
`scripts/z_generate_manuscript_variables.py` rebuilds the research package
(analysis, figures, variables, binding) so PDF/HTML render against current
artifacts.

### Template render path (managed mirror)

PDF/HTML render and validation run through the template's managed
`_`-category mirror, which is the only alias the parent provenance binder
authorizes for a nested ongoing project (intermediate symlinks are rejected
with `PROJECT_LINK_INVALID`):

```bash
cd ../template
uv run python scripts/pipeline/stage_03_render.py --project ongoing/_fracti/FractiSkills
uv run python scripts/pipeline/stage_04_validate.py --project ongoing/_fracti/FractiSkills
```

`template/projects/ongoing/_fracti/FractiSkills` is a leaf symlink to this
checkout inside a real `_fracti/` category directory (the engine's documented
`projects/<lifecycle>/_<category>/<name>` shape). Outputs land in this
project's `output/pdf/` and `output/web/`.

### Claim ledger

`data/claim_ledger.yaml` follows the parent engine's evidence-registry
claim-ledger contract (`claims[].claim_id/value/artifact_path`); it admits
every prose number in the manuscript, including HTTP 400 (the no-`?id=`
reader failure) and the 88.9% sitemap-only miss rate.

## Doctor-style checks

- Spec loads and bindings are absolute paths: `scripts/00_preflight.py`.
- Every tracked package validates: `scripts/60_validate.py` (nonzero exit on
  any failure).
- Inventory completeness: `output/data/inventory.json` `incomplete` flag plus
  crawl warnings; unresolved sitemap URLs appear as recorded notes.