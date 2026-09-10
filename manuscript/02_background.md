# Background {#sec:background}

## Skillarum {#sec:skillarum}

[Skillarum](@skillarum) v0.2.0 provides the acquisition and generation engine. Its five-stage pipeline — *acquire → prepare → process → parse → render* — turns a declarative YAML profile into validated `SKILL.md` packages. Profiles define a base URL, safety-bounded crawl configuration (robots compliance, same-origin policy, request/page caps, streaming reads, rate limiting), extraction rules, and a list of named targets, each mapping to exact page URLs. The deterministic generator produces source-grounded skill bodies — *When to use*, *Semantic knowledge*, *Procedural guidance*, *Verification* — entirely offline; provider backends (OpenAI, Ollama, command) are optional. Every rendered package carries a manifest binding it to its prepared corpus fingerprint, plus a source map with per-page URLs, retrieval timestamps, status codes, and content hashes.

FractiSkills consumes Skillarum as a pinned dependency (`skillarum @ git+…@v0.2.0`) and adds three things: whole-site discovery, dynamic-content augmentation, and publication-scale organization.

## The site as corpus {#sec:site-corpus}

The SS Vibelandia site declares its machine-readable surfaces up front: `robots.txt` (`User-agent: * / Allow: /`, "All crawlers welcome. All content public. Index everything.") and a sitemap of {{SITEMAP_URLS}} URLs following the sitemap protocol [@sitemaps]. The crawl itself respects the Robots Exclusion Protocol [@rfc9309] as enforced by Skillarum's crawler. The site's content spans an art manifest, a ship-board blog, journey brochures, nesting guides, press releases, a whitepaper reading room, and interactive exhibit pages — an ideal stress test for section-organized whole-site skilling.

## The dynamic-content problem {#sec:dynamic}

A whole-site render hits a class of pages Skillarum's static fetcher alone cannot serve honestly: client-rendered shells. Their served HTML contains a loading frame (roughly twenty words) while the real document is fetched by in-page JavaScript from same-origin JSON endpoints such as `/api/whitepaper?id=<id>`. Rendering those skills from static HTML alone would produce near-empty packages that *look* complete — a provenance failure rather than a mere inconvenience. FractiSkills makes the document dependency explicit: each dynamic page pattern is bound, in the reviewed site spec, to the same-origin endpoint that carries its real content, and the render stage retrieves and stamps those documents (§\ref{sec:methods}).
