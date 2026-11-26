# Summary {#sec:summary}

The analyzed run at `{{BASE_URL}}` produced a printed corpus: one skill per page, {{SKILL_COUNT}} pages across {{SECTION_COUNT}} sections, {{TOTAL_WORDS}} words in all. Every page exists because the crawl found it — nothing was invented to fill space.

Three honesty mechanisms carry the book. First, union discovery: pages come from the sitemap unioned with the crawl frontier ({{VIA_SITEMAP}} pages via sitemap, {{VIA_CRAWL_ONLY}} reachable only by crawling), so provenance is explicit rather than assumed. Second, receipted augmentation: {{AUGMENT_OK}} of {{AUGMENT_ATTEMPTS}} API calls succeeded, each with a verifiable receipt; the {{AUGMENT_FAILED}} failures are printed as loud failures, not silently dropped. Third, token-bound prose: every figure caption and statistic binds to a named placeholder, so no number in this book is hand-typed.

The pinned pipeline (version {{PIPELINE_VERSION}}, cache version {{CACHE_VERSION}}) can rebuild from retained run inputs. A new acquisition is a separately dated observation. The public release [@fractiskills] preserves the published case-study measurements; fixture verification exercises the renderer and evidence binding on a synthetic site.

Observation window: {{OBSERVATION_WINDOW}}.
