# Discussion and Limitations {#sec:discussion}

## What the render gets right {#sec:discussion-strengths}

The pipeline produces a complete, section-organized, provenance-bound skill library in one command, and it does so honestly: pages are counted only when fetched, augmentations are receipted whether they succeed or fail, and every body quotes its source as delimited untrusted data. The union discovery strategy matters — the sitemap under-reports the site ({{VIA_CRAWL_ONLY}} pages were crawl-only in this run), and a sitemap-only scraper would have silently shipped an incomplete library while claiming completeness.

## Known limitations {#sec:discussion-limits}

1. **Discovery boundary.** Coverage is sitemap ∪ crawl-reachable pages. A page linked from nowhere and absent from the sitemap is undiscoverable by any crawler that respects the site's structure; the inventory records its own completeness conditions (`incomplete` flag, crawl warnings) instead of overclaiming.
2. **Static fetcher.** Skillarum's shipped fetcher is static HTTP by design (the v1 boundary defers browser-backed fetching). JavaScript-heavy pages are handled through the declared binding mechanism, which requires a reviewed spec entry per dynamic pattern; a dynamic pattern without a binding renders as a thin shell with a warning.
3. **Duplicate documents, distinct pages.** The site exposes some documents at multiple routes (for example a path-style `/whitepaper/<slug>` and a query-style reader URL backed by the same API document). FractiSkills renders one skill per *page*, as asked, and the augmentation receipts make the shared backing document visible; it does not silently collapse pages, and it does not pretend duplicates are independent works.
4. **Names are path-derived.** Skill directory names derive from page paths (stable across refreshes) rather than page titles (which drift). This trades a little readability for install-path stability, following Skillarum's target-name-authority principle.
5. **Content is a snapshot.** The site is a living artwork with daily ship notes. This repository's tracked skills are a dated observation; rerunning `uv run python -m fractiskills run --refresh` produces a new dated observation with fresh receipts and a reconciliation diff, not an implicit merge.

## Ethical posture {#sec:discussion-ethics}

The site publishes `robots.txt` permitting all crawlers and invites indexing; the pipeline honors robots, rate-limits every request, identifies itself with a project user agent, and records the site's own honesty rail rather than stripping it. The site's creative content remains the work of its author; FractiSkills claims no copyright over source pages and binds every skill to its source URL so attribution travels with every artifact.
