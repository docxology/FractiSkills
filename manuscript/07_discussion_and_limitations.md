# Discussion and Limitations {#sec:discussion}

This chapter reads the pipeline's receipts against the {{TOTAL_PAGES}}-page corpus and states what the render cannot do. Claims carry tokens rather than prose where a number exists.

## What the render gets right

**Complete coverage.** The render accounts for {{TOTAL_PAGES}} pages and {{SKILL_COUNT}} skills across {{SECTION_COUNT}} sections. The union strategy treats sitemap entries and crawl discoveries as equally eligible, so the {{VIA_CRAWL_ONLY}} traversal-only pages render alongside the {{VIA_SITEMAP}} sitemap-advertised pages. Completeness is a ledger claim: every page carries provenance naming how it was found.

**Honest augmentation receipts.** Of {{AUGMENT_ATTEMPTS}} attempts, {{AUGMENT_OK}} succeeded and {{AUGMENT_FAILED}} failed — and failures render as failures, not silently patched text. Receipts record API URL, timestamp, HTTP outcome, and error class (400, empty payload, timeout, 404 in the observed window), so a reader can tell a static-fetch body from an augmented one.

**Union beats sitemap-only.** Sitemap-only ingestion recovers 11% of the corpus ({{VIA_SITEMAP}} of {{TOTAL_PAGES}} pages) and misses whole sections: Ship-Blog and Voyage contributed zero sitemap entries in the window. The union closes that gap by construction.

**Sections mirror the site.** The manuscript's section structure corresponds to the origin's directory layout; heavy sections surface honestly (Interfaces is both the link-heaviest and the largest by page count), and the render does not flatten that asymmetry.

**Quantified augmentation effect.** Median words move from {{MEDIAN_WORDS_STATIC}} (static) to {{MEDIAN_WORDS_AUGMENTED}} (augmented) — {{AUGMENT_RATIO}}x. Reported as a corpus median, this describes what a typical reader receives; per-page receipts let anyone audit the outliers.

## Known limitations

1. **Discovery boundary.** Sitemap and crawler see different slices; neither is a superset. Pages in neither source stay invisible, so any claim about "the site" is a claim about the observed union.
2. **Static fetcher and binding coverage.** The fetcher renders only what the fetch returns. Where substance arrives via a runtime binding, coverage requires a spec entry naming it; uncovered bindings yield thin pages, recorded as thin rather than inferred.
3. **One skill per page, shared backing documents.** The same document served at multiple routes renders as distinct pages per the one-skill-per-page contract. Duplicates are real in the page graph but not independent in substance; receipts expose the shared backing document by content hash, so downstream analysis can deduplicate deliberately.
4. **Path-derived names.** Names derive from URL paths: stable against origin routing, but cryptic where paths are, and origin renames propagate. Curated titles would be prettier and less auditable.
5. **Dated snapshot.** The corpus reflects the observation window. A refresh yields a new observation, not a merge; diffs compute between snapshots, and provenance for any fact ends at the snapshot boundary.
6. **Single-origin design.** One origin, one sitemap, one crawl per snapshot. Cross-origin corpora need a second discovery envelope and per-origin attribution the current evidence model does not carry.

## Ethical posture

The origin's `robots.txt` welcomes all crawlers (a verifiable property of the site, recorded in the reviewed site spec that bounds every request); the pipeline honored that welcome at its declared budget — {{REQUEST_COUNT}} requests, each rate-limited by the crawler's configured minimum delay and issued under the project user agent the spec declares. The honesty rail holds end to end: receipts show what was fetched, when, and how.

The content remains the author's work. The render is a structural mirror with attribution, not a republication: each page traces to its source URL through the source map, and attribution travels with excerpts. Where augmentation transformed text, the receipt records the transformation; nothing is laundered into appearing original. The pipeline's claim is only that it observed the corpus faithfully — authorship, and the responsibility it entails, stays with the origin.
