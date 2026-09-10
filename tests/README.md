# tests/

Hermetic pytest suite: local fixture HTTP servers, no mock frameworks.
`conftest.py` serves a small multi-page site (sitemap, 301 alias, reader
shell + JSON API, catalog API) and derives a pointing SiteSpec.

- Default: `uv run pytest tests/ --cov=src --cov-fail-under=90`
- Live (opt-in): `FRACTISKILLS_RUN_LIVE=1 uv run pytest tests/test_live_site.py`
