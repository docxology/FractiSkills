# Scope and Related Work {#sec:scope}

## In scope

FractiSkills does exactly four things for exactly one declared site, SS Vibelandia:

1. **Discovery.** Enumerate every page as the union of sitemap endpoints and a bounded breadth-first crawl, reconciled against {{SITEMAP_URLS}} sitemap entries into {{TOTAL_PAGES}} unique pages.
2. **Render.** One validated portable skill per page, with honest dynamic-document augmentation where the site offers a structured document surface — {{AUGMENT_OK}} of {{AUGMENT_ATTEMPTS}} attempts succeed.
3. **Publish.** Reconcile the skills into a tracked library organized by the site's own {{SECTION_COUNT}}-section architecture, plus a discovery index keyed on the link graph.
4. **Research (document).** Aggregate the run into one analysis record, render its figures, and bind this token-bound manuscript; every numeric claim resolves from the run manifest.

The result is a *render* of one public work, with the work's own architecture as the organizing principle — not a retelling of it.

## Out of scope

- **Not a general crawler.** Discovery is bounded to one origin, {{BASE_URL}}, and terminates; it is not a reusable web-crawling framework.
- **Not a search engine.** The discovery index answers "which skill exists where," not relevance ranking.
- **Not an LLM synthesis pipeline.** The deterministic backend is the default and produced all tracked artifacts; no provider LLM content appears in the corpus.
- **Single-origin only.** No aggregation of multiple sites into one skill namespace.
- **No generated-code execution.** Rendered skills are inspected, never run.
- **No fixture-to-live upgrades.** Evidence-origin rules are inherited from Skillarum and enforced in run manifests; live observations stay {{EVIDENCE_ORIGINS}}.

## Related work

- **Skillarum** [@skillarum] — the engine: acquisition-to-render pipeline, portable skill format, provenance manifests, validator suite. FractiSkills is a downstream consumer and a whole-site-scale demonstration of Skillarum's extension points.
- **The template pipeline** [@fractiskills] — parent engineering conventions this repo follows: src-layout packages, thin scripts, ≥90% coverage on `src/`, no-mock hermetic tests, claim ledgers, token-bound manuscripts.
- **Sitemap protocol** [@sitemaps] and **Robots Exclusion Protocol** [@rfc9309] — the cooperative-crawl primitives the discovery stage builds on, which the corpus site extends deliberately to all agents.
- **SS Vibelandia** [@ssvibelandia] — the corpus itself: an openly shared artwork whose own metadata — robots rules, sitemap, honesty rail — makes a respectful whole-site render possible.
