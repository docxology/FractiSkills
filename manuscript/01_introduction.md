# Introduction {#sec:introduction}

Agent harnesses load skills as portable `SKILL.md` packages: frontmatter plus structured Markdown teaching what a body of knowledge is, when to use it, how to verify claims. [Skillarum][@skillarum] renders such packages from *selected* pages — a profile names targets, each mapping to an exact URL. FractiSkills asks the next question: what does it take to skill an **entire website** — every page, organized as the site itself is organized, published as one reviewable artifact?

Whole-site skilling must first *discover* what the site contains. A declared sitemap alone is not enough — on the subject site, {{SITEMAP_URLS}} declared URLs yielded only {{VIA_SITEMAP}} pages, while a bounded, robots-respecting crawl added {{VIA_CRAWL_ONLY}} more. Coverage requires unioning declared and discovered sources under the site's own section architecture.

The subject corpus is the *SS Vibelandia Omniversal Canvas* at {{BASE_URL}} — a self-described "digital Burning Man camp and art exhibit" [@ssvibelandia]. It is a demanding test case: static pages sit beside client-rendered readers whose served HTML is a loading shell, JSON-backed catalogs, redirect stubs, and query-parameterized document routes. `robots.txt` welcomes all crawlers and a sitemap declares the corpus; {{TOTAL_PAGES}} pages across {{SECTION_COUNT}} sections exercise every path the pipeline implements.

## A formal preview {#sec:formal-preview}

The three contributions compose into one coverage statement. If $\mathcal{S}$ is the declared sitemap, $\mathcal{C}$ the crawl's accepted pages, and $\operatorname{id}(\cdot)$ the canonical identity of a URL, the render target set is the union

$$
\mathcal{P} \;=\; \operatorname{id}(\mathcal{S}) \,\cup\, \operatorname{id}(\mathcal{C})
$$ {#eq:coverage_preview}

developed as [@eq:union] in §\ref{sec:formal} with the alias fixed point of [@eq:alias_resolution]; the yields of [@eq:sitemap_yield] and [@eq:sitemap_miss] are its two measurements, and the hub score of [@eq:inbound_score] and the augmentation ratio of [@eq:augment_ratio] are the run's headline outcomes.

## Contributions {#sec:contributions}

1. **Whole-site discovery with alias resolution.** The discovery stage unions the declared sitemap with a bounded crawl, resolves redirect aliases to canonical pages, and partitions every page into the site's own sections — one render target per page. The {{VIA_CRAWL_ONLY}} crawl-only additions — sitemap-only ingestion would have missed 88.9% of the corpus ({{SITEMAP_YIELD}} of declared sitemap URLs resolve to pages) — motivate this union strategy.
2. **Declared dynamic-document augmentation.** An `AugmentedGenerator` keeps Skillarum's deterministic skill body but retrieves client-rendered documents from reviewed, same-origin JSON endpoints, stamping per-fetch receipts into metadata and artifacts; failures degrade to honest thin skills, never fabricated content ({{AUGMENT_OK}} of {{AUGMENT_ATTEMPTS}} succeed).
3. **A tracked, reconciled library.** Validated packages publish into a clean-cut `skills/` tree with a discovery index, plus deterministic figures and a fully token-bound manuscript — every numeric claim hydrated from persisted run artifacts, none hand-typed (§\ref{sec:methods}).

Reading guide: §\ref{sec:background} sets the Skillarum context; §\ref{sec:methods} specifies the pipeline and its formal model; §\ref{sec:results} reports the live run through seven numbered results subsections; §\ref{sec:visualizations} presents thirteen auto-numbered figures; §\ref{sec:catalog} catalogs every skill; §\ref{sec:discussion} states limitations; §\ref{sec:reproducibility} gives the reproduction contract.
