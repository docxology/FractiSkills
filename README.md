# FractiSkills

One portable agent `SKILL.md` package **per page** of the [SS Vibelandia Omniversal Canvas](https://www.ssvibelandiaquestfest24x365.com/) — a living, openly shared SuperAI art project by Valet Pru (Downtown Reno) — rendered with [Skillarum](https://github.com/docxology/Skillarum), organized by the site's own section architecture, published with deterministic figures and a token-hydrated manuscript.

**Agent orientation (read in this order):** [AGENTS.md](AGENTS.md) (layer contract + testing rules) → `uv run python scripts/00_preflight.py` → `output/data/inventory.json` (page inventory) → `skills/index.json` (discovery index for rendered skills).

## What a full run produces

| Artifact | Where |
| --- | --- |
| Page inventory (sitemap ∪ bounded crawl, aliases resolved) | `output/data/inventory.json` |
| One validated skill package per page | `skills/<Section>/<Skill>/SKILL.md` + `manifest.json` |
| Harness discovery index | `skills/index.json` |
| Augmentation receipts (dynamic documents) | `output/data/augmentation_receipts.jsonl` |
| Aggregated analysis record + CSV | `output/data/fractiskills_analysis.json`, `skills.csv` |
| Five deterministic figures + registry | `output/figures/*.png`, `output/data/figure_registry.json` |
| Bound manuscript chapters | `output/manuscript/` |

## Quick start

```bash
git clone https://github.com/docxology/FractiSkills
cd FractiSkills
uv sync --extra dev
uv run python -m fractiskills run --refresh --json   # full live pipeline
```

Stage-by-stage:

```bash
uv run python scripts/10_discover.py           # sitemap + bounded BFS crawl
uv run python scripts/20_render_skills.py      # one SKILL.md per page
uv run python scripts/30_publish_skills.py     # validate + publish tracked tree
uv run python scripts/40_analyze.py            # aggregate artifacts
uv run python scripts/50_figures.py            # visualizations
uv run python scripts/60_validate.py           # validate every tracked package
```

## How it works

Four stages, each a separate testable module:

```text
discover → render → publish → research
```

1. **discover** — fetch the site's declared sitemap, then run one bounded, robots-respecting breadth-first crawl (Skillarum's `WebsiteCrawler`: same-origin, rate-limited, streamed) seeded with `/` and every sitemap URL. Redirect chains and declared canonical duplicates are resolved to aliases; the union is the page inventory.
2. **render** — one Skillarum profile per site section, one exact-page target per page. The `AugmentedGenerator` keeps Skillarum's deterministic skill body and, for pages whose static HTML is a client-rendered shell, retrieves the real document from the same-origin JSON endpoint declared in the reviewed site spec — with per-fetch receipts. Hard target failures fail their section loudly; nothing is silently skipped or fabricated.
3. **publish** — validate every rendered package and copy it into the tracked, reconciled `skills/` tree; rebuild the discovery index.
4. **research** — aggregate artifacts into one analysis record, render the five figures, compute manuscript tokens, bind them into `output/manuscript/`.

Every numeric claim in the manuscript is a bound token hydrated from persisted run artifacts; rerunning produces a new dated observation with fresh receipts, not an implicit merge.

## Source boundaries

All network behavior is bounded by two reviewed files: `data/sources/ssvibelandia.yaml` (crawl limits, user agent, dynamic bindings) and the Skillarum safety limits it feeds. The crawler honors the site's `robots.txt` (which explicitly welcomes all crawlers), rate-limits every request, and identifies itself with the project user agent. Source page content is delimited as untrusted data inside generated skills; generated code is never executed.

## Development

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src tests && uv run ruff format --check src tests
```

Tests are hermetic from a clean checkout (local fixture HTTP servers, no mocks of the acquisition path). Live-site tests are opt-in: `FRACTISKILLS_RUN_LIVE=1 uv run pytest tests/test_live_site.py`.

## License

MIT. Source-page content remains the work of its author; every skill binds back to its source URL.