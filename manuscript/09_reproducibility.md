# Reproducibility {#sec:reproducibility}

The artifact regenerates from a clean checkout. Setup: `uv sync --extra dev`. Staged execution runs the numbered scripts in order — `scripts/00_preflight.py` (environment and site-spec checks), `10_discover.py`, `20_render_skills.py --refresh`, `30_publish_skills.py`, `40_analyze.py`, `50_figures.py`, `60_validate.py` — or the equivalent one-command entry point, `uv run python -m fractiskills run --refresh --json`. On the reference machine the full pipeline — discovery plus render — completed in roughly seven and a half minutes wall-clock (the published observation window bounds it); analysis, figures, and binding are near-instant.

## Caching and revalidation

HTTP fetches cache under `output/.cache/fetches/` and revalidate conditionally with ETag/Last-Modified, so unchanged pages cost one 304 per URL. The draft cache is keyed by prepared-corpus hash plus generator fingerprint: re-runs reuse rendered drafts until either the corpus or the `AugmentedGenerator` changes. `--refresh` re-renders within cache discipline; `--force-process` bypasses draft reuse entirely. Stage identities are stable run ids, not timestamps, so repeated runs address the same record idempotently.

## Failure recovery and evidence origins

A section that fails hard persists `failure.json` and aborts its stage — no silent partial renders. Recovery re-runs only the failed sections; receipts record every attempt, successful or not. Evidence origins are sticky: observations captured from fixtures never upgrade to `live` on later runs, and the corpus records which origin produced each document.

## Tracked vs disposable; determinism

Tracked inputs/outputs: `skills/` (published packages), `data/` (site spec, figure definitions), and this manuscript. The entire `output/` tree is disposable and rebuildable. The generator is deterministic — no LLM contributes to tracked artifacts — figures render on a fixed matplotlib Agg backend with no timestamps drawn, and byte-level re-runs of render/publish are stable.

## Artifact inventory

| Artifact | Contents |
| --- | --- |
| `inventory.json` | discovered-page inventory and provenance |
| `render_summary.json` | per-section render outcomes and counts |
| `publish_receipt.json` | validation/copy results for the `skills/` tree |
| `augmentation_receipts.jsonl` | one receipt per augmentation attempt ({{AUGMENT_ATTEMPTS}} attempts, {{AUGMENT_OK}} ok) |
| `fractiskills_analysis.json` | aggregate corpus analysis record |
| `skills.csv` | flat catalog of all {{SKILL_COUNT}} skills |
| `figure_registry.json` | figure paths, captions, registry metadata |
| `manuscript_variables.json` | bound token values for this manuscript |
| `manuscript_receipt.json` | bind receipt linking tokens to sources |
