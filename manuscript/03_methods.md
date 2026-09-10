# Methods {#sec:methods}

The pipeline is four stages — **discover → render → publish → research** — each a separate testable module under `src/fractiskills/`, orchestrated by thin scripts and a `fractiskills` CLI. Network behavior is bounded by two reviewed files: the site spec `data/sources/ssvibelandia.yaml` (crawl limits, user agent, dynamic bindings) and the Skillarum crawl safety limits it feeds.

## Discovery {#sec:methods-discovery}

`discover.py` fetches the declared sitemap (`{{SITEMAP_URL}}`), normalizes and validates every entry (same-origin, public HTTP(S)), then runs **one bounded breadth-first crawl** through Skillarum's `WebsiteCrawler` seeded with `/` and every sitemap URL, with `follow_links` enabled, prefix filtering, page/request caps ({{CRAWL_ACCEPTED}} pages accepted from the sitemap-seeded frontier), a minimum delay per request, and streamed bounded responses. Redirect chains are recorded as alias maps so that stub URLs (for example meta-refresh redirect pages) resolve to the canonical page they forward to; sitemap URLs that redirect onto another sitemap page are recorded as aliases of it rather than as duplicate pages. The union — sitemap ∪ crawl, deduplicated by canonical/final URL — is persisted as the page inventory (`output/data/inventory.json`) with per-page provenance (`via_sitemap`, `via_crawl_only`), title, BFS depth, outbound links, and section assignment.

Sections mirror the site's information architecture: multi-segment paths take their area from the first path segment (`/journey/*` → `Journey`, `/ship-blog/*` → `Ship-Blog`, `/interfaces/nesting/*` promoted to `Nesting`), while single-segment deck-level pages join `Core`. This mechanical rule yields {{SECTION_COUNT}} sections over {{TOTAL_PAGES}} pages.

## Render {#sec:methods-render}

`profiles.py` compiles one Skillarum profile per section (one exact-page target per discovered page; page-count-derived request budgets; 0.5 s minimum delay), and `pipeline.py` executes each with `skillarum.pipeline.run_profile`, passing the `AugmentedGenerator` described below. Targets that fail hard (for example a page that vanished between discovery and render) fail their section run with a persisted failure manifest rather than silently skipping a page — partial renders are never presented as complete.

## Dynamic-document augmentation {#sec:methods-augmentation}

`AugmentedGenerator` subclasses Skillarum's `DeterministicGenerator`, so every skill body keeps the deterministic section structure and passes Skillarum's portable-body validators. For pages whose URL matches a declared binding, it fetches the bound same-origin JSON endpoint (GET only, timeout-bounded, DNS-validated, same-origin enforced), extracts the document text from the payload HTML, prepends a provenance header (endpoint, timestamp, HTTP status, content SHA-256, ETag), and replaces the shell text with the augmented text. Each attempt — successful or failed — is appended as a receipt to `output/data/augmentation_receipts.jsonl` and stored in the skill's manifest metadata. Failed augmentations keep the static shell text and add an explicit warning to the corpus, so the rendered skill remains truthful about its thinness.

## Publish and research {#sec:methods-publish}

`publish_skills` validates every rendered package with Skillarum's package validator, copies it into the tracked `skills/<Section>/<Skill>/` tree, reconciles stale packages away, and rebuilds the discovery index. The research stage (`analysis.py`, `figures.py`, `publication.py`) aggregates run manifests, augmentation receipts, and the published tree into one analysis record, renders the five figures of §\ref{sec:visualizations}, computes the manuscript token values, and binds them into `output/manuscript/`. All {{SKILL_COUNT}} skills, both figures and receipts, and the analysis CSV regenerate from a clean checkout with `uv run python -m fractiskills run --refresh`.
