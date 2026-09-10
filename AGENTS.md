# FractiSkills agent guidance

FractiSkills is a standalone code project. Its implementation lives in
`src/fractiskills/`; `scripts/` only dispatches the package CLI. Keep page
discovery, augmentation, publication, and research as separate testable stages.

## Per-directory guidance

| Directory | Guide |
| --- | --- |
| Package source | [`src/fractiskills/AGENTS.md`](src/fractiskills/AGENTS.md) |
| Entrypoints | [`scripts/AGENTS.md`](scripts/AGENTS.md) |
| Tests | [`tests/AGENTS.md`](tests/AGENTS.md) |
| Inputs and ledgers | [`data/AGENTS.md`](data/AGENTS.md), [`data/sources/AGENTS.md`](data/sources/AGENTS.md) |
| Manuscript sources | [`manuscript/AGENTS.md`](manuscript/AGENTS.md) |
| Documentation | [`docs/AGENTS.md`](docs/AGENTS.md) |

`output/` is generated, disposable, and untracked. It is not documented.

## Layer contract

- `src/fractiskills/models.py` and `profiles.py` are deterministic contracts
  and transformations — no network, no sibling-stage imports.
- `src/fractiskills/discover.py` owns the acquisition boundary: one sitemap
  GET plus one bounded Skillarum BFS crawl, then one exact-page resolution
  fetch per unaccepted sitemap URL. It owns `output/data/inventory.json`.
- `src/fractiskills/generator.py` is the augmentation boundary: same-origin
  JSON GETs for declared bindings only. Everything else is offline.
- `src/fractiskills/pipeline.py` orchestrates; page acquisition and skill
  rendering are delegated to `skillarum.pipeline` / `skillarum.render`.
- `analysis.py`, `figures.py`, `publication.py` form the research layer;
  they read persisted artifacts and never acquire pages.
- `cli.py` and `scripts/` are thin dispatch only.
- Live counts are bound as manuscript tokens from persisted artifacts —
  never hand-typed into prose.

## Testing rules

Tests use local fixture HTTP servers (pytest-httpserver) and real subprocesses
rather than mock frameworks; the default suite must be hermetic from a clean
checkout (`output/` and `skills/` are disposable/ignored for tests). Fixture
origin runs pass `evidence_origin="fixture"` and `allow_private_hosts=True`;
a fixture observation is never presented as live-site evidence. Default suite:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Before a release or push also run `ruff check src tests`, `ruff format --check
src tests`, and `uv run python scripts/60_validate.py` over the tracked skill
tree. Do not commit credentials, crawl caches, or run logs. Deterministic
skills, the inventory, and the discovery index may be retained as reviewable
outputs — the tracked `skills/` tree is the product.

## Safety posture

- Acquisition honors `robots.txt` and same-origin policy; every request is
  rate-limited and bounded in size; redirects are validated before following.
- Dynamic-document augmentation touches only the same-origin endpoints
  declared in `data/sources/ssvibelandia.yaml`.
- Generated skills store `untrusted_source=True` and `source_bounded=True`
  metadata; hostile source wording is preserved only as delimited reference
  data by the deterministic extractor.

## Current verification

Run the commands in this file and the README; historical receipts are not
current receipts. `publication.py` owns the ordered offline research build;
the parent-template pre-render hook is `scripts/z_generate_manuscript_variables.py`.