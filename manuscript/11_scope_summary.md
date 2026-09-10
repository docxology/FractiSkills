# Summary {#sec:summary}

This manuscript rendered the living artwork {{BASE_URL}} as a printed corpus: one skill per page, {{SKILL_COUNT}} pages across {{SECTION_COUNT}} sections, {{TOTAL_WORDS}} words in all. Every page exists because the crawl found it — nothing was invented to fill space.

Three honesty mechanisms carry the book. First, union discovery: pages come from the sitemap unioned with the crawl frontier ({{VIA_SITEMAP}} pages via sitemap, {{VIA_CRAWL_ONLY}} reachable only by crawling), so provenance is explicit rather than assumed. Second, receipted augmentation: {{AUGMENT_OK}} of {{AUGMENT_ATTEMPTS}} API calls succeeded, each with a verifiable receipt; the {{AUGMENT_FAILED}} failures are printed as loud failures, not silently dropped. Third, token-bound prose: every figure caption and statistic binds to a named placeholder, so no number in this book is hand-typed.

Reproduction is one command against the pinned pipeline (version {{PIPELINE_VERSION}}, cache version {{CACHE_VERSION}}), which re-crawls, re-augments, re-figures, and re-typesets deterministically. If the output differs, the corpus changed — the manuscript is a measurement, not a snapshot frozen in prose.

Observation window: {{OBSERVATION_WINDOW}}.
