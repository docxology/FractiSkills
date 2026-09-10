# tests/ guide

- `conftest.py` serves a small multi-page fixture site over real HTTP
  (sitemap, redirect alias, dynamic shell + API, catalog binding) and derives
  a `SiteSpec` pointing at it.
- No mock frameworks: tests hit real local HTTP. Fixture-origin runs pass
  `evidence_origin="fixture"`; the default suite never reads pre-existing
  `output/` or `skills/` artifacts.
- `test_live_site.py` is opt-in (`FRACTISKILLS_RUN_LIVE=1`, marker `live`).
- Coverage gate: `--cov=src --cov-fail-under=90` (branch coverage).
