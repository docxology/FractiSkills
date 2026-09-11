# Methods {#sec:methods}

The pipeline is four stages — **discover → render → publish → research** — each a separate testable module under `src/fractiskills/`, orchestrated by thin scripts and a `fractiskills` CLI. Network behavior is bounded by two reviewed files: the site spec `data/sources/ssvibelandia.yaml` (crawl limits, user agent, dynamic bindings) and the Skillarum crawl safety limits it feeds.

## Pipeline overview

| Stage | Module | Reads | Writes | Network |
| --- | --- | --- | --- | --- |
| discover | `discover.py` | site spec, sitemap | `output/data/inventory.json` | sitemap GET + bounded BFS crawl + resolution fetches |
| render | `pipeline.py` | inventory, site spec | `output/skills/`, run manifests | page GETs via Skillarum crawler |
| publish | `pipeline.py` | rendered packages | tracked `skills/`, `skills/index.json` | none |
| research | `analysis.py`, `figures.py`, `publication.py` | persisted artifacts | analysis record, figures, bound manuscript | none |

: The four stages, their module boundaries, and their single network column. {#tbl:pipeline_stages}

Every stage writes atomically and reads only persisted artifacts, so any stage can be re-run independently; [@tbl:pipeline_stages] is the enforcement surface for the layer contract in `manuscript/layer_contract.yaml`.

## Discovery

`discover.py` fetches the declared sitemap (`{{SITEMAP_URL}}`), normalizes and validates every entry (same-origin, public HTTP(S)), then runs **one bounded breadth-first crawl** through Skillarum's `WebsiteCrawler` seeded with `/` and every sitemap URL, with `follow_links` enabled, prefix filtering, page/request caps, a minimum delay per request, and streamed bounded responses. Redirect chains are recorded as alias maps so that stub URLs (for example meta-refresh redirect pages) resolve to the canonical page they forward to; sitemap URLs that redirect onto another sitemap page are recorded as aliases of it rather than as duplicate pages. Sitemap URLs the breadth-first pass cannot accept — most importantly canonical-declared duplicates — get one exact-page resolution fetch, whose served HTML canonical tag recovers the alias target from the crawler's own fetch cache.

The union — sitemap ∪ crawl, deduplicated by canonical/final URL — is persisted as the page inventory (`output/data/inventory.json`) with per-page provenance (`via_sitemap`, `via_crawl_only`), title, BFS depth, outbound links, and section assignment.

Sections mirror the site's information architecture: multi-segment paths take their area from the first path segment (`/journey/*` → `Journey`, `/ship-blog/*` → `Ship-Blog`, `/interfaces/nesting/*` promoted to `Nesting`), while single-segment deck-level pages join `Core`. This mechanical rule yields {{SECTION_COUNT}} sections over {{TOTAL_PAGES}} pages.

## A formal model of coverage {#sec:formal}

Let $\mathcal{S}$ be the declared sitemap URLs and $\mathcal{C}$ the pages accepted by the bounded crawl. Every fetched URL is reduced to a canonical identity $\operatorname{id}(u)$ — its declared `<link rel="canonical">` target when present, its final post-redirect URL otherwise — and the discovered page set is the union

$$
\mathcal{P} \;=\; \operatorname{id}(\mathcal{S}) \,\cup\, \operatorname{id}(\mathcal{C}),
$$ {#eq:union}

so a URL reached under several spellings contributes exactly one page. Alias resolution is the fixed point of the alias step $f$ (each hop recorded by a redirect event, a canonical declaration, or a duplicate rejection), computed with a cycle guard:

$$
\operatorname{res}(u) \;=\;
\begin{cases}
\operatorname{res}\!\bigl(f(u)\bigr) & \text{if } f(u) \neq u,\\
u & \text{otherwise.}
\end{cases}
$$ {#eq:alias_resolution}

Each section profile renders $|\mathcal{P}_s|$ exact-page targets under a request budget that grows linearly with the section's page count plus fixed headroom for robots, redirects, and retries:

$$
R_s \;=\; 3\,|\mathcal{P}_s| + 20,
$$ {#eq:request_budget}

which kept the twelve section runs inside {{REQUEST_COUNT}} network requests in total. A sitemap URL that survives neither the breadth-first pass nor alias resolution becomes a recorded note — never a silent gap — so the inventory is complete with respect to its own evidence.

## Render

`profiles.py` compiles one Skillarum profile per section (one exact-page target per discovered page; page-count-derived request budgets per [@eq:request_budget]; 0.5 s minimum delay), and `pipeline.py` executes each with `skillarum.pipeline.run_profile`, passing the `AugmentedGenerator` described below. Targets that fail hard (for example a page that vanished between discovery and render) fail their section run with a persisted failure manifest rather than silently skipping a page — partial renders are never presented as complete.

## Dynamic-document augmentation

`AugmentedGenerator` subclasses Skillarum's `DeterministicGenerator`, so every skill body keeps the deterministic section structure and passes Skillarum's portable-body validators. For pages whose URL matches a declared binding, it fetches the bound same-origin JSON endpoint (GET only, timeout-bounded, DNS-validated, same-origin enforced), extracts the document text from the payload HTML, prepends a provenance header (endpoint, timestamp, HTTP status, content SHA-256, ETag), and replaces the shell text with the augmented text. Each attempt — successful or failed — is appended as a receipt to `output/data/augmentation_receipts.jsonl` and stored in the skill's manifest metadata. Failed augmentations keep the static shell text and add an explicit warning to the corpus, so the rendered skill remains truthful about its thinness.

## Publish and research

`publish_skills` validates every rendered package with Skillarum's package validator, copies it into the tracked `skills/<Section>/<Skill>/` tree, reconciles stale packages away, and rebuilds the discovery index. The research stage (`analysis.py`, `figures.py`, `publication.py`) aggregates run manifests, augmentation receipts, and the published tree into one analysis record, renders the thirteen figures of §\ref{sec:visualizations}, computes the manuscript token values, and binds them into `output/manuscript/`. All {{SKILL_COUNT}} skills, the figures and receipts, and the analysis CSV regenerate from a clean checkout with `uv run python -m fractiskills run --refresh --json`.
