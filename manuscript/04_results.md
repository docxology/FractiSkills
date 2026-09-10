# Results {#sec:results}

One complete live run of the pipeline over the observation window {{OBSERVATION_WINDOW}} produced the following inventory and render record. Discovery enumerated **{{TOTAL_PAGES}} distinct pages** of the site: {{VIA_SITEMAP}} also present in the declared sitemap (which lists {{SITEMAP_URLS}} URLs) and {{VIA_CRAWL_ONLY}} found only by the crawl, with {{ALIAS_PAGES}} pages carrying redirect aliases that were resolved to their canonical identity. The render stage executed {{SECTION_COUNT}} section profiles and published **{{SKILL_COUNT}} skills** — one per page, no gaps — with a combined body of {{TOTAL_WORDS}} words (median {{MEDIAN_WORDS}} words per skill), at an acquisition cost of {{REQUEST_COUNT}} network requests.

## Inventory and render by section {#sec:results-sections}

{{SECTION_TABLE}}

Every discovered page yielded exactly one skill: sections with `skills = pages` indicate full coverage. The section totals above are bound tokens computed from the published skill tree, so any rerun that changes the inventory changes this table mechanically.

## Dynamic-document augmentation {#sec:results-augmentation}

Of {{AUGMENT_ATTEMPTS}} declared augmentation attempts, {{AUGMENT_OK}} retrieved real documents ({{AUGMENT_CHARS}} document characters in total) and {{AUGMENT_FAILED}} failed with persisted receipts. Each successful attempt converts a would-be twenty-word "Loading document…" shell skill into a body carrying the full retrieved document with its retrieval provenance inline. Receipts are appended to `output/data/augmentation_receipts.jsonl` and mirrored into each skill's manifest metadata, so the augmentation story of any individual skill is auditable from the published package alone.

## Evidence and provenance {#sec:results-evidence}

Run manifests record evidence origin `{{EVIDENCE_ORIGINS}}` for the live acquisition, the generator identity (`fractiskills-augmented-deterministic`), and the Skillarum pipeline contract (pipeline {{PIPELINE_VERSION}}, cache {{CACHE_VERSION}}). Content hashes bind every skill to its prepared corpus, and every skill body's *Semantic knowledge* section quotes its source page text delimited as untrusted data — the generated skill can never silently substitute its own claims for the site's.
