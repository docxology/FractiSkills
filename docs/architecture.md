# Architecture

## Stage contracts

```text
data/sources/*.yaml        reviewed network truth (crawl limits, bindings)
        │
        ▼
discover.py ──GET sitemap──┐
        │  one bounded BFS crawl (skillarum.crawler.WebsiteCrawler)
        │  one exact-page resolve per unaccepted sitemap URL
        ▼
output/data/inventory.json  PageEntry records: url, path, section,
        │                   via_sitemap/via_crawl, title, links, aliases
        ▼
profiles.py  one Skillarum SourceProfile per section,
        │    one exact-page TargetSpec per page
        ▼
pipeline.render_site ── skillarum.pipeline.run_profile (per section)
        │   AugmentedGenerator: deterministic bodies + declared
        │   same-origin API augmentation (receipts per attempt)
        ▼
output/skills/<Section>/<Skill>/SKILL.md + manifest.json
        │
        ▼
pipeline.publish_skills ─ validate, copy into tracked skills/,
        │                 reconcile stale packages, rebuild index.json
        ▼
research layer (analysis.py → figures.py → publication.py)
        │  one analysis record, five PNG figures, token variables,
        │  bound chapters in output/manuscript/
```

## Data contracts

- **PageEntry**: the atomic inventory unit; provenance flags are set only
  from observed crawl/sitemap facts.
- **BundleRecord / PageRecord** (Skillarum): per-target acquisition receipts
  with request events; FractiSkills never edits them.
- **AugmentationReceipt**: one JSON line per dynamic-document fetch — page
  URL, API URL, ok/status/title/text_chars/sha256/etag/fetched_at/error.
- **RenderSummary**: per-section `SectionRun` outcomes; `ok=False` carries a
  truncated error and does not abort sibling sections.

## Deliberate boundaries

- The shipped Skillarum fetcher is static HTTP (v1 boundary): no browser
  fetcher. Dynamic pages are served through declared bindings instead.
- Skill names are path-derived; page titles live in inventory and bodies.
- Publishing is a clean cutover, not a merge.

See `manuscript/layer_contract.yaml` for the enforcement table and
`docs/policies.md` for safety and evidence rules.