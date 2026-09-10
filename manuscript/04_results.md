# Results {#sec:results}

A complete live run over the observation window {{OBSERVATION_WINDOW}} produced the following record. Discovery enumerated **{{TOTAL_PAGES}} distinct pages**: {{VIA_SITEMAP}} of them are also declared in the sitemap (which contains {{SITEMAP_URLS}} URLs), the other {{VIA_CRAWL_ONLY}} were reachable only by following links; {{ALIAS_PAGES}} of the pages carry alias URLs (redirect stubs and declared canonical duplicates) that fold onto them and are not additional pages. Rendering executed {{SECTION_COUNT}} section profiles and published **{{SKILL_COUNT}} skills** — one per page, no gaps — totaling {{TOTAL_WORDS}} words (median {{MEDIAN_WORDS}} per skill) at a cost of {{REQUEST_COUNT}} network requests.

## Inventory and render by section

{{SECTION_TABLE}}

Every discovered page yielded exactly one skill: sections with `skills = pages` indicate full coverage. The distribution is heavy-tailed — Interfaces, Whitepaper, and Ship-Blog dominate the word count, while schedule and lattice sections contribute small but structurally load-bearing profiles. These totals are bound tokens computed from the published skill tree, so a rerun that changes the inventory changes this table mechanically (@fractiskills).

## Discovery provenance

Of the {{SITEMAP_URLS}} declared sitemap URLs, {{VIA_SITEMAP}} resolved to distinct pages — an {{SITEMAP_YIELD}} sitemap-URL acceptance rate, covering 11% of the corpus: {{VIA_SITEMAP}} of {{TOTAL_PAGES}} rendered pages appear in the sitemap; the other {{VIA_CRAWL_ONLY}} were found only because the crawl followed links the sitemap does not enumerate. A sitemap-only render would have missed roughly nine of every ten pages ({{VIA_CRAWL_ONLY}} of {{TOTAL_PAGES}}) — including the entire Ship-Blog archive and all Voyage content — silently shrinking the corpus. Alias maps keep the crawl-only surplus honest: redirect stubs forward onto canonical URLs counted once, so the surplus is distinct content, not duplicated paths (@sitemaps, @rfc9309).

## Depth profile

{{DEPTH_TABLE}}

The corpus is deep rather than shallow: the modal profile is {{DEPTH_MODE_DEPTH}}, covering {{DEPTH_MODE_SHARE}} of all pages, with the deepest material at {{TOP_DEPTH}} levels of link traversal from the root. This long tail of nested content is exactly what sitemap-only discovery cannot see.

## Hub structure

{{TOP_INDEGREE_TABLE}}

The inbound-link ranking shows a small hub set the rest of the site cites constantly: the questfest landing page dominates as the event's canonical entry point (its inbound links resolve through the site's own canonical declaration onto the vibelandia-questfest page), followed by the Ship-Blog index and lattice-chat, the live interface project pages reference; the root, frontiersman-voyage, the reading room, and the questfest bridge form the next tier. These hubs are the crawl's load-bearing nodes: link-following discovery converges on them quickly, and a failed render would orphan large subgraphs. Only discovered pages are ranked — link targets that are redirect stubs or query variants are folded onto the pages they forward to.

## Dynamic-document augmentation

Of {{AUGMENT_ATTEMPTS}} declared augmentation attempts, {{AUGMENT_OK}} retrieved real documents ({{AUGMENT_CHARS}} characters total) and {{AUGMENT_FAILED}} failed with persisted receipts. Each success converts a short "Loading document…" shell skill into a body carrying the full retrieved document with retrieval provenance inline. The failures are recorded receipts, not silent losses: HTTP 400 for an empty `id`, a payload with no document text, a read timeout, and HTTP 404 for a whitepaper id the API no longer serves. In every failure case the static shell text remains published with an explicit warning that the dynamic layer did not resolve, and each receipt is appended to `output/data/augmentation_receipts.jsonl` and mirrored into the skill's manifest metadata — every skill's augmentation story is auditable from the package alone.

## Evidence and provenance

Run manifests record evidence origin `{{EVIDENCE_ORIGINS}}`, the generator identity (`fractiskills-augmented-deterministic`), and the Skillarum pipeline contract (pipeline {{PIPELINE_VERSION}}, cache {{CACHE_VERSION}}). Content hashes bind every skill to its prepared corpus, so a rerun producing different bytes produces a different, detectable package. Every skill body's *Semantic knowledge* section quotes its source page text delimited as untrusted data: the skill can never silently substitute its own claims for the site's (@fractiskills, @skillarum).
