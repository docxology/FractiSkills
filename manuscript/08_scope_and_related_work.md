# Scope and Related Work {#sec:scope}

## In scope {#sec:scope-in}

FractiSkills does exactly four things for exactly one declared site: discover every page (sitemap ∪ bounded crawl), render one validated portable skill per page with honest dynamic-document augmentation, publish the skills as a reconciled tracked library with a discovery index, and document the whole run with figures and a token-hydrated manuscript. It is a *render* of one public work, with the work's own architecture as the organizing principle.

## Out of scope {#sec:scope-out}

It is not a general web-crawling framework, a search engine, an LLM synthesis pipeline (the deterministic backend is the default and the tracked artifacts were produced without any provider), or an aggregation of multiple sites into one skill namespace. It does not modify the source site, does not execute generated code, and does not upgrade fixture observations into live evidence — the evidence-origin rules are inherited from Skillarum and enforced in run manifests.

## Related work {#sec:related}

- **Skillarum** [@skillarum] — the engine: five-stage acquisition-to-render pipeline, portable skill format, provenance manifests, validator suite. FractiSkills is a downstream consumer and a demonstration of Skillarum's extension points (custom generators, per-area organization) at whole-site scale.
- **The template pipeline** [@fractiskills] — the parent engineering conventions this repo follows: src-layout packages, thin scripts, ≥90% coverage on `src/`, no-mock hermetic tests, claim ledgers, and token-bound manuscripts.
- **Sitemap protocol** [@sitemaps] and **Robots Exclusion Protocol** [@rfc9309] — the cooperative-crawl primitives the discovery stage builds on and the site explicitly extends to all agents.
- **SS Vibelandia** [@ssvibelandia] — the corpus itself: an openly shared artwork whose own metadata (robots, sitemap, honesty rail) makes a respectful whole-site render possible.
