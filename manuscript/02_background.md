# Background {#sec:background}

## Skillarum

[Skillarum][@skillarum] v0.2.0 is the acquisition and generation engine behind FractiSkills. Its pipeline runs in five stages — *acquire → prepare → process → parse → render* — turning a declarative YAML profile into validated `SKILL.md` packages. A profile fixes the base URL, a safety-bounded crawl configuration (robots compliance, same-origin policy, request/page caps, streaming reads, rate limits), extraction rules, and named targets, each bound to exact page URLs. The deterministic render backend composes source-grounded skill bodies (*When to use*, *Semantic knowledge*, *Procedural guidance*, *Verification*) entirely offline; provider backends (OpenAI, Ollama, shell command) are optional supplements. Every package carries a manifest binding it to its prepared corpus's fingerprint, so later package/source drift is detectable. Validators gate each stage — crawl manifest, prepared corpus, rendered package — and failures are withheld, not emitted. FractiSkills consumes Skillarum as a pinned dependency (v0.2.0), adding whole-site discovery, dynamic-content augmentation, and publication-scale organization.

## The site as corpus

The corpus is the SS Vibelandia site at {{BASE_URL}}. Its machine posture is explicit: `robots.txt` serves `User-agent: * / Allow: /` with the banner "All crawlers welcome. All content public. Index everything." A sitemap of {{SITEMAP_URLS}} URLs follows the sitemap protocol [@sitemaps], and the crawl respects the Robots Exclusion Protocol [@rfc9309] as enforced by Skillarum's fetcher. Content spans an art manifest, a ship-board blog, journey brochures, nesting guides, press releases, a whitepaper reading room, and interactive exhibits — a stress test for whole-site, section-organized skilling.

## The dynamic-content problem

A whole-site render meets pages Skillarum's static fetcher cannot serve honestly: client-rendered shells. Their served HTML holds only a near-empty loading frame while the real document arrives from a same-origin JSON endpoint
