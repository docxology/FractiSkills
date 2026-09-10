# Visualizations {#sec:visualizations}

All ten figures are generated deterministically by `figures.py` from the persisted analysis record — no hand-entered numbers, no timestamps drawn inside the images. Color is the colorblind-safe Okabe-Ito palette throughout. Each run writes `output/data/figure_registry.json`; the binder binds the `FIGURE_<ID>_ALT` and `FIGURE_<ID>_CAPTION` tokens below, so captions cannot drift from their data, and chapters reference the PNGs under the `../output/figures/` convention.

![{{FIGURE_SITE_SECTIONS_ALT}}](../output/figures/fig1-site-sections.png)

**Figure 1.** {{FIGURE_SITE_SECTIONS_CAPTION}}

![{{FIGURE_DISCOVERY_PROVENANCE_ALT}}](../output/figures/fig2-discovery-provenance.png)

**Figure 2.** {{FIGURE_DISCOVERY_PROVENANCE_CAPTION}}

![{{FIGURE_CORPUS_SHARE_ALT}}](../output/figures/fig3-corpus-share.png)

**Figure 3.** {{FIGURE_CORPUS_SHARE_CAPTION}}

![{{FIGURE_SKILL_SIZE_DISTRIBUTION_ALT}}](../output/figures/fig4-skill-size-distribution.png)

**Figure 4.** {{FIGURE_SKILL_SIZE_DISTRIBUTION_CAPTION}}

![{{FIGURE_SECTION_LINK_GRAPH_ALT}}](../output/figures/fig5-section-link-graph.png)

**Figure 5.** {{FIGURE_SECTION_LINK_GRAPH_CAPTION}}

![{{FIGURE_AUGMENTATION_ALT}}](../output/figures/fig6-augmentation.png)

**Figure 6.** {{FIGURE_AUGMENTATION_CAPTION}}

![{{FIGURE_DISCOVERY_FUNNEL_ALT}}](../output/figures/fig7-discovery-funnel.png)

**Figure 7.** {{FIGURE_DISCOVERY_FUNNEL_CAPTION}}

![{{FIGURE_CRAWL_DEPTH_ALT}}](../output/figures/fig8-crawl-depth.png)

**Figure 8.** {{FIGURE_CRAWL_DEPTH_CAPTION}}

![{{FIGURE_TOP_INDEGREE_ALT}}](../output/figures/fig9-top-indegree.png)

**Figure 9.** {{FIGURE_TOP_INDEGREE_CAPTION}}

![{{FIGURE_AUGMENTATION_EFFECT_ALT}}](../output/figures/fig10-augmentation-effect.png)

**Figure 10.** {{FIGURE_AUGMENTATION_EFFECT_CAPTION}}

## Reading the set

Read in order, the ten figures narrate the corpus. Figure 1 fixes structure — {{SECTION_COUNT}} sections, the largest {{BIGGEST_SECTION}}. Figure 2 splits provenance: {{VIA_SITEMAP}} sitemap pages against {{VIA_CRAWL_ONLY}} crawl-only. Figure 3 weighs mass, pages against word share; Figure 4 spreads skill sizes, a broad body with a small tail; Figure 5 traces flow across the cross-section link graph. Figure 6 itemizes the augmentation layer, successes and persisted failures alike; Figure 7 compresses discovery from {{SITEMAP_URLS}} declared URLs to the {{TOTAL_PAGES}}-page union; Figure 8 explains the funnel's width — {{DEPTH_MODE_SHARE}} of pages at {{DEPTH_MODE_DEPTH}}. Figure 9 names the hubs that link-following converges on; Figure 10 measures augmentation's effect on median skill size. Structure, provenance, mass, sizes, flow, augmentation, funnel, depth, hubs, effect: one deterministic pass over one dated observation.
