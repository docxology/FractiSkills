# FractiSkills package source guide

Modules, in dependency order:

| Module | Role |
| --- | --- |
| `models.py` | Typed contracts (`SiteSpec`, `PageEntry`, `SiteInventory`, `SectionRun`, `RenderSummary`) + atomic JSON/YAML/text IO helpers |
| `profiles.py` | Compile Skillarum `SourceProfile`s: discovery BFS, single-URL resolve, per-section exact-page targets |
| `discover.py` | Acquisition boundary: sitemap + BFS crawl + alias resolution → persisted inventory |
| `generator.py` | `AugmentedGenerator` — deterministic bodies plus declared same-origin API augmentation with receipts |
| `pipeline.py` | Stage orchestration: `render_site` (per-section `run_profile`) and `publish_skills` (validate, copy, reconcile, index) |
| `analysis.py` | Offline aggregation over inventory, run manifests, receipts, and the published tree |
| `figures.py` | Deterministic matplotlib figures + figure registry |
| `publication.py` | Manuscript token variables, token binding with loud failures, ordered research build |
| `cli.py` | argparse dispatch over the stages |

## Invariants

- No module outside `discover.py`/`generator.py`/`pipeline.py` touches the
  network; research modules only read persisted artifacts.
- `run_profile` is called once per section; one failing target fails that
  section run (persisted `failure.json`), and `render_site` continues with
  the remaining sections — partial renders are reported, never hidden.
- Skill directory names derive from page paths (stable), never page titles.
- Every augmentation attempt appends a receipt (success or failure) and is
  mirrored into the skill manifest metadata.
- Publishing reconciles: packages absent from the current render are removed
  so the tracked tree is always a clean cut.