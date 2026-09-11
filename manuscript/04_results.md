# Results {#sec:results}

One complete live run over the observation window {{OBSERVATION_WINDOW}} produced the following record. Discovery enumerated **{{TOTAL_PAGES}} distinct pages**: {{VIA_SITEMAP}} of them are also declared in the sitemap (which contains {{SITEMAP_URLS}} URLs), the other {{VIA_CRAWL_ONLY}} were reachable only by following links; {{ALIAS_PAGES}} of the pages carry alias URLs (redirect stubs and declared canonical duplicates) that fold onto them and are not additional pages. Rendering executed {{SECTION_COUNT}} section profiles and published **{{SKILL_COUNT}} skills** — one per page, no gaps — totaling {{TOTAL_WORDS}} words (median {{MEDIAN_WORDS}} per skill) at a cost of {{REQUEST_COUNT}} network requests.

## Inventory and render by section

{{SECTION_TABLE}}

Every discovered page yielded exactly one skill: sections with `skills = pages` indicate full coverage. The distribution is heavy-tailed — Interfaces, Whitepaper, and Ship-Blog dominate the word count, while schedule and lattice sections contribute small but structurally load-bearing profiles. These totals are bound tokens computed from the published skill tree, so a rerun that changes the inventory changes this table mechanically ([@fractiskills]).

## Discovery yield

The two yields decompose the union of [@eq:union] from each side. Measuring the sitemap against itself, the sitemap-URL acceptance yield

$$
Y_{\mathcal{S}} \;=\; \frac{|\operatorname{id}(\mathcal{S}) \cap \mathcal{P}|}{|\mathcal{S}|}
$$ {#eq:sitemap_yield}

is {{SITEMAP_YIELD}}: {{VIA_SITEMAP}} of the {{SITEMAP_URLS}} declared URLs resolved to distinct pages, the rest being aliases of pages discovered elsewhere. Measuring the same intersection against the corpus, the sitemap-only miss rate

$$
M_{\mathcal{S}} \;=\; 1 \;-\; \frac{|\operatorname{id}(\mathcal{S}) \cap \mathcal{P}|}{|\mathcal{P}|}
$$ {#eq:sitemap_miss}

is 88.9%: {{VIA_CRAWL_ONLY}} of {{TOTAL_PAGES}} pages exist only because the crawl followed links the sitemap does not enumerate — including the entire Ship-Blog archive and all Voyage content. A sitemap-only render would have shipped roughly one page in nine while claiming completeness; alias maps keep the crawl-only surplus honest, so the surplus is distinct content, not duplicated paths.

## Depth profile

[@eq:union] hides *where* the crawl earned its pages. Grouping the inventory by breadth-first depth,

$$
d^\ast \;=\; \operatorname*{arg\,max}_{d}\, |\mathcal{P}_d|,
\qquad
s^\ast \;=\; \frac{|\mathcal{P}_{d^\ast}|}{|\mathcal{P}|},
$$ {#eq:depth_mode}

gives the modal depth {{DEPTH_MODE_DEPTH}} holding {{DEPTH_MODE_SHARE}} of all pages, with the deepest page found at depth {{TOP_DEPTH}}. The full histogram follows.

{{DEPTH_TABLE}}

## Hub structure

The inbound score of a page $p$ counts the discovered pages whose quoted links resolve onto it under [@eq:alias_resolution],

$$
h(p) \;=\; \bigl|\{\, q \in \mathcal{P} \;\big|\; p \in \operatorname{res}(\operatorname{links}(q)) \,\}\bigr|,
$$ {#eq:inbound_score}

and the top of that ranking is the site's hub structure.

{{TOP_INDEGREE_TABLE}}

The questfest landing page dominates as the event's canonical entry point: its table-leading inbound count is carried partly by links to the `/questfest` spelling, which the site's own canonical declaration folds onto the vibelandia-questfest page — followed by the Ship-Blog index and lattice-chat, the live interface project pages reference; the root, frontiersman-voyage, the reading room, and the questfest bridge form the next tier. Only discovered pages are ranked: link targets that are redirect stubs or query variants fold onto the pages they forward to, and the handful that land on API endpoints or dead links are receipted separately rather than miscounted.

## Dynamic-document augmentation

Of {{AUGMENT_ATTEMPTS}} declared augmentation attempts, {{AUGMENT_OK}} retrieved real documents ({{AUGMENT_CHARS}} document characters in total) and {{AUGMENT_FAILED}} failed with persisted receipts. Each successful attempt converts a would-be twenty-word "Loading document…" shell skill into a body carrying the full retrieved document with its retrieval provenance inline.

| Page | Declared endpoint | Failure |
| --- | --- | --- |
| `/interfaces/whitepaper-surface.html` (no `?id=`) | `/api/whitepaper?id=` | HTTP 400 |
| `/interfaces/whitepaper-surface.html?id=synthobs` | `/api/whitepaper?id=synthobs` | payload carried no document text |
| `/special-projects/geomagnetic-herbivore-study` | `/api/turner-recent-anomaly-report` | read timeout |
| `/whitepaper/lattice-token-reduction-proof` | `/api/whitepaper?id=lattice-token-reduction-proof` | HTTP 404 |

: The four failed augmentation attempts; each keeps its static shell text plus an explicit warning. {#tbl:augmentation_failures}

[@tbl:augmentation_failures] is the complete failure set: a router page without an `?id=` parameter, a document that exists but carries no body, a transient timeout, and a stale whitepaper path. Each receipt is appended to `output/data/augmentation_receipts.jsonl` and mirrored into the skill's manifest metadata, so the augmentation story of any individual skill is auditable from the published package alone.

## Corpus shape

The size effect of augmentation is captured by the median ratio

$$
r \;=\; \frac{\tilde{w}_{\mathrm{aug}}}{\tilde{w}_{\mathrm{stat}}},
$$ {#eq:augment_ratio}

where $\tilde{w}$ denotes the median body size in words over the {{AUGMENT_SKILLS}} augmented and {{STATIC_SKILLS}} static skills: $r = {{AUGMENT_RATIO}}$ ({{MEDIAN_WORDS_AUGMENTED}} versus {{MEDIAN_WORDS_STATIC}} words). Corpus-wide, the {{SKILL_COUNT}} skills carry {{TOTAL_WORDS}} words in {{TOTAL_CHARS}} characters of body text — evidence-weighted prose, not filler.

## Evidence and provenance

Run manifests record evidence origin `{{EVIDENCE_ORIGINS}}` for the live acquisition, the generator identity (`fractiskills-augmented-deterministic`), and the Skillarum pipeline contract (pipeline {{PIPELINE_VERSION}}, cache {{CACHE_VERSION}}). Content hashes bind every skill to its prepared corpus, and every skill body's *Semantic knowledge* section quotes its source page text delimited as untrusted data — the generated skill can never silently substitute its own claims for the site's.